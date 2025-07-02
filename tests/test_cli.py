"""
Tests for CLI functionality
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from rich.console import Console
from io import StringIO

from src.cli.conversation_controller import ConversationController
from src.cli.commands import CLICommands


class TestConversationController:
    """Test ConversationController functionality"""
    
    def test_conversation_controller_initialization(self, research_system):
        """Test ConversationController initialization"""
        controller = ConversationController(research_system)
        
        assert controller.research_system == research_system
        assert hasattr(controller, 'console')
        assert hasattr(controller, 'state_manager')
    
    @pytest.mark.asyncio
    async def test_start_interactive_session(self, research_system):
        """Test starting an interactive session"""
        controller = ConversationController(research_system)
        
        # Mock user input and system responses
        with patch('rich.prompt.Prompt.ask') as mock_prompt, \
             patch.object(controller, '_handle_user_input') as mock_handle:
            
            mock_prompt.side_effect = ["test topic", "exit"]
            mock_handle.return_value = {"action": "exit"}
            
            result = await controller.start_interactive_session(
                initial_topic="AI in Healthcare"
            )
            
            assert result is not None
    
    def test_display_welcome_message(self, research_system):
        """Test welcome message display"""
        controller = ConversationController(research_system)
        
        # Capture console output
        string_io = StringIO()
        controller.console = Console(file=string_io, width=80)
        
        controller._display_welcome_message()
        
        output = string_io.getvalue()
        assert "HierarchicalResearchAI" in output
        assert "multi-agent research system" in output
    
    def test_display_session_selection(self, research_system):
        """Test session selection display"""
        controller = ConversationController(research_system)
        
        # Mock session manager
        controller.session_manager.list_sessions = MagicMock(return_value=[
            {
                "session_id": "123",
                "name": "Test Session",
                "topic": "AI Research",
                "created_at": "2024-01-01T12:00:00",
                "status": "active"
            }
        ])
        
        string_io = StringIO()
        controller.console = Console(file=string_io, width=80)
        
        controller._display_session_selection()
        
        output = string_io.getvalue()
        assert "Recent Sessions" in output
        assert "Test Session" in output
    
    @pytest.mark.asyncio
    async def test_handle_research_command(self, research_system):
        """Test handling research command"""
        controller = ConversationController(research_system)
        
        # Mock research system methods
        research_system.start_project = MagicMock()
        research_system.generate_report = AsyncMock(return_value={
            "status": "completed",
            "output_path": "/test/report.md",
            "word_count": 25000
        })
        
        result = await controller._handle_research_command("AI in Healthcare")
        
        assert result["action"] == "research_completed"
        research_system.start_project.assert_called_once()


class TestCLICommands:
    """Test CLI command handlers"""
    
    def test_cli_commands_initialization(self, research_system):
        """Test CLICommands initialization"""
        commands = CLICommands(research_system)
        
        assert commands.research_system == research_system
        assert hasattr(commands, 'console')
    
    @pytest.mark.asyncio
    async def test_add_source_command(self, research_system, sample_pdf_file):
        """Test add-source command"""
        commands = CLICommands(research_system)
        
        # Mock toolkit
        with patch.object(commands.research_system.research_toolkit, 'add_source') as mock_add:
            mock_add.return_value = "src_123"
            
            result = await commands.add_source(
                source=sample_pdf_file,
                description="Test document",
                source_type="document"
            )
            
            assert result == "src_123"
            mock_add.assert_called_once()
    
    def test_list_sources_command(self, research_system):
        """Test list-sources command"""
        commands = CLICommands(research_system)
        
        # Mock toolkit
        commands.research_system.research_toolkit.source_manager.list_sources = MagicMock(
            return_value=[
                {
                    "source_id": "src_123",
                    "source_type": "document", 
                    "description": "Test document",
                    "created_at": "2024-01-01T12:00:00"
                }
            ]
        )
        
        string_io = StringIO()
        commands.console = Console(file=string_io, width=80)
        
        commands.list_sources()
        
        output = string_io.getvalue()
        assert "src_123" in output
        assert "Test document" in output
    
    def test_list_sessions_command(self, research_system):
        """Test sessions command"""
        commands = CLICommands(research_system)
        
        # Mock session manager
        commands.research_system.session_manager.list_sessions = MagicMock(
            return_value=[
                {
                    "session_id": "sess_123",
                    "name": "Test Session",
                    "topic": "AI Research",
                    "status": "active",
                    "created_at": "2024-01-01T12:00:00"
                }
            ]
        )
        
        string_io = StringIO()
        commands.console = Console(file=string_io, width=80)
        
        commands.list_sessions()
        
        output = string_io.getvalue()
        assert "sess_123" in output
        assert "Test Session" in output
    
    def test_show_status_command(self, research_system):
        """Test status command"""
        commands = CLICommands(research_system)
        
        # Mock system status
        research_system.get_system_status = MagicMock(return_value={
            "model_config": {"models": "configured"},
            "cost_summary": {"total_cost": 5.25},
            "session_stats": {"total_sessions": 3},
            "active_projects": 1
        })
        
        string_io = StringIO()
        commands.console = Console(file=string_io, width=80)
        
        commands.show_status()
        
        output = string_io.getvalue()
        assert "System Status" in output
        assert "$5.25" in output
        assert "3" in output  # session count
    
    @pytest.mark.asyncio
    async def test_research_command_with_topic(self, research_system):
        """Test research command with topic"""
        commands = CLICommands(research_system)
        
        # Mock research system
        research_system.start_project = MagicMock()
        research_system.generate_report = AsyncMock(return_value={
            "status": "completed",
            "output_path": "/test/report.md",
            "word_count": 25000
        })
        
        await commands.research(topic="AI in Healthcare")
        
        research_system.start_project.assert_called_once()
        research_system.generate_report.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_research_command_resume_session(self, research_system):
        """Test research command resuming session"""
        commands = CLICommands(research_system)
        
        # Mock research system
        research_system.resume_research = AsyncMock(return_value={
            "status": "completed",
            "output_path": "/test/report.md"
        })
        
        await commands.research(session_id="sess_123")
        
        research_system.resume_research.assert_called_once_with("sess_123")


class TestCLIStateManager:
    """Test CLI state management"""
    
    def test_state_manager_initialization(self, research_system):
        """Test state manager initialization"""
        controller = ConversationController(research_system)
        
        assert hasattr(controller, 'state_manager')
        assert controller.state_manager.current_phase == "welcome"
    
    def test_state_transitions(self, research_system):
        """Test state transitions"""
        controller = ConversationController(research_system)
        
        # Test state transitions
        controller.state_manager.set_phase("session_selection")
        assert controller.state_manager.current_phase == "session_selection"
        
        controller.state_manager.set_phase("research_active")
        assert controller.state_manager.current_phase == "research_active"
    
    def test_state_context_management(self, research_system):
        """Test context management in states"""
        controller = ConversationController(research_system)
        
        # Set context
        controller.state_manager.set_context("research_topic", "AI in Healthcare")
        controller.state_manager.set_context("requirements", {"target_length": 25000})
        
        # Get context
        topic = controller.state_manager.get_context("research_topic")
        requirements = controller.state_manager.get_context("requirements")
        
        assert topic == "AI in Healthcare"
        assert requirements["target_length"] == 25000


class TestCLIIntegration:
    """Test CLI integration with research system"""
    
    @pytest.mark.asyncio
    async def test_full_cli_workflow(self, research_system, temp_workspace):
        """Test full CLI workflow"""
        controller = ConversationController(research_system)
        
        # Mock all interactions
        with patch('rich.prompt.Prompt.ask') as mock_prompt, \
             patch('rich.prompt.Confirm.ask') as mock_confirm:
            
            # Simulate user interactions
            mock_prompt.side_effect = [
                "AI in Healthcare",  # topic
                "25000",  # target length
                "APA",  # citation style
                "exit"  # exit command
            ]
            mock_confirm.return_value = True
            
            # Mock research system
            research_system.start_project = MagicMock()
            research_system.generate_report = AsyncMock(return_value={
                "status": "completed",
                "output_path": "/test/report.md"
            })
            
            result = await controller.start_interactive_session()
            
            assert result is not None
    
    def test_error_handling_in_cli(self, research_system):
        """Test error handling in CLI"""
        controller = ConversationController(research_system)
        
        # Mock an error in research system
        research_system.get_system_status = MagicMock(
            side_effect=Exception("System error")
        )
        
        commands = CLICommands(research_system)
        
        # Should handle error gracefully
        string_io = StringIO()
        commands.console = Console(file=string_io, width=80)
        
        commands.show_status()
        
        output = string_io.getvalue()
        assert "Error" in output
    
    def test_progress_display(self, research_system):
        """Test progress display functionality"""
        controller = ConversationController(research_system)
        
        string_io = StringIO()
        controller.console = Console(file=string_io, width=80)
        
        # Test progress callback
        controller._progress_callback("research_planning", 25)
        
        # Should not raise errors
        assert True  # If we get here, no exceptions were raised