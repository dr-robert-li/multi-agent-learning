"""
Hierarchical Research AI Package
"""

__version__ = "0.2.2"
__author__ = "Dr. Robert Li"

from .workflows.research_workflow import HierarchicalResearchSystem
from .config.models import ModelConfig

__all__ = ["HierarchicalResearchSystem", "ModelConfig", "__version__", "__author__"]