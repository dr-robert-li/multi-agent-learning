"""
Tests for research tools and utilities
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.tools.research_tools import ResearchToolkit
from src.tools.document_ingestion import DocumentIngestor
from src.tools.data_ingestion import DataIngestor
from src.utils.session_manager import SessionManager, ResearchSession
from src.utils.memory_management import MemoryManager


class TestResearchToolkit:
    """Test ResearchToolkit functionality"""
    
    def test_research_toolkit_initialization(self, temp_workspace):
        """Test ResearchToolkit initialization"""
        toolkit = ResearchToolkit(temp_workspace)
        
        assert toolkit.workspace_dir == temp_workspace
        assert hasattr(toolkit, 'document_ingestor')
        assert hasattr(toolkit, 'data_ingestor')
        assert hasattr(toolkit, 'source_manager')
    
    @pytest.mark.asyncio
    async def test_add_source_document(self, temp_workspace, sample_pdf_file):
        """Test adding a document source"""
        toolkit = ResearchToolkit(temp_workspace)
        
        with patch.object(toolkit.document_ingestor, 'ingest_document', new_callable=AsyncMock) as mock_ingest:
            mock_ingest.return_value = {
                "content": "Sample document content",
                "metadata": {"title": "Test Document"},
                "source_id": "doc_123"
            }
            
            source_id = await toolkit.add_source(
                source=sample_pdf_file,
                source_type="document",
                metadata={"description": "Test PDF document"}
            )
            
            assert source_id is not None
            mock_ingest.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_source_data(self, temp_workspace, sample_csv_file):
        """Test adding a data source"""
        toolkit = ResearchToolkit(temp_workspace)
        
        with patch.object(toolkit.data_ingestor, 'ingest_data', new_callable=AsyncMock) as mock_ingest:
            mock_ingest.return_value = {
                "data": [{"id": 1, "value": 100}],
                "metadata": {"rows": 1, "columns": 2},
                "source_id": "data_123"
            }
            
            source_id = await toolkit.add_source(
                source=sample_csv_file,
                source_type="data",
                metadata={"description": "Test CSV data"}
            )
            
            assert source_id is not None
            mock_ingest.assert_called_once()
    
    def test_get_all_user_content(self, temp_workspace):
        """Test getting all user content"""
        toolkit = ResearchToolkit(temp_workspace)
        
        # Mock source manager to return test data
        with patch.object(toolkit.source_manager, 'get_all_sources') as mock_get_sources:
            mock_get_sources.return_value = {
                "documents": [{"id": "doc1", "content": "Test doc"}],
                "datasets": [{"id": "data1", "data": [{"test": "value"}]}]
            }
            
            content = toolkit.get_all_user_content()
            
            assert "documents" in content
            assert "datasets" in content
            assert len(content["documents"]) == 1
            assert len(content["datasets"]) == 1
    
    def test_prepare_context_for_agent(self, temp_workspace):
        """Test preparing context for agents"""
        toolkit = ResearchToolkit(temp_workspace)
        
        with patch.object(toolkit, 'get_all_user_content') as mock_get_content:
            mock_get_content.return_value = {
                "documents": [
                    {"content": "AI healthcare research", "metadata": {"tags": ["ai", "healthcare"]}}
                ],
                "datasets": []
            }
            
            context = toolkit.prepare_context_for_agent(
                agent_name="LiteratureSurveyAgent",
                source_types=["document"],
                keywords=["healthcare"]
            )
            
            assert "documents" in context
            assert "instructions" in context


class TestDocumentIngestor:
    """Test DocumentIngestor functionality"""
    
    def test_document_ingestor_initialization(self, temp_workspace):
        """Test DocumentIngestor initialization"""
        ingestor = DocumentIngestor(temp_workspace)
        assert ingestor.workspace_dir == temp_workspace
    
    def test_is_url_detection(self, temp_workspace):
        """Test URL detection"""
        ingestor = DocumentIngestor(temp_workspace)
        
        assert ingestor._is_url("https://example.com/document.pdf")
        assert ingestor._is_url("http://example.com/file.txt")
        assert not ingestor._is_url("./local/file.pdf")
        assert not ingestor._is_url("/absolute/path/file.pdf")
    
    @pytest.mark.asyncio
    async def test_ingest_text_file(self, temp_workspace):
        """Test ingesting a text file"""
        ingestor = DocumentIngestor(temp_workspace)
        
        # Create a test text file
        test_file = Path(temp_workspace) / "test.txt"
        test_content = "This is a test document for ingestion testing."
        test_file.write_text(test_content)
        
        result = await ingestor.ingest_document(
            source=str(test_file),
            metadata={"description": "Test document"}
        )
        
        assert result["content"] == test_content
        assert result["metadata"]["file_type"] == "txt"
        assert result["original_source"] == str(test_file)
    
    @pytest.mark.asyncio
    async def test_ingest_json_file(self, temp_workspace):
        """Test ingesting a JSON file"""
        ingestor = DocumentIngestor(temp_workspace)
        
        # Create a test JSON file
        test_file = Path(temp_workspace) / "test.json"
        test_data = {"title": "Test Document", "content": "Test content"}
        test_file.write_text(json.dumps(test_data))
        
        result = await ingestor.ingest_document(
            source=str(test_file),
            metadata={"description": "Test JSON document"}
        )
        
        assert "Test Document" in result["content"]
        assert result["metadata"]["file_type"] == "json"
    
    @pytest.mark.asyncio
    async def test_ingest_unsupported_format(self, temp_workspace):
        """Test handling of unsupported file format"""
        ingestor = DocumentIngestor(temp_workspace)
        
        # Create a file with unsupported extension
        test_file = Path(temp_workspace) / "test.xyz"
        test_file.write_text("Some content")
        
        with pytest.raises(ValueError, match="Unsupported document format"):
            await ingestor.ingest_document(str(test_file))


class TestDataIngestor:
    """Test DataIngestor functionality"""
    
    def test_data_ingestor_initialization(self, temp_workspace):
        """Test DataIngestor initialization"""
        ingestor = DataIngestor(temp_workspace)
        assert ingestor.workspace_dir == temp_workspace
    
    @pytest.mark.asyncio
    async def test_ingest_csv_file(self, temp_workspace, sample_csv_file):
        """Test ingesting a CSV file"""
        ingestor = DataIngestor(temp_workspace)
        
        result = await ingestor.ingest_data(
            source=sample_csv_file,
            metadata={"description": "Test CSV data"}
        )
        
        assert "data" in result
        assert "metadata" in result
        assert result["metadata"]["file_type"] == "csv"
        assert result["metadata"]["rows"] > 0
    
    @pytest.mark.asyncio
    async def test_ingest_json_data(self, temp_workspace):
        """Test ingesting JSON data"""
        ingestor = DataIngestor(temp_workspace)
        
        # Create test JSON data file
        test_file = Path(temp_workspace) / "data.json"
        test_data = [
            {"id": 1, "name": "Item 1", "value": 100},
            {"id": 2, "name": "Item 2", "value": 200}
        ]
        test_file.write_text(json.dumps(test_data))
        
        result = await ingestor.ingest_data(
            source=str(test_file),
            metadata={"description": "Test JSON data"}
        )
        
        assert len(result["data"]) == 2
        assert result["metadata"]["file_type"] == "json"
    
    @pytest.mark.asyncio
    async def test_ingest_from_url(self, temp_workspace, mock_aiohttp_session):
        """Test ingesting data from URL"""
        ingestor = DataIngestor(temp_workspace)
        
        with patch('aiohttp.ClientSession', return_value=mock_aiohttp_session):
            mock_aiohttp_session.get.return_value.__aenter__.return_value.json.return_value = [
                {"id": 1, "test": "data"}
            ]
            
            result = await ingestor.ingest_data(
                source="https://api.example.com/data",
                metadata={"description": "Test API data"}
            )
            
            assert "data" in result
            assert result["original_source"] == "https://api.example.com/data"


class TestSessionManager:
    """Test SessionManager functionality"""
    
    def test_session_manager_initialization(self, temp_workspace):
        """Test SessionManager initialization"""
        with patch('src.utils.session_manager.DEFAULT_SESSION_DIR', temp_workspace):
            manager = SessionManager()
            assert manager.session_dir == temp_workspace
    
    def test_create_session(self, temp_workspace):
        """Test creating a new session"""
        with patch('src.utils.session_manager.DEFAULT_SESSION_DIR', temp_workspace):
            manager = SessionManager()
            
            session = manager.create_session(
                name="Test Session",
                topic="Test Topic",
                requirements={"target_length": 25000}
            )
            
            assert isinstance(session, ResearchSession)
            assert session.name == "Test Session"
            assert session.topic == "Test Topic"
            assert session.requirements["target_length"] == 25000
    
    def test_save_and_load_session(self, temp_workspace):
        """Test saving and loading a session"""
        with patch('src.utils.session_manager.DEFAULT_SESSION_DIR', temp_workspace):
            manager = SessionManager()
            
            # Create and save session
            session = manager.create_session(
                name="Test Session",
                topic="Test Topic",
                requirements={"target_length": 25000}
            )
            
            manager.save_session(session)
            
            # Load session
            loaded_session = manager.load_session(session.session_id)
            
            assert loaded_session is not None
            assert loaded_session.name == "Test Session"
            assert loaded_session.topic == "Test Topic"
    
    def test_list_sessions(self, temp_workspace):
        """Test listing sessions"""
        with patch('src.utils.session_manager.DEFAULT_SESSION_DIR', temp_workspace):
            manager = SessionManager()
            
            # Create multiple sessions
            session1 = manager.create_session("Session 1", "Topic 1", {})
            session2 = manager.create_session("Session 2", "Topic 2", {})
            
            manager.save_session(session1)
            manager.save_session(session2)
            
            sessions = manager.list_sessions()
            
            assert len(sessions) >= 2
            session_names = [s["name"] for s in sessions]
            assert "Session 1" in session_names
            assert "Session 2" in session_names


class TestMemoryManager:
    """Test MemoryManager functionality"""
    
    def test_memory_manager_initialization(self):
        """Test MemoryManager initialization"""
        memory = MemoryManager()
        
        assert memory.conversation_history == []
        assert memory.agent_outputs == {}
        assert memory.session_metadata == {}
    
    def test_add_conversation_turn(self):
        """Test adding conversation turns"""
        memory = MemoryManager()
        
        memory.add_conversation_turn("user", "What is AI?")
        memory.add_conversation_turn("assistant", "AI is artificial intelligence...")
        
        assert len(memory.conversation_history) == 2
        assert memory.conversation_history[0]["role"] == "user"
        assert memory.conversation_history[1]["role"] == "assistant"
    
    def test_add_agent_output(self):
        """Test adding agent outputs"""
        memory = MemoryManager()
        
        output = {
            "analysis": "Test analysis",
            "findings": ["Finding 1", "Finding 2"]
        }
        
        memory.add_agent_output("TestAgent", output)
        
        assert "TestAgent" in memory.agent_outputs
        assert len(memory.agent_outputs["TestAgent"]) == 1
        assert memory.agent_outputs["TestAgent"][0]["analysis"] == "Test analysis"
    
    def test_get_relevant_context(self):
        """Test getting relevant context"""
        memory = MemoryManager()
        
        # Add some conversation history
        memory.add_conversation_turn("user", "Tell me about machine learning")
        memory.add_conversation_turn("assistant", "Machine learning is a subset of AI...")
        
        # Add agent output
        memory.add_agent_output("LiteratureAgent", {
            "survey": "Recent ML research shows...",
            "keywords": ["machine learning", "neural networks"]
        })
        
        context = memory.get_relevant_context("machine learning")
        
        assert "conversation_context" in context
        assert "agent_context" in context
        assert len(context["conversation_context"]) > 0
    
    def test_export_and_import_memory(self):
        """Test exporting and importing memory"""
        memory = MemoryManager()
        
        # Add some data
        memory.add_conversation_turn("user", "Test message")
        memory.add_agent_output("TestAgent", {"result": "test"})
        memory.session_metadata = {"test_key": "test_value"}
        
        # Export
        exported = memory.export_memory()
        
        # Create new memory manager and import
        new_memory = MemoryManager()
        new_memory.import_memory(exported)
        
        assert len(new_memory.conversation_history) == 1
        assert "TestAgent" in new_memory.agent_outputs
        assert new_memory.session_metadata["test_key"] == "test_value"