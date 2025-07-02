"""
Agent modules for Hierarchical Research AI
"""

from .base_agent import BaseAgent, AgentState
from .research_team import (
    DomainAnalysisAgent,
    LiteratureSurveyAgent,
    ResearchQuestionFormulationAgent
)
from .analysis_team import (
    QuantitativeAnalysisAgent,
    QualitativeAnalysisAgent,
    SynthesisAgent
)
from .qa_team import (
    PeerReviewAgent,
    CitationVerificationAgent,
    AcademicStandardsComplianceAgent
)
from .generation_team import (
    SectionWritingAgent,
    CoherenceIntegrationAgent,
    FinalAssemblyAgent
)

__all__ = [
    "BaseAgent",
    "AgentState",
    "DomainAnalysisAgent",
    "LiteratureSurveyAgent",
    "ResearchQuestionFormulationAgent",
    "QuantitativeAnalysisAgent",
    "QualitativeAnalysisAgent",
    "SynthesisAgent",
    "PeerReviewAgent",
    "CitationVerificationAgent",
    "AcademicStandardsComplianceAgent",
    "SectionWritingAgent",
    "CoherenceIntegrationAgent",
    "FinalAssemblyAgent"
]