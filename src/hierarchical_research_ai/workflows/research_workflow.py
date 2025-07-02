"""
Main Research Workflow System

Orchestrates the complete hierarchical multi-agent research process.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pathlib import Path
import structlog  # type: ignore

from ..config.models import ModelConfig
from ..config.costs import CostTracker
from ..utils.session_manager import SessionManager, ResearchSession
from ..utils.memory_management import MemoryManager
from ..tools.research_tools import ResearchToolkit
from .supervisor import HierarchicalSupervisor
from .report_generation import ReportGenerator

logger = structlog.get_logger()


class ResearchProject:
    """Represents a research project"""
    
    def __init__(self, project_id: str, topic: str, requirements: Dict[str, Any]):
        self.id = project_id
        self.topic = topic
        self.requirements = requirements
        self.created_at = datetime.now()
        self.status = "initialized"
        self.progress = {
            "current_phase": "initialization",
            "completion_percentage": 0,
            "phases_completed": [],
            "start_time": datetime.now().isoformat()
        }
        self.results = {}


class HierarchicalResearchSystem:
    """Main research system orchestrating all components"""
    
    def __init__(self, 
                 cli_mode: bool = False,
                 privacy_mode: bool = False,
                 session: Optional[ResearchSession] = None,
                 workspace_dir: Optional[str] = None):
        
        # Configuration
        self.cli_mode = cli_mode
        self.privacy_mode = privacy_mode
        self.workspace_dir = workspace_dir or "./workspace"
        
        # Initialize core components
        self.model_config = ModelConfig()
        self.cost_tracker = CostTracker()
        self.session_manager = SessionManager()
        self.memory_manager = MemoryManager()
        self.research_toolkit = ResearchToolkit(self.workspace_dir)
        
        # Initialize workflow components
        self.supervisor = HierarchicalSupervisor(self.model_config, self.research_toolkit)
        self.report_generator = ReportGenerator(self.model_config, self.research_toolkit)
        
        # CLI controller (if in CLI mode)
        if self.cli_mode:
            from ..cli.conversation_controller import ConversationController
            self.cli_controller = ConversationController(self, session)
        
        # Current session
        self.current_session = session
        
        # Active projects
        self.projects = {}
        
        # Create workspace
        os.makedirs(self.workspace_dir, exist_ok=True)
        
        logger.info("HierarchicalResearchSystem initialized", 
                   cli_mode=cli_mode, 
                   privacy_mode=privacy_mode)
    
    def start_project(self, 
                     topic: str,
                     target_length: int = 50000,
                     citation_style: str = "APA",
                     quality_level: str = "academic_thesis",
                     privacy_mode: Optional[bool] = None,
                     budget_limit: float = 50.0,
                     session_name: Optional[str] = None,
                     **kwargs) -> ResearchProject:
        """
        Start a new research project
        
        Args:
            topic: Research topic
            target_length: Target word count
            citation_style: Citation style (APA, MLA, etc.)
            quality_level: Quality level (academic_thesis, professional_report, etc.)
            privacy_mode: Enable privacy mode
            budget_limit: Budget limit for API costs
            session_name: Name for the session
            **kwargs: Additional requirements
            
        Returns:
            ResearchProject instance
        """
        # Generate project ID
        project_id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Prepare requirements
        requirements = {
            "topic": topic,
            "target_length": target_length,
            "citation_style": citation_style,
            "quality_level": quality_level,
            "privacy_mode": privacy_mode if privacy_mode is not None else self.privacy_mode,
            "budget_limit": budget_limit,
            **kwargs
        }
        
        # Create project
        project = ResearchProject(project_id, topic, requirements)
        self.projects[project_id] = project
        
        # Create or update session
        if not self.current_session:
            self.current_session = self.session_manager.create_session(
                name=session_name or f"Research: {topic[:30]}",
                topic=topic,
                requirements=requirements,
                metadata={
                    "project_id": project_id,
                    "created_via": "start_project",
                    "privacy_mode": requirements["privacy_mode"]
                }
            )
        else:
            # Update existing session
            self.current_session.requirements.update(requirements)
            self.current_session.metadata["project_id"] = project_id
            self.session_manager.save_session(self.current_session)
        
        logger.info("Started new research project", 
                   project_id=project_id, 
                   topic=topic,
                   session_id=self.current_session.session_id)
        
        return project
    
    async def generate_report(self, project_id: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive research report
        
        Args:
            project_id: Project identifier
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary containing report results and metadata
        """
        if project_id not in self.projects:
            raise ValueError(f"Project {project_id} not found")
        
        project = self.projects[project_id]
        project.status = "running"
        
        logger.info("Starting report generation", project_id=project_id)
        
        try:
            # Execute the hierarchical workflow
            workflow_result = await self.supervisor.execute_workflow(
                research_topic=project.topic,
                requirements=project.requirements,
                progress_callback=progress_callback
            )
            
            # Generate the final report
            report_result = await self.report_generator.generate_final_report(
                agent_outputs=workflow_result["agent_outputs"],
                requirements=project.requirements,
                research_topic=project.topic
            )
            
            # Update project
            project.status = "completed" if workflow_result["status"] == "completed" else "completed_with_errors"
            project.progress = workflow_result["progress"]
            project.results = {
                "workflow_result": workflow_result,
                "report_result": report_result,
                "generation_time": datetime.now().isoformat()
            }
            
            # Update session
            if self.current_session:
                self.current_session.status = project.status
                self.current_session.progress = project.progress
                self.current_session.agent_outputs = workflow_result["agent_outputs"]
                self.current_session.metadata["final_result"] = report_result
                self.session_manager.save_session(self.current_session)
            
            # Prepare final result
            result = {
                "status": project.status,
                "project_id": project_id,
                "session_id": self.current_session.session_id if self.current_session else None,
                "output_path": report_result.get("output_path"),
                "word_count": report_result.get("word_count", 0),
                "section_count": report_result.get("section_count", 0),
                "source_count": len(workflow_result.get("user_sources", {}).get("documents", [])) + len(workflow_result.get("user_sources", {}).get("datasets", [])),
                "citation_count": report_result.get("citation_count", 0),
                "total_cost": self.cost_tracker.get_session_summary()["total_cost"],
                "errors": workflow_result.get("errors", []),
                "completed_agents": workflow_result.get("completed_agents", [])
            }
            
            logger.info("Report generation completed", 
                       project_id=project_id,
                       status=result["status"],
                       word_count=result["word_count"])
            
            return result
            
        except Exception as e:
            project.status = "failed"
            logger.error("Report generation failed", project_id=project_id, error=str(e))
            
            return {
                "status": "failed",
                "project_id": project_id,
                "session_id": self.current_session.session_id if self.current_session else None,
                "error": str(e),
                "total_cost": self.cost_tracker.get_session_summary()["total_cost"]
            }
    
    async def interactive_research(self, 
                                 initial_topic: Optional[str] = None,
                                 session_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Start interactive research session via CLI
        
        Args:
            initial_topic: Optional initial topic
            session_name: Optional session name
            
        Returns:
            Research results
        """
        if not self.cli_mode:
            raise ValueError("CLI mode not enabled. Initialize with cli_mode=True")
        
        if not hasattr(self, 'cli_controller'):
            from ..cli.conversation_controller import ConversationController
            self.cli_controller = ConversationController(self, self.current_session)
        
        # Start interactive session
        result = await self.cli_controller.start_interactive_session(
            initial_topic=initial_topic,
            session_name=session_name
        )
        
        return result
    
    async def resume_research(self, session_id: str) -> Dict[str, Any]:
        """
        Resume research from a saved session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Research results
        """
        # Load session
        session = self.session_manager.load_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        self.current_session = session
        
        # Check if research was already completed
        if session.status == "completed":
            logger.info("Research already completed", session_id=session_id)
            return session.metadata.get("final_result", {})
        
        # Resume research
        if session.progress.get("completion_percentage", 0) < 100:
            # Create project from session
            project_id = session.metadata.get("project_id")
            if not project_id:
                project_id = f"resumed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            project = ResearchProject(project_id, session.topic, session.requirements)
            project.progress = session.progress
            self.projects[project_id] = project
            
            # Continue research
            return await self.generate_report(project_id)
        else:
            # Already completed
            return session.metadata.get("final_result", {})
    
    async def generate_report_with_cli_feedback(self, 
                                              requirements: Dict[str, Any],
                                              progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Generate report with CLI feedback integration
        
        Args:
            requirements: Research requirements
            progress_callback: Progress callback function
            
        Returns:
            Research results
        """
        # Create project
        project = self.start_project(**requirements)
        
        # Generate report
        return await self.generate_report(project.id, progress_callback)
    
    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get status of a research project"""
        if project_id not in self.projects:
            return {"error": "Project not found"}
        
        project = self.projects[project_id]
        return {
            "project_id": project_id,
            "topic": project.topic,
            "status": project.status,
            "progress": project.progress,
            "created_at": project.created_at.isoformat(),
            "requirements": project.requirements
        }
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects"""
        return [
            {
                "project_id": project.id,
                "topic": project.topic,
                "status": project.status,
                "created_at": project.created_at.isoformat(),
                "progress": project.progress
            }
            for project in self.projects.values()
        ]
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary for current session"""
        return self.cost_tracker.get_session_summary()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "model_config": self.model_config.get_model_info(),
            "cost_summary": self.cost_tracker.get_session_summary(),
            "session_stats": self.session_manager.get_session_stats(),
            "workspace_dir": self.workspace_dir,
            "active_projects": len(self.projects),
            "current_session": self.current_session.session_id if self.current_session else None
        }