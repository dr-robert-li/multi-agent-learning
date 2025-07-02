"""
CLI Entry Point and Command Interface
"""

import asyncio
import click
import sys
import os
import logging
import structlog
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
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

console = Console()


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
                console.print(f"[red]Error:[/red] Session '{session_id}' not found")
                return
            console.print(f"[green]Resuming session:[/green] {session.name}")
            console.print(f"[cyan]Topic:[/cyan] {session.topic}")
        else:
            # Check for existing sessions and offer to resume
            recent_sessions = session_manager.list_sessions()[:5]  # Show 5 most recent
            
            if recent_sessions and interactive:
                console.print("\n[bold]Recent Sessions:[/bold]")
                for i, sess in enumerate(recent_sessions, 1):
                    status_color = {"active": "green", "completed": "blue", "paused": "yellow", "error": "red"}.get(sess.get('status', 'unknown'), "white")
                    console.print(f"  {i}. [{status_color}]{sess['name']}[/{status_color}] - {sess['topic']} ({sess.get('last_accessed_days', 0)} days ago)")
                
                console.print("  n. Start new session")
                
                temp_console = Console(force_terminal=True, legacy_windows=True)
                choice = Prompt.ask("Choose session to resume or 'n' for new", default="n", console=temp_console)
                
                if choice.isdigit() and 1 <= int(choice) <= len(recent_sessions):
                    resumed_session_id = recent_sessions[int(choice) - 1]['session_id']
                    session = session_manager.load_session(resumed_session_id)
                    if session:
                        console.print(f"[green]Resuming session:[/green] {session.name}")
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
                console.print("[red]Error:[/red] Topic required for batch mode")
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
            console.print(f"\n[green]Research completed successfully![/green]")
            if 'output_path' in result:
                console.print(f"Report saved to: {result['output_path']}")
            if 'session_id' in result:
                console.print(f"Session ID: {result['session_id']}")
    
    # Run the async function
    asyncio.run(run_research())


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status and configuration"""
    from ..config.models import ModelConfig
    
    console.print("\n[bold blue]System Status[/bold blue]\n")
    
    try:
        model_config = ModelConfig()
        info = model_config.get_model_info()
        
        console.print(f"[cyan]Privacy Mode:[/cyan] {'Enabled' if info['privacy_mode'] else 'Disabled'}")
        console.print(f"[cyan]CLI Mode:[/cyan] {'Enabled' if info['cli_mode'] else 'Disabled'}")
        console.print("\n[bold]Configured Models:[/bold]")
        
        for role, model in info['models'].items():
            console.print(f"  • {role.capitalize()}: {model}")
        
    except Exception as e:
        console.print(f"[red]Error checking status:[/red] {str(e)}")
        console.print("\n[yellow]Make sure you have configured your environment variables.[/yellow]")
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
            temp_console = Console(force_terminal=True, legacy_windows=True)
            source = Prompt.ask("Enter file path or URL", console=temp_console)
        
        metadata = {}
        if description:
            metadata['description'] = description
        if tags:
            metadata['tags'] = [tag.strip() for tag in tags.split(',')]
        
        try:
            console.print(f"[cyan]Processing source:[/cyan] {source}")
            source_id = await source_manager.add_source(
                source=source,
                source_type=source_type or 'auto',
                metadata=metadata
            )
            console.print(f"[green]✓ Successfully added source with ID:[/green] {source_id}")
            
            # Show summary
            source_data = source_manager.get_source(source_id)
            ingested_data = source_data['ingested_data']
            
            if source_data['source_type'] == 'document':
                console.print(f"Document: {ingested_data.get('word_count', 0):,} words")
            else:
                console.print(f"Data: {ingested_data.get('metadata', {}).get('row_count', 0):,} rows")
                
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")
    
    asyncio.run(run_add_source())


@cli.command()
@click.option('--type', 'source_type', help='Filter by source type (document/data)')
def list_sources(source_type):
    """List all sources in your research project"""
    from ..tools.source_manager import SourceManager
    
    source_manager = SourceManager()
    sources = source_manager.list_sources(source_type)
    
    if not sources:
        console.print("[yellow]No sources found.[/yellow]")
        return
    
    table = Table(title="Your Research Sources")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Source", style="white")
    table.add_column("Description", style="blue")
    table.add_column("Added", style="dim")
    
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
    
    console.print(table)
    
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
        console.print(f"[green]✓ Removed source:[/green] {source_id}")
    else:
        console.print(f"[red]Source not found:[/red] {source_id}")


@cli.command()
@click.argument('query')
@click.option('--type', 'source_type', help='Filter by source type (document/data)')
def search_sources(query, source_type):
    """Search your sources by content or metadata"""
    from ..tools.source_manager import SourceManager
    
    source_manager = SourceManager()
    results = source_manager.search_sources(query, source_type)
    
    if not results:
        console.print(f"[yellow]No sources found matching '[bold]{query}[/bold]'[/yellow]")
        return
    
    console.print(f"[green]Found {len(results)} sources matching '[bold]{query}[/bold]':[/green]\n")
    
    for result in results[:10]:  # Limit to top 10
        source_data = result['source_data']
        score = result['relevance_score']
        
        console.print(f"[cyan]ID:[/cyan] {source_data['id']}")
        console.print(f"[cyan]Source:[/cyan] {source_data['original_source']}")
        console.print(f"[cyan]Relevance:[/cyan] {score}/10")
        console.print(f"[cyan]Type:[/cyan] {source_data['source_type']}")
        
        description = source_data.get('user_metadata', {}).get('description')
        if description:
            console.print(f"[cyan]Description:[/cyan] {description}")
        
        console.print("---")


@cli.command()
def sources_summary():
    """Show summary of all sources in your research project"""
    from ..tools.source_manager import SourceManager
    
    source_manager = SourceManager()
    summary = source_manager.get_sources_summary()
    
    console.print("\n[bold blue]Sources Summary[/bold blue]\n")
    
    # Overview
    console.print(f"[cyan]Total Sources:[/cyan] {summary['total_sources']}")
    console.print(f"[cyan]Documents:[/cyan] {summary['documents']['count']} ({summary['documents']['total_words']:,} words)")
    console.print(f"[cyan]Data Sources:[/cyan] {summary['data_sources']['count']} ({summary['data_sources']['total_rows']:,} rows)")
    
    # Recent additions
    if summary['recent_additions']:
        console.print("\n[bold]Recent Additions:[/bold]")
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
        console.print("[yellow]No sessions found.[/yellow]")
        return
    
    table = Table(title="Research Sessions")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Topic", style="green")
    table.add_column("Status", style="blue")
    table.add_column("Created", style="dim")
    table.add_column("Last Access", style="dim")
    
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
            f"[{status_color}]{session.get('status', 'unknown')}[/{status_color}]",
            session.get('created_at', '')[:10],
            f"{session.get('last_accessed_days', 0)} days ago"
        )
    
    console.print(table)
    
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
        console.print(f"[red]Session not found:[/red] {session_id}")
        return
    
    # Basic info
    console.print(f"\n[bold blue]Session Details[/bold blue]")
    console.print(f"[cyan]ID:[/cyan] {session.session_id}")
    console.print(f"[cyan]Name:[/cyan] {session.name}")
    console.print(f"[cyan]Topic:[/cyan] {session.topic}")
    console.print(f"[cyan]Status:[/cyan] {session.status}")
    console.print(f"[cyan]Created:[/cyan] {session.created_at}")
    console.print(f"[cyan]Last Accessed:[/cyan] {session.last_accessed}")
    console.print(f"[cyan]Age:[/cyan] {session.get_age_days()} days")
    
    # Progress info
    if session.progress:
        console.print(f"\n[bold]Progress:[/bold]")
        console.print(f"[cyan]Current Phase:[/cyan] {session.progress.get('current_phase', 'Unknown')}")
        console.print(f"[cyan]Completion:[/cyan] {session.progress.get('completion_percentage', 0)}%")
        
        phases = session.progress.get('phases_completed', [])
        if phases:
            console.print(f"[cyan]Completed Phases:[/cyan] {', '.join(phases)}")
    
    # Sources info
    if session.source_ids:
        console.print(f"\n[bold]Sources:[/bold] {len(session.source_ids)} items")
    
    # Agent outputs
    if session.agent_outputs:
        console.print(f"\n[bold]Agent Outputs:[/bold] {len(session.agent_outputs)} agents completed")
    
    # Conversation
    if session.conversation_history:
        console.print(f"\n[bold]Conversation:[/bold] {len(session.conversation_history)} turns")


@cli.command()
@click.argument('session_id')
@click.confirmation_option(prompt='Are you sure you want to delete this session?')
def delete_session(session_id):
    """Delete a research session permanently"""
    from ..utils.session_manager import SessionManager
    
    session_manager = SessionManager()
    
    if session_manager.delete_session(session_id):
        console.print(f"[green]✓ Deleted session:[/green] {session_id}")
    else:
        console.print(f"[red]Failed to delete session:[/red] {session_id}")


@cli.command()
@click.argument('query')
def search_sessions(query):
    """Search sessions by name, topic, or content"""
    from ..utils.session_manager import SessionManager
    
    session_manager = SessionManager()
    results = session_manager.search_sessions(query)
    
    if not results:
        console.print(f"[yellow]No sessions found matching '[bold]{query}[/bold]'[/yellow]")
        return
    
    console.print(f"[green]Found {len(results)} sessions matching '[bold]{query}[/bold]':[/green]\n")
    
    for result in results[:10]:  # Limit to top 10
        console.print(f"[cyan]ID:[/cyan] {result['session_id'][:12]}...")
        console.print(f"[cyan]Name:[/cyan] {result.get('name', 'Unnamed')}")
        console.print(f"[cyan]Topic:[/cyan] {result.get('topic', 'No topic')}")
        console.print(f"[cyan]Relevance:[/cyan] {result.get('relevance_score', 0)}/10")
        console.print("---")


@cli.command()
@click.argument('session_id')
@click.argument('export_path')
def export_session(session_id, export_path):
    """Export a session to a file"""
    from ..utils.session_manager import SessionManager
    
    session_manager = SessionManager()
    
    if session_manager.export_session(session_id, export_path):
        console.print(f"[green]✓ Exported session to:[/green] {export_path}")
    else:
        console.print(f"[red]Failed to export session:[/red] {session_id}")


@cli.command()
@click.argument('import_path')
def import_session(import_path):
    """Import a session from a file"""
    from ..utils.session_manager import SessionManager
    
    session_manager = SessionManager()
    new_session_id = session_manager.import_session(import_path)
    
    if new_session_id:
        console.print(f"[green]✓ Imported session with ID:[/green] {new_session_id}")
    else:
        console.print(f"[red]Failed to import session from:[/red] {import_path}")


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
        console.print(f"[green]✓ Cleaned up {deleted_count} old sessions[/green]")
    else:
        console.print("[yellow]No sessions needed cleanup[/yellow]")


@cli.command()
def sessions_stats():
    """Show session statistics and usage"""
    from ..utils.session_manager import SessionManager
    
    session_manager = SessionManager()
    stats = session_manager.get_session_stats()
    
    console.print("\n[bold blue]Session Statistics[/bold blue]\n")
    console.print(f"[cyan]Total Sessions:[/cyan] {stats['total_sessions']}")
    console.print(f"[cyan]Active Sessions:[/cyan] {stats['active_sessions']}")
    console.print(f"[cyan]Completed Sessions:[/cyan] {stats['completed_sessions']}")
    console.print(f"[cyan]Paused Sessions:[/cyan] {stats.get('paused_sessions', 0)}")
    console.print(f"[cyan]Error Sessions:[/cyan] {stats.get('error_sessions', 0)}")
    
    if stats['total_sessions'] > 0:
        console.print(f"[cyan]Average Age:[/cyan] {stats.get('average_age_days', 0):.1f} days")
        console.print(f"[cyan]Oldest Session:[/cyan] {stats.get('oldest_session_days', 0)} days")
        console.print(f"[cyan]Most Recent Access:[/cyan] {stats.get('most_recent_access_days', 0)} days ago")


@cli.command()
def version():
    """Show version information"""
    from .. import __version__
    console.print(f"HierarchicalResearchAI v{__version__}")


def main():
    """Main entry point for CLI"""
    try:
        cli()
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()