"""
CLI Entry Point and Command Interface
"""

import asyncio
import click
import sys
import os
import logging
import structlog
from .prompt_console import PromptConsole, create_table
from .conversation_controller import ConversationController
from ..workflows.research_workflow import HierarchicalResearchSystem

# Configure logging based on environment variable
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(message)s'
)

# Configure structlog to use the same log level
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, log_level, logging.INFO)
    ),
)

console = PromptConsole()


def run_async_safe(coro):
    """
    Safely run an async coroutine, handling cases where an event loop is already running.
    """
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        # If we're in an event loop, we need to handle this differently
        # For CLI usage, we'll actually create a new thread with its own loop
        import threading
        import concurrent.futures
        
        result_container = {'result': None, 'exception': None}
        
        def run_in_thread():
            try:
                # Create a new event loop for this thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    result_container['result'] = new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()
            except Exception as e:
                result_container['exception'] = e
        
        thread = threading.Thread(target=run_in_thread)
        thread.start()
        thread.join()
        
        if result_container['exception']:
            raise result_container['exception']
        return result_container['result']
        
    except RuntimeError:
        # No event loop running, safe to use asyncio.run
        return asyncio.run(coro)


@click.group()
@click.option('--privacy-mode', is_flag=True, help='Enable privacy mode (local processing)')
@click.option('--budget', type=float, help='Research budget limit')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, privacy_mode, budget, verbose):
    """HierarchicalResearchAI - Interactive Research Assistant"""
    ctx.ensure_object(dict)
    ctx.obj['privacy_mode'] = privacy_mode
    ctx.obj['budget'] = budget
    ctx.obj['verbose'] = verbose


@cli.command()
@click.option('--topic', help='Initial research topic')
@click.option('--interactive/--batch', default=True, help='Interactive vs batch mode')
@click.option('--session-id', help='Resume existing session')
@click.option('--session-name', help='Name for new session')
@click.pass_context
def research(ctx, topic, interactive, session_id, session_name):
    """Start a research project"""
    
    async def run_research():
        from ..utils.session_manager import SessionManager
        
        session_manager = SessionManager()
        
        # Handle session management
        session = None
        if session_id:
            # Resume existing session
            session = session_manager.load_session(session_id)
            if not session:
                console.print(f"Error: Session '{session_id}' not found")
                return
            console.print(f"Resuming session: {session.name}")
            console.print(f"Topic: {session.topic}")
        else:
            # Check for existing sessions and offer to resume
            recent_sessions = session_manager.list_sessions()[:5]  # Show 5 most recent
            
            if recent_sessions and interactive:
                console.print("\nRecent Sessions:")
                for i, sess in enumerate(recent_sessions, 1):
                    console.print(f"  {i}. {sess['name']} - {sess['topic']} ({sess.get('last_accessed_days', 0)} days ago)")
                
                console.print("  n. Start new session")
                
                # Allow environment variable to bypass interactive choice for testing
                auto_choice = os.getenv('CLI_AUTO_CHOICE', '')
                if auto_choice:
                    choice = auto_choice
                    console.print(f"Auto-selected: {choice}")
                else:
                    choice = console.input("Choose session to resume or 'n' for new [n]: ") or "n"
                
                if choice.isdigit() and 1 <= int(choice) <= len(recent_sessions):
                    resumed_session_id = recent_sessions[int(choice) - 1]['session_id']
                    session = session_manager.load_session(resumed_session_id)
                    if session:
                        console.print(f"Resuming session: {session.name}")
                    # else: session remains None for new session
        
        # Initialize research system
        research_system = HierarchicalResearchSystem(
            cli_mode=interactive,
            privacy_mode=ctx.obj.get('privacy_mode', False),
            session=session  # Pass existing session if resuming
        )
        
        if interactive:
            # CLI conversational mode
            result = await research_system.interactive_research(
                initial_topic=topic,
                session_name=session_name
            )
        else:
            # Batch mode for programmatic use
            if not topic and not session:
                console.print("Error: Topic required for batch mode")
                return
            
            if session:
                # Resume batch processing from session
                result = await research_system.resume_research(session.session_id)
            else:
                # Start new batch research
                project = research_system.start_project(
                    topic=topic,
                    budget_limit=ctx.obj.get('budget', 50.0),
                    session_name=session_name
                )
                result = await research_system.generate_report(project.id)
        
        if result:
            console.print(f"\nResearch completed successfully!")
            if 'output_path' in result:
                console.print(f"Report saved to: {result['output_path']}")
            if 'session_id' in result:
                console.print(f"Session ID: {result['session_id']}")
    
    # Run the async function with proper event loop handling
    run_async_safe(run_research())


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status and configuration"""
    from ..config.models import ModelConfig
    
    console.print("\nSystem Status\n")
    
    try:
        model_config = ModelConfig()
        info = model_config.get_model_info()
        
        console.print(f"Privacy Mode: {'Enabled' if info['privacy_mode'] else 'Disabled'}")
        console.print(f"CLI Mode: {'Enabled' if info['cli_mode'] else 'Disabled'}")
        console.print("\nConfigured Models:")
        
        for role, model in info['models'].items():
            console.print(f"  • {role.capitalize()}: {model}")
        
    except Exception as e:
        console.print(f"Error checking status: {str(e)}")
        console.print("\nMake sure you have configured your environment variables.")
        console.print("Copy .env.example to .env and add your API keys.")


@cli.command()
@click.option('--source', help='Source file path or URL')
@click.option('--type', 'source_type', help='Source type (document/data/auto)')
@click.option('--description', help='Description of the source')
@click.option('--tags', help='Comma-separated tags')
@click.pass_context
def add_source(ctx, source, source_type, description, tags):
    """Add a document or data source to your research project"""
    from ..tools.source_manager import SourceManager
    
    async def run_add_source():
        source_manager = SourceManager()
        
        if not source:
            source = console.input("Enter file path or URL: ")
        
        metadata = {}
        if description:
            metadata['description'] = description
        if tags:
            metadata['tags'] = [tag.strip() for tag in tags.split(',')]
        
        try:
            console.print(f"Processing source: {source}")
            source_id = await source_manager.add_source(
                source=source,
                source_type=source_type or 'auto',
                metadata=metadata
            )
            console.print(f"✓ Successfully added source with ID: {source_id}")
            
            # Show summary
            source_data = source_manager.get_source(source_id)
            ingested_data = source_data['ingested_data']
            
            if source_data['source_type'] == 'document':
                console.print(f"Document: {ingested_data.get('word_count', 0):,} words")
            else:
                console.print(f"Data: {ingested_data.get('metadata', {}).get('row_count', 0):,} rows")
                
        except Exception as e:
            console.print(f"Error: {str(e)}")
    
    run_async_safe(run_add_source())


@cli.command()
@click.option('--type', 'source_type', help='Filter by source type (document/data)')
def list_sources(source_type):
    """List all sources in your research project"""
    from ..tools.source_manager import SourceManager
    
    source_manager = SourceManager()
    sources = source_manager.list_sources(source_type)
    
    if not sources:
        console.print("No sources found.")
        return
    
    table = create_table("Your Research Sources")
    table.add_column("ID")
    table.add_column("Type")
    table.add_column("Source")
    table.add_column("Description")
    table.add_column("Added")
    
    for source in sources:
        description = source.get('user_metadata', {}).get('description', '')
        added = source.get('added_timestamp', '')[:10]  # Just date part
        
        table.add_row(
            source['id'][:12] + "...",  # Truncate ID
            source['source_type'].title(),
            source['original_source'][:50] + ("..." if len(source['original_source']) > 50 else ""),
            description[:30] + ("..." if len(description) > 30 else ""),
            added
        )
    
    table.render(console)
    
    # Show summary
    summary = source_manager.get_sources_summary()
    console.print(f"\nTotal: {summary['total_sources']} sources")


@cli.command()
@click.argument('source_id')
def remove_source(source_id):
    """Remove a source from your research project"""
    from ..tools.source_manager import SourceManager
    
    source_manager = SourceManager()
    
    if source_manager.remove_source(source_id):
        console.print(f"✓ Removed source: {source_id}")
    else:
        console.print(f"Source not found: {source_id}")


@cli.command()
@click.argument('query')
@click.option('--type', 'source_type', help='Filter by source type (document/data)')
def search_sources(query, source_type):
    """Search your sources by content or metadata"""
    from ..tools.source_manager import SourceManager
    
    source_manager = SourceManager()
    results = source_manager.search_sources(query, source_type)
    
    if not results:
        console.print(f"No sources found matching '{query}'")
        return
    
    console.print(f"Found {len(results)} sources matching '{query}':\n")
    
    for result in results[:10]:  # Limit to top 10
        source_data = result['source_data']
        score = result['relevance_score']
        
        console.print(f"ID: {source_data['id']}")
        console.print(f"Source: {source_data['original_source']}")
        console.print(f"Relevance: {score}/10")
        console.print(f"Type: {source_data['source_type']}")
        
        description = source_data.get('user_metadata', {}).get('description')
        if description:
            console.print(f"Description: {description}")
        
        console.print("---")


@cli.command()
def sources_summary():
    """Show summary of all sources in your research project"""
    from ..tools.source_manager import SourceManager
    
    source_manager = SourceManager()
    summary = source_manager.get_sources_summary()
    
    console.print("\nSources Summary\n")
    
    # Overview
    console.print(f"Total Sources: {summary['total_sources']}")
    console.print(f"Documents: {summary['documents']['count']} ({summary['documents']['total_words']:,} words)")
    console.print(f"Data Sources: {summary['data_sources']['count']} ({summary['data_sources']['total_rows']:,} rows)")
    
    # Recent additions
    if summary['recent_additions']:
        console.print("\nRecent Additions:")
        for recent in summary['recent_additions']:
            console.print(f"  • {recent['source']} ({recent['added'][:10]})")


# Session Management Commands
@cli.command()
@click.option('--status', help='Filter by status (active/completed/paused/error)')
def sessions(status):
    """List all research sessions"""
    from ..utils.session_manager import SessionManager
    
    session_manager = SessionManager()
    sessions_list = session_manager.list_sessions(status)
    
    if not sessions_list:
        console.print("No sessions found.")
        return
    
    table = create_table("Research Sessions")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Topic")
    table.add_column("Status")
    table.add_column("Created")
    table.add_column("Last Access")
    
    for session in sessions_list:
        status_color = {
            "active": "green",
            "completed": "blue", 
            "paused": "yellow",
            "error": "red"
        }.get(session.get('status', 'unknown'), "white")
        
        table.add_row(
            session['session_id'][:8] + "...",
            session.get('name', 'Unnamed')[:30],
            session.get('topic', 'No topic')[:40],
            session.get('status', 'unknown'),
            session.get('created_at', '')[:10],
            f"{session.get('last_accessed_days', 0)} days ago"
        )
    
    table.render(console)
    
    # Show statistics
    stats = session_manager.get_session_stats()
    console.print(f"\nTotal: {stats['total_sessions']} sessions "
                 f"({stats['active_sessions']} active, {stats['completed_sessions']} completed)")


@cli.command()
@click.argument('session_id')
def session_info(session_id):
    """Show detailed information about a session"""
    from ..utils.session_manager import SessionManager
    
    session_manager = SessionManager()
    session = session_manager.load_session(session_id)
    
    if not session:
        console.print(f"Session not found: {session_id}")
        return
    
    # Basic info
    console.print(f"\nSession Details")
    console.print(f"ID: {session.session_id}")
    console.print(f"Name: {session.name}")
    console.print(f"Topic: {session.topic}")
    console.print(f"Status: {session.status}")
    console.print(f"Created: {session.created_at}")
    console.print(f"Last Accessed: {session.last_accessed}")
    console.print(f"Age: {session.get_age_days()} days")
    
    # Progress info
    if session.progress:
        console.print(f"\nProgress:")
        console.print(f"Current Phase: {session.progress.get('current_phase', 'Unknown')}")
        console.print(f"Completion: {session.progress.get('completion_percentage', 0)}%")
        
        phases = session.progress.get('phases_completed', [])
        if phases:
            console.print(f"Completed Phases: {', '.join(phases)}")
    
    # Sources info
    if session.source_ids:
        console.print(f"\nSources: {len(session.source_ids)} items")
    
    # Agent outputs
    if session.agent_outputs:
        console.print(f"\nAgent Outputs: {len(session.agent_outputs)} agents completed")
    
    # Conversation
    if session.conversation_history:
        console.print(f"\nConversation: {len(session.conversation_history)} turns")


@cli.command()
@click.argument('session_id')
@click.confirmation_option(prompt='Are you sure you want to delete this session?')
def delete_session(session_id):
    """Delete a research session permanently"""
    from ..utils.session_manager import SessionManager
    
    session_manager = SessionManager()
    
    if session_manager.delete_session(session_id):
        console.print(f"✓ Deleted session: {session_id}")
    else:
        console.print(f"Failed to delete session: {session_id}")


@cli.command()
@click.argument('query')
def search_sessions(query):
    """Search sessions by name, topic, or content"""
    from ..utils.session_manager import SessionManager
    
    session_manager = SessionManager()
    results = session_manager.search_sessions(query)
    
    if not results:
        console.print(f"No sessions found matching '{query}'")
        return
    
    console.print(f"Found {len(results)} sessions matching '{query}':\n")
    
    for result in results[:10]:  # Limit to top 10
        console.print(f"ID: {result['session_id'][:12]}...")
        console.print(f"Name: {result.get('name', 'Unnamed')}")
        console.print(f"Topic: {result.get('topic', 'No topic')}")
        console.print(f"Relevance: {result.get('relevance_score', 0)}/10")
        console.print("---")


@cli.command()
@click.argument('session_id')
@click.argument('export_path')
def export_session(session_id, export_path):
    """Export a session to a file"""
    from ..utils.session_manager import SessionManager
    
    session_manager = SessionManager()
    
    if session_manager.export_session(session_id, export_path):
        console.print(f"✓ Exported session to: {export_path}")
    else:
        console.print(f"Failed to export session: {session_id}")


@cli.command()
@click.argument('import_path')
def import_session(import_path):
    """Import a session from a file"""
    from ..utils.session_manager import SessionManager
    
    session_manager = SessionManager()
    new_session_id = session_manager.import_session(import_path)
    
    if new_session_id:
        console.print(f"✓ Imported session with ID: {new_session_id}")
    else:
        console.print(f"Failed to import session from: {import_path}")


@cli.command()
@click.option('--max-age', type=int, default=30, help='Maximum age in days')
@click.option('--max-inactive', type=int, default=7, help='Maximum inactive days')
@click.confirmation_option(prompt='Are you sure you want to cleanup old sessions?')
def cleanup_sessions(max_age, max_inactive):
    """Clean up old or inactive sessions"""
    from ..utils.session_manager import SessionManager
    
    session_manager = SessionManager()
    deleted_count = session_manager.cleanup_old_sessions(max_age, max_inactive)
    
    if deleted_count > 0:
        console.print(f"✓ Cleaned up {deleted_count} old sessions")
    else:
        console.print("No sessions needed cleanup")


@cli.command()
def sessions_stats():
    """Show session statistics and usage"""
    from ..utils.session_manager import SessionManager
    
    session_manager = SessionManager()
    stats = session_manager.get_session_stats()
    
    console.print("\nSession Statistics\n")
    console.print(f"Total Sessions: {stats['total_sessions']}")
    console.print(f"Active Sessions: {stats['active_sessions']}")
    console.print(f"Completed Sessions: {stats['completed_sessions']}")
    console.print(f"Paused Sessions: {stats.get('paused_sessions', 0)}")
    console.print(f"Error Sessions: {stats.get('error_sessions', 0)}")
    
    if stats['total_sessions'] > 0:
        console.print(f"Average Age: {stats.get('average_age_days', 0):.1f} days")
        console.print(f"Oldest Session: {stats.get('oldest_session_days', 0)} days")
        console.print(f"Most Recent Access: {stats.get('most_recent_access_days', 0)} days ago")


@cli.command()
def version():
    """Show version information"""
    from .. import __version__
    console.print(f"HierarchicalResearchAI v{__version__}")


@cli.command()
def test_input():
    """Test terminal input methods to diagnose visibility issues"""
    from .terminal_input import TerminalInputHandler
    
    console.print("Testing Terminal Input Methods\n")
    console.print("This will test different input methods to find the best one for your terminal.")
    console.print("For each test, please type 'test' and press Enter.\n")
    
    handler = TerminalInputHandler(console)
    results = handler.test_input_methods()
    
    console.print("\n" + "="*60)
    console.print("RESULTS:")
    console.print("="*60)
    
    working_methods = []
    
    for method, result in results.items():
        status = result['status']
        if status == 'success':
            visible = result.get('visible', False)
            response = result.get('response', '')
            
            if visible:
                console.print(f"✓ {method:12}: WORKING - Input visible, got: '{response}'")
                working_methods.append(method)
            else:
                console.print(f"~ {method:12}: PARTIAL - Input captured but not visible, got: '{response}'")
        else:
            error = result.get('error', 'Unknown error')
            console.print(f"✗ {method:12}: FAILED - {error}")
    
    console.print("\n" + "="*60)
    
    if working_methods:
        best_method = working_methods[0]
        console.print(f"RECOMMENDATION:")
        console.print(f"Set environment variable: INPUT_METHOD={best_method}")
        console.print(f"Example: INPUT_METHOD={best_method} research-ai research")
        
        # Show .env file update suggestion
        console.print(f"\nOr add to your .env file:")
        console.print(f"INPUT_METHOD={best_method}")
    else:
        console.print(f"WARNING: No methods provided fully visible input!")
        console.print(f"Try updating your terminal or using a different terminal emulator.")
        console.print(f"Methods that captured input (even if not visible) can still work:")
        
        partial_methods = [m for m, r in results.items() 
                          if r['status'] == 'success' and r.get('response')]
        if partial_methods:
            console.print(f"Try: INPUT_METHOD={partial_methods[0]}")
    
    # Show current environment info
    console.print(f"\nEnvironment Info:")
    console.print(f"Terminal: {os.getenv('TERM', 'unknown')}")
    console.print(f"TMUX: {'yes' if os.getenv('TMUX') else 'no'}")
    console.print(f"TTY: {'yes' if sys.stdin.isatty() else 'no'}")
    console.print(f"Platform: {sys.platform}")
    
    current_method = os.getenv('INPUT_METHOD', 'auto-detect')
    console.print(f"Current INPUT_METHOD: {current_method}")


def main():
    """Main entry point for CLI"""
    try:
        cli()
    except Exception as e:
        console.print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()