"""
CLI Commands module for Hierarchical Research AI
"""

import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from rich.console import Console
from rich.table import Table


class CLICommands:
    """CLI command implementations"""
    
    def __init__(self, research_system):
        self.research_system = research_system
        self.console = Console()
    
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
            self.console.print("[yellow]No sessions found.[/yellow]")
            return
        
        table = Table(title="Research Sessions")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", style="blue")
        table.add_column("Created", style="yellow")
        
        for session in sessions:
            table.add_row(
                session.id[:8],
                session.name,
                session.status,
                session.created_at.strftime("%Y-%m-%d %H:%M")
            )
        
        self.console.print(table)
    
    def show_status(self):
        """Show system status"""
        status_table = Table(title="System Status")
        status_table.add_column("Component", style="bold cyan")
        status_table.add_column("Status", style="green")
        
        # Check model availability
        status_table.add_row("Privacy Mode", 
                           "Enabled" if self.research_system.model_config.privacy_mode else "Disabled")
        
        # Check workspace
        workspace_exists = Path(self.research_system.workspace_dir).exists()
        status_table.add_row("Workspace", 
                           "Ready" if workspace_exists else "Not Found")
        
        self.console.print(status_table)
    
    def show_costs(self):
        """Show cost summary"""
        costs = self.research_system.cost_tracker.get_session_summary()
        
        cost_table = Table(title="Cost Summary")
        cost_table.add_column("Provider", style="cyan")
        cost_table.add_column("Tokens Used", style="yellow")
        cost_table.add_column("Cost", style="green")
        
        for provider, data in costs.items():
            cost_table.add_row(
                provider,
                str(data.get('tokens', 0)),
                f"${data.get('cost', 0.0):.2f}"
            )
        
        self.console.print(cost_table)