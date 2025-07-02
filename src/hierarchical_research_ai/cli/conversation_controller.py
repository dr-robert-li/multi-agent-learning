"""
Conversation Controller for CLI Interface

Manages the interactive conversation flow for requirement gathering.
"""

import os
import sys
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.markdown import Markdown

from .state_manager import ConversationStateManager
from .question_generator import QuestionGenerator
from .response_parser import ResponseParser
from ..config.models import ModelConfig
from ..tools.source_manager import SourceManager
from ..utils.session_manager import SessionManager, ResearchSession
from ..utils.memory_management import MemoryManager


class ConversationController:
    """Orchestrates CLI conversations for research requirement gathering"""
    
    def __init__(self, research_system: 'HierarchicalResearchSystem', session: Optional[ResearchSession] = None):
        self.research_system = research_system
        self.console = Console()
        self.state_manager = ConversationStateManager()
        self.question_generator = QuestionGenerator(research_system.model_config)
        self.response_parser = ResponseParser()
        self.source_manager = SourceManager()
        self.session_manager = SessionManager()
        self.memory_manager = MemoryManager()
        self.max_rounds = int(os.getenv("MAX_CLARIFICATION_ROUNDS", 5))
        
        # Current session
        self.current_session = session
        
        # Load session state if resuming
        if self.current_session:
            self._load_session_state()
    
    def _get_user_input(self, prompt_text: str) -> str:
        """Get user input with proper terminal handling"""
        # Temporarily disable logging to prevent interference
        import logging
        root_logger = logging.getLogger()
        original_level = root_logger.level
        root_logger.setLevel(logging.CRITICAL)
        
        try:
            # Create a new console without capture to ensure input visibility
            temp_console = Console(force_terminal=True, legacy_windows=True, quiet=True)
            response = Prompt.ask(prompt_text.rstrip(": "), console=temp_console)
            return response
        finally:
            # Restore original logging level
            root_logger.setLevel(original_level)
    
    def _load_session_state(self):
        """Load state from existing session"""
        if not self.current_session:
            return
        
        # Load conversation state
        self.state_manager.requirements = self.current_session.requirements
        self.state_manager.conversation_history = self.current_session.conversation_history
        
        # Load memory
        if hasattr(self.current_session, 'memory_data'):
            self.memory_manager.import_memory(self.current_session.memory_data)
        
        self.console.print(f"[green]Loaded session state:[/green] {len(self.current_session.conversation_history)} conversation turns")
    
    def _save_session_state(self):
        """Save current state to session"""
        if not self.current_session:
            return
        
        # Update session with current state
        self.current_session.requirements = self.state_manager.requirements
        self.current_session.conversation_history = self.state_manager.conversation_history
        self.current_session.source_ids = getattr(self.state_manager.requirements.get('user_sources', {}), 'get', lambda x, d: d)('source_ids', [])
        
        # Save memory state
        memory_data = self.memory_manager.export_memory()
        self.current_session.metadata['memory_data'] = memory_data
        
        # Update progress
        self.current_session.progress.update({
            'last_update': datetime.now().isoformat(),
            'conversation_turns': len(self.current_session.conversation_history),
            'requirements_completeness': self.state_manager.completeness_score
        })
        
        # Save to disk
        self.session_manager.save_session(self.current_session)
    
    async def start_interactive_session(self, initial_topic: Optional[str] = None, session_name: Optional[str] = None) -> Dict[str, Any]:
        """Main conversation loop with clarifying questions"""
        self.display_welcome()
        
        # Handle initial topic
        if not self.current_session:
            if not initial_topic:
                self.console.print("\n[bold cyan]What would you like to research?[/bold cyan]")
                initial_topic = self._get_user_input("Topic: ")
            
            # Extract and set topic
            topic = self.response_parser.extract_topic(initial_topic) or initial_topic
            self.state_manager.requirements["topic"] = topic
            self.state_manager.add_to_history("user", initial_topic)
            
            # Create new session
            if not session_name:
                default_name = f"Research: {topic[:30]}"
                self.console.print(f"Session name (optional, default: {default_name})")
                session_name = self._get_user_input("Session name: ").strip()
                if not session_name:
                    session_name = default_name
            
            self.current_session = self.session_manager.create_session(
                name=session_name,
                topic=topic,
                requirements=self.state_manager.requirements,
                metadata={
                    "created_via": "interactive_cli",
                    "privacy_mode": self.research_system.model_config.privacy_mode
                }
            )
            
            self.console.print(f"\n[bold blue]Research Topic:[/bold blue] {topic}")
            self.console.print(f"[dim]Session ID: {self.current_session.session_id}[/dim]")
        else:
            # Resuming session
            topic = self.current_session.topic
            self.console.print(f"\n[bold blue]Resuming Research:[/bold blue] {topic}")
            self.console.print(f"[dim]Session: {self.current_session.name}[/dim]")
        
        # Add conversation turn to memory
        if initial_topic:
            self.memory_manager.add_conversation_turn("user", initial_topic)
        
        # Show privacy mode warning if enabled
        if self.research_system.model_config.privacy_mode:
            self._show_privacy_warning()
        
        # Interactive requirement gathering (skip if resuming completed requirements)
        if not self.current_session or self.state_manager.completeness_score < 0.75:
            requirements = await self.gather_requirements(topic)
        else:
            requirements = self.state_manager.generate_research_config()
            self.console.print("\n[green]Using existing requirements from session[/green]")
        
        # Ask about user sources (skip if resuming and sources already added)
        if not self.current_session.source_ids:
            await self.handle_user_sources()
        else:
            self.console.print(f"\n[green]Using {len(self.current_session.source_ids)} sources from session[/green]")
        
        # Save session state before proceeding
        self._save_session_state()
        
        # Confirm research plan
        if self.confirm_research_plan(requirements):
            return await self.execute_research_with_feedback(requirements)
        else:
            self.console.print("\n[yellow]Research cancelled by user.[/yellow]")
            # Mark session as paused
            self.current_session.status = 'paused'
            self._save_session_state()
            return None
    
    def display_welcome(self):
        """Display welcome message and system information"""
        welcome_text = """
# Welcome to HierarchicalResearchAI

I'll help you conduct comprehensive research on any topic. 
I'll ask you a few questions to better understand your needs and deliver the best results.

**Features:**
- Deep autonomous research with multiple sources
- Academic-quality analysis and synthesis  
- Customizable output formats and styles
- Real-time progress tracking
- Cost monitoring and budget alerts
        """
        
        self.console.print(Panel(Markdown(welcome_text), title="Research Assistant", 
                                border_style="blue"))
    
    def _show_privacy_warning(self):
        """Show privacy mode warning"""
        warning = """
⚠️  **Privacy Mode Enabled**

- All processing will be done locally
- No data will be sent to external APIs
- Limited reasoning capabilities
- No real-time web access
- Slower processing speed

This mode is ideal for sensitive data but may produce less comprehensive results.
        """
        self.console.print(Panel(Markdown(warning), title="Privacy Mode", 
                                border_style="yellow"))
    
    async def gather_requirements(self, initial_topic: str) -> Dict[str, Any]:
        """Iteratively refine research requirements through conversation"""
        rounds = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            while rounds < self.max_rounds and not self.state_manager.assess_readiness():
                # Generate contextual questions
                task = progress.add_task("Analyzing requirements...", total=None)
                
                questions = await self.question_generator.generate_contextual_questions(
                    conversation_history=self.state_manager.conversation_history,
                    research_domain=initial_topic,
                    completeness_score=self.state_manager.completeness_score,
                    missing_requirements=self.state_manager.get_missing_requirements()
                )
                
                progress.remove_task(task)
                
                if not questions:
                    break
                
                # Ask questions and collect responses
                self.console.print(f"\n[bold]Round {rounds + 1} - Clarifying Questions:[/bold]")
                
                for i, question in enumerate(questions, 1):
                    self.console.print(f"\n[cyan]{i}.[/cyan] {question}")
                    try:
                        # Use helper method for clean input
                        response = self._get_user_input("   Your answer: ")
                        
                        if not response or response.strip() == "":
                            response = "No specific preference"
                    except (KeyboardInterrupt, EOFError):
                        self.console.print("\n[yellow]Skipping this question...[/yellow]")
                        response = "No answer provided"
                    
                    # Add to history
                    self.state_manager.add_to_history("assistant", question)
                    self.state_manager.add_to_history("user", response)
                    
                    # Add to memory
                    self.memory_manager.add_conversation_turn("assistant", question)
                    self.memory_manager.add_conversation_turn("user", response)
                    
                    # Parse and update requirements
                    updates = self.response_parser.parse_response(response, question)
                    for category, value in updates.items():
                        if category not in ["confirmed"]:
                            self.state_manager.update_requirements(category, value)
                
                rounds += 1
                self.state_manager.clarification_count = rounds
                
                # Save session state periodically
                self._save_session_state()
                
                # Show progress
                self._show_progress()
                
                # Ask if user wants to continue
                if rounds < self.max_rounds and not self.state_manager.assess_readiness():
                    self.console.print("\n[yellow]Would you like to provide more details? (y/n)[/yellow]")
                    continue_response = self._get_user_input("Continue: ").strip().lower()
                    if continue_response not in ['y', 'yes', '']:
                        break
        
        return self.state_manager.generate_research_config()
    
    def _show_progress(self):
        """Display requirement gathering progress"""
        score = self.state_manager.completeness_score
        bar_length = 30
        filled = int(bar_length * score)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        self.console.print(f"\n[bold]Requirement Completeness:[/bold] {bar} {score:.0%}")
    
    def confirm_research_plan(self, requirements: Dict[str, Any]) -> bool:
        """Display research plan for confirmation"""
        table = Table(title="Research Plan Summary", show_header=True, 
                     header_style="bold cyan")
        table.add_column("Aspect", style="cyan", width=20)
        table.add_column("Configuration", style="white")
        
        table.add_row("Topic", requirements.get("topic", "Not specified"))
        table.add_row("Target Length", f"{requirements.get('target_length', 50000):,} words")
        table.add_row("Citation Style", requirements.get("citation_style", "APA"))
        table.add_row("Audience", requirements.get("audience", "Academic"))
        table.add_row("Research Depth", requirements.get("research_depth", "Comprehensive"))
        table.add_row("Budget Limit", f"${requirements.get('budget_limit', 50.00):.2f}")
        table.add_row("Privacy Mode", "Yes" if requirements.get("privacy_mode", False) else "No")
        
        self.console.print("\n")
        self.console.print(table)
        
        # Show cost estimate
        self._show_cost_estimate(requirements)
        
        self.console.print("\n[bold]Proceed with this research plan? (y/n)[/bold]")
        proceed_response = self._get_user_input("Proceed: ").strip().lower()
        return proceed_response in ['y', 'yes', '']
    
    def _show_cost_estimate(self, requirements: Dict[str, Any]):
        """Show estimated cost for the research"""
        # Rough estimation based on target length
        words = requirements.get("target_length", 50000)
        
        # Estimate tokens (roughly 1.3 tokens per word)
        estimated_tokens = words * 1.3
        
        # Estimate costs (simplified)
        if requirements.get("privacy_mode"):
            estimated_cost = 0.0  # Local processing
        else:
            # Rough estimate: 20% research, 30% analysis, 50% generation
            research_cost = (estimated_tokens * 0.2 / 1_000_000) * 5.0  # Average of model costs
            analysis_cost = (estimated_tokens * 0.3 / 1_000_000) * 9.0
            generation_cost = (estimated_tokens * 0.5 / 1_000_000) * 2.4
            estimated_cost = research_cost + analysis_cost + generation_cost
        
        self.console.print(f"\n[bold]Estimated Cost:[/bold] ${estimated_cost:.2f}")
        
        if estimated_cost > requirements.get("budget_limit", 50.0):
            self.console.print("[yellow]⚠️  Warning: Estimated cost exceeds budget limit![/yellow]")
    
    async def execute_research_with_feedback(self, requirements: Dict[str, Any]):
        """Execute research with progress feedback"""
        self.console.print("\n[bold green]Starting research...[/bold green]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            "[progress.percentage]{task.percentage:>3.0f}%",
            console=self.console
        ) as progress:
            
            research_task = progress.add_task("Research Phase", total=100)
            analysis_task = progress.add_task("Analysis Phase", total=100)
            writing_task = progress.add_task("Report Writing", total=100)
            
            # Progress callback
            def update_progress(phase: str, percent: float):
                if phase == "research":
                    progress.update(research_task, completed=percent)
                elif phase == "analysis":
                    progress.update(analysis_task, completed=percent)
                elif phase == "writing":
                    progress.update(writing_task, completed=percent)
            
            # Execute research
            try:
                result = await self.research_system.generate_report_with_cli_feedback(
                    requirements=requirements,
                    progress_callback=update_progress
                )
                
                # Complete all tasks
                progress.update(research_task, completed=100)
                progress.update(analysis_task, completed=100)
                progress.update(writing_task, completed=100)
                
            except Exception as e:
                self.console.print(f"\n[red]Error during research:[/red] {str(e)}")
                return None
        
        # Show completion message
        if result:
            self._show_completion_summary(result)
            
            # Mark session as completed
            if self.current_session:
                self.current_session.status = 'completed'
                self.current_session.progress['completion_percentage'] = 100
                self.current_session.progress['completed_at'] = datetime.now().isoformat()
                
                # Add result to session
                self.current_session.metadata['final_result'] = result
                
                # Final save
                self._save_session_state()
                
                self.console.print(f"\n[dim]Session saved: {self.current_session.session_id}[/dim]")
        
        return result
    
    async def handle_user_sources(self):
        """Handle user-provided documents and data sources"""
        self.console.print("\n[bold cyan]Do you have any documents or data files you'd like to include in this research? (y/n)[/bold cyan]")
        include_sources = self._get_user_input("Include sources: ").strip().lower()
        if include_sources not in ['y', 'yes']:
            return
        
        self.console.print("\n[bold]Adding Your Sources[/bold]")
        self.console.print("You can add documents (PDF, Word, text files) and data (CSV, Excel, JSON files)")
        self.console.print("Sources can be local files or URLs\n")
        
        sources_added = []
        
        while True:
            self.console.print("Enter file path or URL (or 'done' to finish):")
            source_path = self._get_user_input("Source: ").strip()
            
            if source_path.lower() == 'done':
                break
            
            try:
                # Get metadata from user
                self.console.print("Brief description of this source (optional):")
                description = self._get_user_input("Description: ").strip()
                
                self.console.print("Tags for this source (comma-separated, optional):")
                tags = self._get_user_input("Tags: ").strip()
                
                metadata = {}
                if description:
                    metadata['description'] = description
                if tags:
                    metadata['tags'] = [tag.strip() for tag in tags.split(',')]
                
                # Add source
                with self.console.status(f"[bold green]Processing {source_path}..."):
                    source_id = await self.source_manager.add_source(
                        source=source_path,
                        metadata=metadata
                    )
                
                sources_added.append(source_id)
                self.console.print(f"[green]✓[/green] Added source: {source_path} (ID: {source_id})")
                
                self.console.print("Add another source? (y/n)")
                add_another = self._get_user_input("Add another: ").strip().lower()
                if add_another not in ['y', 'yes']:
                    break
                    
            except Exception as e:
                self.console.print(f"[red]✗[/red] Failed to add {source_path}: {str(e)}")
                self.console.print("Try another source? (y/n)")
                try_another = self._get_user_input("Try another: ").strip().lower()
                if try_another not in ['y', 'yes']:
                    break
        
        if sources_added:
            self.console.print(f"\n[green]Successfully added {len(sources_added)} sources to your research project.[/green]")
            self._show_sources_summary()
            
            # Update state with user sources
            self.state_manager.update_requirements("user_sources", {
                "source_ids": sources_added,
                "count": len(sources_added)
            })
    
    def _show_sources_summary(self):
        """Display summary of added sources"""
        summary = self.source_manager.get_sources_summary()
        
        table = Table(title="Your Sources Summary", show_header=True)
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="white")
        table.add_column("Details", style="green")
        
        table.add_row(
            "Documents",
            str(summary['documents']['count']),
            f"{summary['documents']['total_words']:,} words total"
        )
        
        table.add_row(
            "Data Sources",
            str(summary['data_sources']['count']),
            f"{summary['data_sources']['total_rows']:,} rows total"
        )
        
        self.console.print(table)
    
    def _show_completion_summary(self, result: Dict[str, Any]):
        """Show research completion summary"""
        summary = f"""
## Research Completed Successfully! ✅

**Report Details:**
- Length: {result.get('word_count', 0):,} words
- Sections: {result.get('section_count', 0)}
- Sources: {result.get('source_count', 0)}
- Citations: {result.get('citation_count', 0)}

**Output Location:**
{result.get('output_path', 'Not saved')}

**Total Cost:** ${result.get('total_cost', 0):.2f}
        """
        
        self.console.print(Panel(Markdown(summary), title="Completion Summary", 
                                border_style="green"))