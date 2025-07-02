"""
Pytest configuration and fixtures for HierarchicalResearchAI tests
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from src.config.models import ModelConfig
from src.tools.research_tools import ResearchToolkit
from src.utils.session_manager import SessionManager
from src.workflows.research_workflow import HierarchicalResearchSystem


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for tests"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_model_config():
    """Mock ModelConfig for testing"""
    config = MagicMock(spec=ModelConfig)
    config.get_research_model.return_value = MagicMock()
    config.get_analysis_model.return_value = MagicMock()
    config.get_routine_model.return_value = MagicMock()
    config.get_model_info.return_value = {"models": "mocked"}
    return config


@pytest.fixture
def mock_research_toolkit(temp_workspace):
    """Mock ResearchToolkit for testing"""
    toolkit = MagicMock(spec=ResearchToolkit)
    toolkit.workspace_dir = temp_workspace
    toolkit.get_all_user_content.return_value = {
        "documents": [],
        "datasets": []
    }
    toolkit.prepare_context_for_agent.return_value = {
        "documents": [],
        "instructions": "Test context"
    }
    return toolkit


@pytest.fixture
def sample_research_topic():
    """Sample research topic for tests"""
    return "Artificial Intelligence in Healthcare"


@pytest.fixture
def sample_requirements():
    """Sample research requirements for tests"""
    return {
        "target_length": 25000,
        "citation_style": "APA",
        "quality_level": "academic_thesis",
        "privacy_mode": False,
        "budget_limit": 50.0
    }


@pytest.fixture
def mock_session_manager():
    """Mock SessionManager for testing"""
    manager = MagicMock(spec=SessionManager)
    manager.create_session.return_value = MagicMock()
    manager.save_session.return_value = True
    manager.load_session.return_value = None
    return manager


@pytest.fixture
async def research_system(mock_model_config, temp_workspace):
    """Create a test research system instance"""
    system = HierarchicalResearchSystem(
        cli_mode=False,
        privacy_mode=True,  # Use privacy mode for testing
        workspace_dir=temp_workspace
    )
    # Replace with mocks
    system.model_config = mock_model_config
    return system


@pytest.fixture
def sample_document_content():
    """Sample document content for testing"""
    return {
        "content": "This is a sample research document about AI in healthcare...",
        "metadata": {
            "title": "AI in Healthcare Research",
            "author": "Test Author",
            "year": 2024,
            "description": "Sample research document"
        },
        "original_source": "test_document.pdf"
    }


@pytest.fixture
def sample_dataset_content():
    """Sample dataset content for testing"""
    return {
        "data": [
            {"id": 1, "name": "Test Patient", "diagnosis": "Condition A"},
            {"id": 2, "name": "Test Patient 2", "diagnosis": "Condition B"}
        ],
        "metadata": {
            "description": "Sample healthcare dataset",
            "rows": 2,
            "columns": 3
        },
        "original_source": "test_data.csv"
    }


@pytest.fixture
def sample_agent_output():
    """Sample agent output for testing"""
    return {
        "DomainAnalysisAgent": [{
            "analysis": "Healthcare AI is a rapidly evolving field...",
            "key_concepts": ["machine learning", "diagnosis", "treatment"],
            "scope": "Clinical applications of artificial intelligence",
            "timestamp": "2024-01-01T12:00:00"
        }],
        "LiteratureSurveyAgent": [{
            "survey": "The literature shows significant advancement...",
            "key_papers": [
                {"citation": "Smith et al. (2023). AI in Healthcare.", "relevance": 0.9},
                {"citation": "Jones et al. (2024). Machine Learning Diagnosis.", "relevance": 0.8}
            ],
            "themes": ["diagnostic accuracy", "patient outcomes", "ethical considerations"],
            "timestamp": "2024-01-01T12:30:00"
        }]
    }


@pytest.fixture
def sample_pdf_file(temp_workspace):
    """Create a sample PDF file for testing"""
    pdf_path = Path(temp_workspace) / "test_document.pdf"
    # Create a minimal PDF-like file (not actually valid PDF, but for testing)
    with open(pdf_path, "w") as f:
        f.write("Sample PDF content for testing")
    return str(pdf_path)


@pytest.fixture
def sample_csv_file(temp_workspace):
    """Create a sample CSV file for testing"""
    csv_path = Path(temp_workspace) / "test_data.csv"
    with open(csv_path, "w") as f:
        f.write("id,name,value\n1,Test Item 1,100\n2,Test Item 2,200\n")
    return str(csv_path)


@pytest.fixture
def mock_api_responses():
    """Mock API responses for external services"""
    return {
        "perplexity": {
            "choices": [{
                "message": {
                    "content": "Mocked Perplexity response about AI research..."
                }
            }]
        },
        "anthropic": {
            "content": [{"text": "Mocked Claude response for analysis..."}]
        }
    }


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables"""
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test_perplexity_key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_anthropic_key")
    monkeypatch.setenv("PRIVACY_MODE", "true")


class AsyncContextManager:
    """Helper class for mocking async context managers"""
    def __init__(self, return_value):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session for API calls"""
    session = MagicMock()
    response = MagicMock()
    response.status = 200
    response.json = AsyncMock(return_value={"test": "response"})
    response.text = AsyncMock(return_value="Test response text")
    session.get.return_value = AsyncContextManager(response)
    session.post.return_value = AsyncContextManager(response)
    return session