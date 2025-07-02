"""
Conversation Controller for CLI Interface

Manages the interactive conversation flow for requirement gathering.
"""

import os
import sys
import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from .prompt_console import PromptConsole, create_table, create_panel, Progress
from .state_manager import ConversationStateManager
from .question_generator import QuestionGenerator
from .response_parser import ResponseParser
from .terminal_input import TerminalInputHandler
from ..config.models import ModelConfig
from ..tools.source_manager import SourceManager
from ..utils.session_manager import SessionManager, ResearchSession
from ..utils.memory_management import MemoryManager


class ConversationController:
    """Orchestrates CLI conversations for research requirement gathering"""
    
    def __init__(self, research_system: 'HierarchicalResearchSystem', session: Optional[ResearchSession] = None):
        self.research_system = research_system
        self.console = PromptConsole()
        self.state_manager = ConversationStateManager()
        self.question_generator = QuestionGenerator(research_system.model_config)
        self.response_parser = ResponseParser()
        self.source_manager = SourceManager()
        self.session_manager = SessionManager()
        self.memory_manager = MemoryManager()
        self.max_rounds = int(os.getenv("MAX_CLARIFICATION_ROUNDS", 5))
        
        # Use prompt_toolkit directly for reliable input
        # self.input_handler = TerminalInputHandler(self.console) # Disabled - using prompt_toolkit directly
        
        # Current session
        self.current_session = session
        
        # Load session state if resuming
        if self.current_session:
            self._load_session_state()
    
    def _get_user_input(self, prompt_text: str) -> str:
        """Get user input using prompt_toolkit for reliable visibility"""
        return self.console.input(prompt_text)
    
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
        
        self.console.print(f"Loaded session state: {len(self.current_session.conversation_history)} conversation turns")
    
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
                self.console.print("\nWhat would you like to research?")
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
            
            self.console.print(f"\nResearch Topic: {topic}", style='blue')
            self.console.print(f"Session ID: {self.current_session.session_id}", style='dim')
        else:
            # Resuming session
            topic = self.current_session.topic
            self.console.print(f"\nResuming Research: {topic}", style='blue')
            self.console.print(f"Session: {self.current_session.name}", style='dim')
        
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
            self.console.print("\nUsing existing requirements from session", style='success')
        
        # Ask about user sources (skip if resuming and sources already added)
        if not self.current_session.source_ids:
            await self.handle_user_sources()
        else:
            self.console.print(f"\nUsing {len(self.current_session.source_ids)} sources from session", style='success')
        
        # Save session state before proceeding
        self._save_session_state()
        
        # Confirm research plan
        if self.confirm_research_plan(requirements):
            return await self.execute_research_with_feedback(requirements)
        else:
            self.console.print("\nResearch cancelled by user.", style='warning')
            # Mark session as paused
            self.current_session.status = 'paused'
            self._save_session_state()
            return None
    
    def display_welcome(self):
        """Display welcome message and system information"""
        # Check if strategic analysis mode is enabled
        strategic_mode = os.getenv("STRATEGIC_ANALYSIS_MODE", "true").lower() == "true"
        question_depth = os.getenv("CLARIFICATION_DEPTH", "standard").lower()
        
        if strategic_mode:
            welcome_text = """Welcome to HierarchicalResearchAI - Strategic Analysis Mode

I'll help you conduct executive-level strategic business analysis using a Strategic Analysis Template framework.
I'll ask focused questions to understand your strategic context and deliver board-ready insights.

Strategic Features:
- Executive-focused business analysis framework
- Strategic challenge diagnosis and recommendation
- Competitive positioning and market analysis
- Implementation roadmaps with ROI projections
- Board-ready deliverables and executive summaries
- Industry best practices and proven frameworks

Question Depth: """ + question_depth.upper() + """
- MINIMAL: Essential strategic context only (1-2 questions)
- STANDARD: Focused strategic areas (2-3 questions)  
- COMPREHENSIVE: Thorough strategic analysis (3-4 questions)
- EXECUTIVE: High-level business impact focus (2-3 questions)"""
        else:
            welcome_text = """Welcome to HierarchicalResearchAI

I'll help you conduct comprehensive research on any topic. 
I'll ask you a few questions to better understand your needs and deliver the best results.

Features:
- Deep autonomous research with multiple sources
- Academic-quality analysis and synthesis  
- Customizable output formats and styles
- Real-time progress tracking
- Cost monitoring and budget alerts"""
        
        title = "Strategic Research Assistant" if strategic_mode else "Research Assistant"
        panel = create_panel(welcome_text, title=title)
        panel.render(self.console)
    
    def _show_privacy_warning(self):
        """Show privacy mode warning"""
        warning = """⚠️  Privacy Mode Enabled

- All processing will be done locally
- No data will be sent to external APIs
- Limited reasoning capabilities
- No real-time web access
- Slower processing speed

This mode is ideal for sensitive data but may produce less comprehensive results."""
        
        panel = create_panel(warning, title="Privacy Mode")
        panel.render(self.console)
    
    async def gather_requirements(self, initial_topic: str) -> Dict[str, Any]:
        """Iteratively refine research requirements through conversation"""
        # Set the initial topic if not already set
        if not self.state_manager.requirements.get("topic"):
            self.state_manager.update_requirements("topic", initial_topic)
        
        rounds = 0
        
        with Progress(self.console) as progress:
            
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
                self.console.print(f"\nRound {rounds + 1} - Clarifying Questions:", style='bold')
                
                for i, question in enumerate(questions, 1):
                    self.console.print(f"\n{i}. {question}", style='cyan')
                    try:
                        # Use helper method for clean input
                        response = self._get_user_input("   Your answer: ")
                        
                        if not response or response.strip() == "":
                            response = "No specific preference"
                    except (KeyboardInterrupt, EOFError):
                        self.console.print("\nSkipping this question...", style='warning')
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
                    if not self.console.confirm("Would you like to provide more details?", default=True):
                        break
        
        return self.state_manager.generate_research_config()
    
    def _show_progress(self):
        """Display requirement gathering progress"""
        score = self.state_manager.completeness_score
        bar_length = 30
        filled = int(bar_length * score)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        self.console.print(f"\nRequirement Completeness: {bar} {score:.0%}", style='bold')
    
    def confirm_research_plan(self, requirements: Dict[str, Any]) -> bool:
        """Display research plan for confirmation"""
        table = create_table("Research Plan Summary", show_header=True)
        table.add_column("Aspect", width=20)
        table.add_column("Configuration")
        
        # Helper function to safely convert values to strings
        def safe_str(value, default="Not specified"):
            if isinstance(value, dict):
                if not value:
                    return default
                # Convert dict to readable string
                return ", ".join([f"{k}: {v}" for k, v in value.items() if v])
            elif isinstance(value, list):
                if not value:
                    return default
                return ", ".join(str(item) for item in value)
            elif value is None or value == "":
                return default
            else:
                return str(value)
        
        table.add_row("Topic", safe_str(requirements.get("topic")))
        table.add_row("Target Length", f"{requirements.get('target_length', 50000):,} words")
        table.add_row("Citation Style", safe_str(requirements.get("citation_style"), "APA"))
        table.add_row("Audience", safe_str(requirements.get("audience"), "Academic"))
        table.add_row("Research Depth", safe_str(requirements.get("research_depth"), "Comprehensive"))
        table.add_row("Budget Limit", f"${requirements.get('budget_limit', 50.00):.2f}")
        table.add_row("Privacy Mode", "Yes" if requirements.get("privacy_mode", False) else "No")
        
        self.console.print("")
        table.render(self.console)
        
        # Show cost estimate
        self._show_cost_estimate(requirements)
        
        self.console.print("\nProceed with this research plan?", style='bold')
        return self.console.confirm("Proceed", default=True)
    
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
        
        self.console.print(f"\nEstimated Cost: ${estimated_cost:.2f}", style='bold')
        
        if estimated_cost > requirements.get("budget_limit", 50.0):
            self.console.print("⚠️  Warning: Estimated cost exceeds budget limit!", style='warning')
    
    async def execute_research_with_feedback(self, requirements: Dict[str, Any]):
        """Execute research with progress feedback"""
        self.console.print("\nStarting research...\n", style='success')
        
        with Progress(self.console) as progress:
            
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
                self.console.print(f"\nError during research: {str(e)}", style='error')
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
                
                self.console.print(f"\nSession saved: {self.current_session.session_id}")
        
        return result
    
    async def handle_user_sources(self):
        """Handle user-provided documents and data sources"""
        self.console.print("\nDo you have any documents or data files you'd like to include in this research? (y/n)")
        include_sources = self._get_user_input("Include sources: ").strip().lower()
        if include_sources not in ['y', 'yes']:
            return
        
        self.console.print("\nAdding Your Sources")
        self.console.print("You can add:")
        self.console.print("  • Folders containing documents or data files")
        self.console.print("  • Individual files (PDF, Word, CSV, Excel, JSON, etc.)")
        self.console.print("  • Website URLs for web content")
        self.console.print("  • API endpoints for data retrieval")
        self.console.print("  • MCP server addresses for connected data sources")
        self.console.print("\nEnter multiple sources separated by commas or new lines\n")
        
        sources_added = []
        
        while True:
            self.console.print("Enter sources (folders, files, URLs, API endpoints, or MCP addresses):")
            self.console.print("Examples:")
            self.console.print("  • /path/to/documents/folder")
            self.console.print("  • /path/to/file.pdf, https://example.com/data.json")
            self.console.print("  • https://api.example.com/v1/data")
            self.console.print("  • mcp://server.example.com:5000/dataset")
            self.console.print("\nEnter 'done' when finished:")
            
            source_input = self._get_user_input("Sources: ").strip()
            
            if source_input.lower() == 'done':
                break
            
            # Parse multiple sources (comma or newline separated)
            sources = self._parse_source_input(source_input)
            
            if not sources:
                self.console.print("No valid sources found. Please try again.")
                continue
            
            # Get common metadata for this batch
            self.console.print("\nProvide metadata for these sources (optional):")
            self.console.print("Brief description:")
            description = self._get_user_input("Description: ").strip()
            
            self.console.print("Tags (comma-separated):")
            tags = self._get_user_input("Tags: ").strip()
            
            metadata = {}
            if description:
                metadata['description'] = description
            if tags:
                metadata['tags'] = [tag.strip() for tag in tags.split(',')]
            
            # Process each source
            for source_path in sources:
                await self._process_single_source(source_path, metadata, sources_added)
            
            self.console.print(f"\nProcessed {len(sources)} sources.")
            self.console.print("Add more sources? (y/n)")
            add_more = self._get_user_input("Add more: ").strip().lower()
            if add_more not in ['y', 'yes']:
                break
        
        if sources_added:
            self.console.print(f"\nSuccessfully added {len(sources_added)} sources to your research project.")
            self._show_sources_summary()
            
            # Update state with user sources
            self.state_manager.update_requirements("user_sources", {
                "source_ids": sources_added,
                "count": len(sources_added)
            })
    
    def _show_sources_summary(self):
        """Display summary of added sources"""
        summary = self.source_manager.get_sources_summary()
        
        table = create_table("Your Sources Summary", show_header=True)
        table.add_column("Type")
        table.add_column("Count")
        table.add_column("Details")
        
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
        
        table.render(self.console)
    
    def _show_completion_summary(self, result: Dict[str, Any]):
        """Show research completion summary"""
        summary = f"""Research Completed Successfully! ✅

Report Details:
- Length: {result.get('word_count', 0):,} words
- Sections: {result.get('section_count', 0)}
- Sources: {result.get('source_count', 0)}
- Citations: {result.get('citation_count', 0)}

Output Location:
{result.get('output_path', 'Not saved')}

Total Cost: ${result.get('total_cost', 0):.2f}"""
        
        panel = create_panel(summary, title="Completion Summary")
        panel.render(self.console)
    
    def _parse_source_input(self, source_input: str) -> List[str]:
        """Parse and validate multiple source inputs from user"""
        sources = []
        
        # Split by comma or newline
        raw_sources = []
        if ',' in source_input:
            raw_sources = [s.strip() for s in source_input.split(',')]
        else:
            raw_sources = [s.strip() for s in source_input.split('\n')]
        
        # Clean and validate each source
        for raw_source in raw_sources:
            if not raw_source:
                continue
                
            # Remove quotes if present
            source = raw_source.strip().strip('"\'')
            
            if self._is_valid_source(source):
                sources.append(source)
            else:
                self.console.print(f"Skipping invalid source: {source}")
        
        return sources
    
    def _is_valid_source(self, source: str) -> bool:
        """Validate if a source path/URL is valid"""
        # Check if it's a URL
        if source.startswith(('http://', 'https://')):
            return True
        
        # Check if it's an API endpoint
        if source.startswith(('api:', 'api://', 'rest://')):
            return True
        
        # Check if it's an MCP server address
        if source.startswith('mcp://'):
            return True
        
        # Check if it's a local path (file or folder)
        if os.path.exists(source):
            return True
        
        # Check if it looks like a valid path format (may not exist yet)
        if os.path.isabs(source) or source.startswith('.'):
            return True
        
        return False
    
    async def _process_single_source(self, source_path: str, metadata: Dict[str, Any], sources_added: List[str]):
        """Process a single source and add it to the project"""
        try:
            self.console.print(f"Processing: {source_path}")
            
            # Determine source type
            source_type = self._determine_source_type(source_path)
            
            # Add to source manager
            source_id = await self.source_manager.add_source(
                source=source_path,
                source_type=source_type,
                metadata=metadata
            )
            
            sources_added.append(source_id)
            self.console.print(f"✓ Added: {source_path} (ID: {source_id})")
            
        except Exception as e:
            self.console.print(f"✗ Failed to process {source_path}: {str(e)}")
    
    def _determine_source_type(self, source_path: str) -> str:
        """Determine the type of source for processing"""
        # URL
        if source_path.startswith(('http://', 'https://')):
            # Check if it's a document URL or web page
            if any(ext in source_path.lower() for ext in ['.pdf', '.docx', '.doc', '.txt', '.md', '.html', '.htm']):
                return 'document'
            
            # Check for common web document patterns (Wikipedia, blogs, articles, etc.)
            web_document_patterns = [
                'wikipedia.org', 'wiki', 'blog', 'article', 'news', 'medium.com',
                'stackoverflow.com', 'github.com', 'reddit.com', 'linkedin.com'
            ]
            
            if any(pattern in source_path.lower() for pattern in web_document_patterns):
                return 'document'
            
            # Check for API endpoints and data sources
            api_patterns = [
                '/api/', '/v1/', '/v2/', '/data/', '.json', '.csv', '.xml', 
                'api.', 'data.', 'feeds.'
            ]
            
            if any(pattern in source_path.lower() for pattern in api_patterns):
                return 'data'
            
            # Default to document for general web pages
            return 'document'
        
        # API endpoint
        if source_path.startswith(('api:', 'api://', 'rest://')):
            return 'data'
        
        # MCP server
        if source_path.startswith('mcp://'):
            return 'data'
        
        # Local path
        if os.path.exists(source_path):
            if os.path.isdir(source_path):
                # Folder - check what's inside to determine predominant type
                return self._analyze_folder_type(source_path)
            else:
                # File - check extension
                return self._analyze_file_type(source_path)
        
        # Default to document for unknown types
        return 'document'
    
    def _analyze_folder_type(self, folder_path: str) -> str:
        """Analyze folder contents to determine predominant source type"""
        document_count = 0
        data_count = 0
        
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_type = self._analyze_file_type(file)
                    if file_type == 'document':
                        document_count += 1
                    elif file_type == 'data':
                        data_count += 1
        except:
            pass
        
        # Return the predominant type, default to document
        return 'data' if data_count > document_count else 'document'
    
    def _analyze_file_type(self, file_path: str) -> str:
        """Analyze file extension to determine source type"""
        from pathlib import Path
        
        extension = Path(file_path).suffix.lower()
        
        document_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md', '.html', '.htm', '.xml', '.rtf'}
        data_extensions = {'.csv', '.json', '.jsonl', '.xlsx', '.xls', '.db', '.sqlite', '.parquet'}
        
        if extension in document_extensions:
            return 'document'
        elif extension in data_extensions:
            return 'data'
        else:
            # Default to document for unknown extensions
            return 'document'