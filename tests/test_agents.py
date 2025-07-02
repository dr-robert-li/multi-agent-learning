"""
Tests for agent implementations
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agents.base_agent import BaseAgent, AgentState
from src.agents.research_team import DomainAnalysisAgent, LiteratureSurveyAgent
from src.agents.analysis_team import QuantitativeAnalysisAgent, SynthesisAgent


class TestBaseAgent:
    """Test BaseAgent functionality"""
    
    def test_base_agent_initialization(self, mock_model_config):
        """Test BaseAgent initialization"""
        mock_model = MagicMock()
        agent = BaseAgent(mock_model)
        
        assert agent.model == mock_model
        assert agent.agent_name == "BaseAgent"
    
    @pytest.mark.asyncio
    async def test_base_agent_process_not_implemented(self, mock_model_config):
        """Test that BaseAgent.process raises NotImplementedError"""
        mock_model = MagicMock()
        agent = BaseAgent(mock_model)
        
        state = AgentState(
            messages=[],
            research_topic="Test Topic",
            current_task="Test Task",
            outputs={},
            metadata={},
            errors=[]
        )
        
        with pytest.raises(NotImplementedError):
            await agent.process(state)


class TestDomainAnalysisAgent:
    """Test DomainAnalysisAgent functionality"""
    
    def test_domain_analysis_agent_initialization(self):
        """Test DomainAnalysisAgent initialization"""
        mock_model = MagicMock()
        agent = DomainAnalysisAgent(mock_model)
        
        assert agent.agent_name == "DomainAnalysisAgent"
        assert agent.model == mock_model
    
    @pytest.mark.asyncio
    async def test_domain_analysis_agent_process(self, sample_research_topic):
        """Test DomainAnalysisAgent processing"""
        mock_model = AsyncMock()
        mock_model.ainvoke.return_value = MagicMock(
            content="Healthcare AI is a rapidly evolving field focusing on machine learning applications in clinical settings."
        )
        
        agent = DomainAnalysisAgent(mock_model)
        
        state = AgentState(
            messages=[],
            research_topic=sample_research_topic,
            current_task="Domain analysis",
            outputs={},
            metadata={},
            errors=[]
        )
        
        result = await agent.process(state)
        
        assert "DomainAnalysisAgent" in result["outputs"]
        assert len(result["outputs"]["DomainAnalysisAgent"]) > 0
        
        output = result["outputs"]["DomainAnalysisAgent"][0]
        assert "analysis" in output
        assert "key_concepts" in output
        assert "scope" in output
        assert output["research_topic"] == sample_research_topic


class TestLiteratureSurveyAgent:
    """Test LiteratureSurveyAgent functionality"""
    
    def test_literature_survey_agent_initialization(self):
        """Test LiteratureSurveyAgent initialization"""
        mock_model = MagicMock()
        agent = LiteratureSurveyAgent(mock_model)
        
        assert agent.agent_name == "LiteratureSurveyAgent"
        assert agent.model == mock_model
    
    @pytest.mark.asyncio
    async def test_literature_survey_agent_process(self, sample_research_topic):
        """Test LiteratureSurveyAgent processing"""
        mock_model = AsyncMock()
        mock_model.ainvoke.return_value = MagicMock(
            content="The literature shows significant advancement in AI healthcare applications with key papers focusing on diagnostic accuracy and patient outcomes."
        )
        
        agent = LiteratureSurveyAgent(mock_model)
        
        state = AgentState(
            messages=[],
            research_topic=sample_research_topic,
            current_task="Literature survey",
            outputs={},
            metadata={},
            errors=[]
        )
        
        result = await agent.process(state)
        
        assert "LiteratureSurveyAgent" in result["outputs"]
        output = result["outputs"]["LiteratureSurveyAgent"][0]
        
        assert "survey" in output
        assert "key_papers" in output
        assert "themes" in output
        assert output["research_topic"] == sample_research_topic


class TestQuantitativeAnalysisAgent:
    """Test QuantitativeAnalysisAgent functionality"""
    
    def test_quantitative_analysis_agent_initialization(self):
        """Test QuantitativeAnalysisAgent initialization"""
        mock_model = MagicMock()
        agent = QuantitativeAnalysisAgent(mock_model)
        
        assert agent.agent_name == "QuantitativeAnalysisAgent"
    
    @pytest.mark.asyncio
    async def test_quantitative_analysis_with_data(self, sample_research_topic, sample_dataset_content):
        """Test QuantitativeAnalysisAgent with dataset"""
        mock_model = AsyncMock()
        mock_model.ainvoke.return_value = MagicMock(
            content="Statistical analysis reveals significant patterns in the healthcare data with 95% confidence intervals."
        )
        
        agent = QuantitativeAnalysisAgent(mock_model)
        
        state = AgentState(
            messages=[],
            research_topic=sample_research_topic,
            current_task="Quantitative analysis",
            outputs={},
            metadata={
                "user_sources": {
                    "datasets": [sample_dataset_content]
                }
            },
            errors=[]
        )
        
        result = await agent.process(state)
        
        assert "QuantitativeAnalysisAgent" in result["outputs"]
        output = result["outputs"]["QuantitativeAnalysisAgent"][0]
        
        assert "analysis" in output
        assert "key_findings" in output
        assert "data_sources" in output


class TestSynthesisAgent:
    """Test SynthesisAgent functionality"""
    
    def test_synthesis_agent_initialization(self):
        """Test SynthesisAgent initialization"""
        mock_model = MagicMock()
        agent = SynthesisAgent(mock_model)
        
        assert agent.agent_name == "SynthesisAgent"
    
    @pytest.mark.asyncio
    async def test_synthesis_agent_process(self, sample_research_topic, sample_agent_output):
        """Test SynthesisAgent processing multiple agent outputs"""
        mock_model = AsyncMock()
        mock_model.ainvoke.return_value = MagicMock(
            content="Synthesis of findings reveals integrated insights across domain analysis and literature review with practical implications for healthcare AI implementation."
        )
        
        agent = SynthesisAgent(mock_model)
        
        state = AgentState(
            messages=[],
            research_topic=sample_research_topic,
            current_task="Synthesis",
            outputs=sample_agent_output,
            metadata={},
            errors=[]
        )
        
        result = await agent.process(state)
        
        assert "SynthesisAgent" in result["outputs"]
        output = result["outputs"]["SynthesisAgent"][0]
        
        assert "synthesis" in output
        assert "integrated_findings" in output
        assert "theoretical_contributions" in output
        assert "practical_implications" in output
        assert "future_directions" in output


class TestAgentErrorHandling:
    """Test error handling in agents"""
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self, sample_research_topic):
        """Test agent behavior when model fails"""
        mock_model = AsyncMock()
        mock_model.ainvoke.side_effect = Exception("Model API error")
        
        agent = DomainAnalysisAgent(mock_model)
        
        state = AgentState(
            messages=[],
            research_topic=sample_research_topic,
            current_task="Domain analysis",
            outputs={},
            metadata={},
            errors=[]
        )
        
        result = await agent.process(state)
        
        assert len(result["errors"]) > 0
        assert "Model API error" in result["errors"][0]
    
    @pytest.mark.asyncio
    async def test_agent_with_invalid_state(self):
        """Test agent behavior with invalid state"""
        mock_model = AsyncMock()
        agent = DomainAnalysisAgent(mock_model)
        
        # Missing required fields
        incomplete_state = {
            "messages": [],
            "research_topic": "",  # Empty topic
            "outputs": {}
        }
        
        # Should handle gracefully
        result = await agent.process(incomplete_state)
        assert "errors" in result