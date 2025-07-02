"""
Hierarchical Multi-Agent Research System

A comprehensive locally-executable hierarchical multi-agent system with conversational CLI interface
and full Python package integration.
"""

__version__ = "0.1.0"
__author__ = "Strategic Consulting"

from .workflows.research_workflow import HierarchicalResearchSystem
from .config.models import ModelConfig

__all__ = ["HierarchicalResearchSystem", "ModelConfig"]