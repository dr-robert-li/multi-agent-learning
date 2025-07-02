"""
Workflows module for Hierarchical Research AI
"""

from .supervisor import HierarchicalSupervisor
from .research_workflow import HierarchicalResearchSystem
from .report_generation import ReportGenerator

__all__ = ["HierarchicalSupervisor", "HierarchicalResearchSystem", "ReportGenerator"]