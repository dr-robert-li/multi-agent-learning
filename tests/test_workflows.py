"""
Tests for workflow systems
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.workflows.supervisor import HierarchicalSupervisor, SupervisorState
from src.workflows.research_workflow import HierarchicalResearchSystem, ResearchProject
from src.workflows.report_generation import ReportGenerator


class TestHierarchicalSupervisor:
    """Test HierarchicalSupervisor functionality"""
    
    def test_supervisor_initialization(self, mock_model_config, mock_research_toolkit):
        """Test supervisor initialization"""
        supervisor = HierarchicalSupervisor(mock_model_config, mock_research_toolkit)
        
        assert supervisor.model_config == mock_model_config
        assert supervisor.research_toolkit == mock_research_toolkit
        assert hasattr(supervisor, 'workflow')
        assert hasattr(supervisor, 'domain_analysis_agent')
        assert hasattr(supervisor, 'literature_survey_agent')
    
    def test_supervisor_state_creation(self):
        """Test SupervisorState creation"""
        state = SupervisorState(
            messages=[],
            research_topic="Test Topic",
            current_phase="initialization",
            agent_outputs={},
            next_agent="",
            completed_agents=[],
            requirements={},
            user_sources={},
            progress={},
            errors=[]
        )
        
        assert state["research_topic"] == "Test Topic"
        assert state["current_phase"] == "initialization"
        assert state["completed_agents"] == []
    
    @pytest.mark.asyncio
    async def test_research_planning_supervisor(self, mock_model_config, mock_research_toolkit):
        """Test research planning supervisor phase"""
        supervisor = HierarchicalSupervisor(mock_model_config, mock_research_toolkit)
        
        # Mock agents
        supervisor.domain_analysis_agent.process = AsyncMock(return_value={
            "outputs": {
                "DomainAnalysisAgent": [{
                    "analysis": "Test domain analysis",
                    "key_concepts": ["concept1", "concept2"]
                }]
            },
            "messages": [{"role": "assistant", "content": "Analysis complete"}],
            "errors": []
        })
        
        supervisor.literature_survey_agent.process = AsyncMock(return_value={
            "outputs": {
                "LiteratureSurveyAgent": [{
                    "survey": "Test literature survey",
                    "key_papers": []
                }]
            },
            "messages": [],
            "errors": []
        })
        
        supervisor.research_question_agent.process = AsyncMock(return_value={
            "outputs": {
                "ResearchQuestionFormulationAgent": [{
                    "primary_question": "Test research question?",
                    "sub_questions": []
                }]
            },
            "messages": [],
            "errors": []
        })
        
        initial_state = SupervisorState(
            messages=[],
            research_topic="Test Topic",
            current_phase="initialization",
            agent_outputs={},
            next_agent="",
            completed_agents=[],
            requirements={},
            user_sources={},
            progress={"phases_completed": []},
            errors=[]
        )
        
        result_state = await supervisor._research_planning_supervisor(initial_state)
        
        assert result_state["current_phase"] == "research_planning"
        assert "research_planning" in result_state["progress"]["phases_completed"]
        assert len(result_state["completed_agents"]) == 3
    
    def test_should_continue_to_data_collection(self, mock_model_config, mock_research_toolkit):
        """Test decision logic for continuing to data collection"""
        supervisor = HierarchicalSupervisor(mock_model_config, mock_research_toolkit)
        
        # Test successful completion
        state = SupervisorState(
            messages=[],
            research_topic="Test",
            current_phase="research_planning",
            agent_outputs={
                "DomainAnalysisAgent": [{}],
                "LiteratureSurveyAgent": [{}],
                "ResearchQuestionFormulationAgent": [{}]
            },
            next_agent="",
            completed_agents=[],
            requirements={},
            user_sources={},
            progress={},
            errors=[]
        )
        
        decision = supervisor._should_continue_to_data_collection(state)
        assert decision == "continue"
        
        # Test with errors
        state["errors"] = ["Error 1", "Error 2", "Error 3", "Error 4"]
        decision = supervisor._should_continue_to_data_collection(state)
        assert decision == "end"
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self, mock_model_config, mock_research_toolkit, sample_requirements):
        """Test complete workflow execution"""
        supervisor = HierarchicalSupervisor(mock_model_config, mock_research_toolkit)
        
        # Mock the workflow execution
        with patch.object(supervisor.workflow, 'astream') as mock_astream:
            mock_final_state = {
                "current_phase": "completed",
                "agent_outputs": {"TestAgent": [{"result": "test"}]},
                "progress": {"completion_percentage": 100},
                "errors": [],
                "completed_agents": ["TestAgent"]
            }
            
            # Mock async stream
            async def mock_stream():
                yield mock_final_state
            
            mock_astream.return_value = mock_stream()
            
            result = await supervisor.execute_workflow(
                research_topic="Test Topic",
                requirements=sample_requirements
            )
            
            assert result["status"] == "completed"
            assert result["research_topic"] == "Test Topic"
            assert "agent_outputs" in result


class TestHierarchicalResearchSystem:
    """Test HierarchicalResearchSystem functionality"""
    
    def test_research_system_initialization(self, temp_workspace):
        """Test research system initialization"""
        system = HierarchicalResearchSystem(
            cli_mode=False,
            privacy_mode=True,
            workspace_dir=temp_workspace
        )
        
        assert system.cli_mode == False
        assert system.privacy_mode == True
        assert system.workspace_dir == temp_workspace
        assert hasattr(system, 'supervisor')
        assert hasattr(system, 'report_generator')
    
    def test_start_project(self, temp_workspace, sample_requirements):
        """Test starting a new research project"""
        system = HierarchicalResearchSystem(workspace_dir=temp_workspace)
        
        project = system.start_project(
            topic="Test Research Topic",
            **sample_requirements
        )
        
        assert isinstance(project, ResearchProject)
        assert project.topic == "Test Research Topic"
        assert project.status == "initialized"
        assert project.requirements["target_length"] == sample_requirements["target_length"]
    
    @pytest.mark.asyncio
    async def test_generate_report(self, temp_workspace, sample_requirements):
        """Test report generation"""
        system = HierarchicalResearchSystem(workspace_dir=temp_workspace)
        
        # Mock the supervisor and report generator
        system.supervisor.execute_workflow = AsyncMock(return_value={
            "status": "completed",
            "agent_outputs": {"TestAgent": [{"result": "test"}]},
            "progress": {"completion_percentage": 100},
            "errors": [],
            "user_sources": {"documents": [], "datasets": []}
        })
        
        system.report_generator.generate_final_report = AsyncMock(return_value={
            "status": "completed",
            "output_path": "/test/report.md",
            "word_count": 25000,
            "section_count": 8,
            "citation_count": 50
        })
        
        project = system.start_project(
            topic="Test Topic",
            **sample_requirements
        )
        
        result = await system.generate_report(project.id)
        
        assert result["status"] == "completed"
        assert result["project_id"] == project.id
        assert result["word_count"] == 25000
        assert "output_path" in result
    
    def test_get_project_status(self, temp_workspace, sample_requirements):
        """Test getting project status"""
        system = HierarchicalResearchSystem(workspace_dir=temp_workspace)
        
        project = system.start_project(
            topic="Test Topic",
            **sample_requirements
        )
        
        status = system.get_project_status(project.id)
        
        assert status["project_id"] == project.id
        assert status["topic"] == "Test Topic"
        assert status["status"] == "initialized"
        assert "progress" in status
    
    def test_list_projects(self, temp_workspace, sample_requirements):
        """Test listing all projects"""
        system = HierarchicalResearchSystem(workspace_dir=temp_workspace)
        
        project1 = system.start_project("Topic 1", **sample_requirements)
        project2 = system.start_project("Topic 2", **sample_requirements)
        
        projects = system.list_projects()
        
        assert len(projects) == 2
        topics = [p["topic"] for p in projects]
        assert "Topic 1" in topics
        assert "Topic 2" in topics


class TestReportGenerator:
    """Test ReportGenerator functionality"""
    
    def test_report_generator_initialization(self, mock_model_config, mock_research_toolkit):
        """Test ReportGenerator initialization"""
        generator = ReportGenerator(mock_model_config, mock_research_toolkit)
        
        assert generator.model_config == mock_model_config
        assert generator.research_toolkit == mock_research_toolkit
    
    @pytest.mark.asyncio
    async def test_generate_final_report(self, mock_model_config, mock_research_toolkit, sample_agent_output, sample_requirements):
        """Test final report generation"""
        generator = ReportGenerator(mock_model_config, mock_research_toolkit)
        
        # Mock research toolkit
        mock_research_toolkit.get_all_user_content.return_value = {
            "documents": [],
            "datasets": []
        }
        
        result = await generator.generate_final_report(
            agent_outputs=sample_agent_output,
            requirements=sample_requirements,
            research_topic="Test Topic"
        )
        
        assert result["status"] == "completed"
        assert "output_path" in result
        assert "word_count" in result
        assert "section_count" in result
        assert "citation_count" in result
    
    def test_extract_abstract(self, mock_model_config, mock_research_toolkit):
        """Test abstract extraction"""
        generator = ReportGenerator(mock_model_config, mock_research_toolkit)
        
        agent_outputs = {
            "SynthesisAgent": [{
                "synthesis": "This research investigates the applications of AI in healthcare with focus on diagnostic accuracy and patient outcomes."
            }]
        }
        
        abstract = generator._extract_abstract(agent_outputs)
        
        assert "This research investigates" in abstract
        assert len(abstract) > 100  # Should be substantial
    
    def test_extract_references(self, mock_model_config, mock_research_toolkit):
        """Test references extraction"""
        generator = ReportGenerator(mock_model_config, mock_research_toolkit)
        
        agent_outputs = {
            "LiteratureSurveyAgent": [{
                "key_papers": [
                    {"citation": "Smith, J. et al. (2023). AI in Healthcare. Journal of Medical AI, 15(3), 245-267."},
                    {"citation": "Jones, M. (2024). Machine Learning Diagnostics. Nature Medicine, 30(2), 123-135."}
                ]
            }]
        }
        
        user_content = {
            "documents": [{
                "original_source": "user_document.pdf",
                "metadata": {"description": "User's preliminary research"}
            }]
        }
        
        references = generator._extract_references(agent_outputs, user_content)
        
        assert "Smith, J. et al." in references
        assert "Jones, M." in references
        assert "User-Provided Sources" in references
    
    def test_format_report(self, mock_model_config, mock_research_toolkit, sample_requirements):
        """Test report formatting"""
        generator = ReportGenerator(mock_model_config, mock_research_toolkit)
        
        content = {
            "title": "Test Research Report",
            "abstract": "This is a test abstract.",
            "introduction": "# Introduction\nThis is the introduction.",
            "literature_review": "# Literature Review\nReview content.",
            "methodology": "# Methodology\nMethodology content.",
            "results": "# Results\nResults content.",
            "discussion": "# Discussion\nDiscussion content.",
            "conclusion": "# Conclusion\nConclusion content.",
            "references": "# References\nReference list.",
            "appendices": "# Appendices\nAppendix content."
        }
        
        formatted = generator._format_report(content, sample_requirements)
        
        assert "# Test Research Report" in formatted
        assert "Table of Contents" in formatted
        assert "Abstract" in formatted
        assert "Introduction" in formatted
        assert formatted.count("---") >= 3  # Separators
    
    def test_generate_report_metadata(self, mock_model_config, mock_research_toolkit, sample_agent_output, sample_requirements):
        """Test report metadata generation"""
        generator = ReportGenerator(mock_model_config, mock_research_toolkit)
        
        report_content = {"title": "Test Report"}
        formatted_report = "# Test Report\n\nThis is a test report with multiple sections. " * 100  # ~2000 words
        
        metadata = generator._generate_report_metadata(
            report_content,
            formatted_report,
            sample_agent_output,
            sample_requirements
        )
        
        assert "word_count" in metadata
        assert "char_count" in metadata
        assert "section_count" in metadata
        assert "agent_stats" in metadata
        assert metadata["word_count"] > 0
        assert metadata["target_length"] == sample_requirements["target_length"]


class TestWorkflowIntegration:
    """Test integration between workflow components"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, temp_workspace, sample_requirements):
        """Test end-to-end workflow execution"""
        system = HierarchicalResearchSystem(
            cli_mode=False,
            privacy_mode=True,
            workspace_dir=temp_workspace
        )
        
        # Mock all the components
        with patch.object(system.supervisor, 'execute_workflow') as mock_workflow, \
             patch.object(system.report_generator, 'generate_final_report') as mock_report:
            
            mock_workflow.return_value = {
                "status": "completed",
                "agent_outputs": {"TestAgent": [{"result": "test"}]},
                "progress": {"completion_percentage": 100},
                "errors": [],
                "user_sources": {"documents": [], "datasets": []}
            }
            
            mock_report.return_value = {
                "status": "completed",
                "output_path": "/test/report.md",
                "word_count": 25000,
                "section_count": 8,
                "citation_count": 50
            }
            
            # Start project and generate report
            project = system.start_project(
                topic="Integration Test Topic",
                **sample_requirements
            )
            
            result = await system.generate_report(project.id)
            
            assert result["status"] == "completed"
            assert result["word_count"] == 25000
            mock_workflow.assert_called_once()
            mock_report.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, temp_workspace, sample_requirements):
        """Test workflow error handling"""
        system = HierarchicalResearchSystem(workspace_dir=temp_workspace)
        
        # Mock supervisor to raise an exception
        system.supervisor.execute_workflow = AsyncMock(
            side_effect=Exception("Workflow execution failed")
        )
        
        project = system.start_project(
            topic="Error Test Topic",
            **sample_requirements
        )
        
        result = await system.generate_report(project.id)
        
        assert result["status"] == "failed"
        assert "error" in result
        assert "Workflow execution failed" in result["error"]