"""
CLI Commands module for Hierarchical Research AI
"""

import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from .prompt_console import PromptConsole, create_table


class CLICommands:
    """CLI command implementations"""
    
    def __init__(self, research_system):
        self.research_system = research_system
        self.console = PromptConsole()
    
    async def research_command(self, topic: str = None, session_id: str = None, 
                              privacy_mode: bool = False, budget: float = 50.0):
        """Execute research command"""
        if session_id:
            # Resume existing session
            return await self.research_system.resume_session(session_id)
        else:
            # Start new research
            return await self.research_system.interactive_research(
                initial_topic=topic
            )
    
    def list_sessions(self):
        """List all research sessions"""
        sessions = self.research_system.session_manager.list_sessions()
        
        if not sessions:
            self.console.print("No sessions found.")
            return
        
        table = create_table("Research Sessions")
        table.add_column("ID")
        table.add_column("Name")
        table.add_column("Status")
        table.add_column("Created")
        
        for session in sessions:
            table.add_row(
                session.id[:8],
                session.name,
                session.status,
                session.created_at.strftime("%Y-%m-%d %H:%M")
            )
        
        table.render(self.console)
    
    def show_status(self):
        """Show system status"""
        status_table = create_table("System Status")
        status_table.add_column("Component")
        status_table.add_column("Status")
        
        # Check model availability
        status_table.add_row("Privacy Mode", 
                           "Enabled" if self.research_system.model_config.privacy_mode else "Disabled")
        
        # Check workspace
        workspace_exists = Path(self.research_system.workspace_dir).exists()
        status_table.add_row("Workspace", 
                           "Ready" if workspace_exists else "Not Found")
        
        status_table.render(self.console)
    
    def show_costs(self):
        """Show cost summary"""
        costs = self.research_system.cost_tracker.get_session_summary()
        
        cost_table = create_table("Cost Summary")
        cost_table.add_column("Provider")
        cost_table.add_column("Tokens Used")
        cost_table.add_column("Cost")
        
        for provider, data in costs.items():
            cost_table.add_row(
                provider,
                str(data.get('tokens', 0)),
                f"${data.get('cost', 0.0):.2f}"
            )
        
        cost_table.render(self.console)