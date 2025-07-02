"""
Tests for main entry points and integration
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from src.cli.interface import main as main_function
from src.workflows.research_workflow import HierarchicalResearchSystem


class TestMainFunction:
    """Test main function and entry points"""
    
    @pytest.mark.asyncio
    async def test_main_function_basic(self):
        """Test basic main function execution"""
        # Mock the research system
        with patch('src.cli.interface.HierarchicalResearchSystem') as mock_system_class:
            mock_system = MagicMock()
            mock_system.interactive_research = AsyncMock(return_value={
                "status": "completed",
                "output_path": "/test/report.md"
            })
            mock_system_class.return_value = mock_system
            
            # Mock CLI argument parsing
            with patch('sys.argv', ['main.py']):
                await main_function()
            
            mock_system_class.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_function_with_topic(self):
        """Test main function with initial topic"""
        with patch('src.cli.interface.HierarchicalResearchSystem') as mock_system_class:
            mock_system = MagicMock()
            mock_system.interactive_research = AsyncMock(return_value={
                "status": "completed"
            })
            mock_system_class.return_value = mock_system
            
            # Simulate command line arguments
            with patch('sys.argv', ['main.py', '--topic', 'AI in Healthcare']):
                await main_function()
            
            # Should have called interactive_research with topic
            mock_system.interactive_research.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_function_privacy_mode(self):
        """Test main function with privacy mode"""
        with patch('src.cli.interface.HierarchicalResearchSystem') as mock_system_class:
            mock_system = MagicMock()
            mock_system.interactive_research = AsyncMock(return_value={"status": "completed"})
            mock_system_class.return_value = mock_system
            
            with patch('sys.argv', ['main.py', '--privacy-mode']):
                await main_function()
            
            # Should have initialized with privacy mode
            mock_system_class.assert_called_once()
            args, kwargs = mock_system_class.call_args
            assert kwargs.get('privacy_mode') == True
    
    def test_main_function_error_handling(self):
        """Test main function error handling"""
        with patch('src.cli.interface.HierarchicalResearchSystem') as mock_system_class:
            mock_system_class.side_effect = Exception("Initialization failed")
            
            # Should handle the error gracefully
            with pytest.raises(Exception):
                asyncio.run(main_function())


class TestSystemIntegration:
    """Test system-wide integration"""
    
    @pytest.mark.asyncio
    async def test_full_system_initialization(self, temp_workspace):
        """Test full system initialization"""
        with patch.dict('os.environ', {
            'ANTHROPIC_API_KEY': 'test_key',
            'PERPLEXITY_API_KEY': 'test_key',
            'PRIVACY_MODE': 'true'
        }):
            system = HierarchicalResearchSystem(
                cli_mode=True,
                privacy_mode=True,
                workspace_dir=temp_workspace
            )
            
            assert system.cli_mode == True
            assert system.privacy_mode == True
            assert system.workspace_dir == temp_workspace
            assert hasattr(system, 'cli_controller')
    
    @pytest.mark.asyncio
    async def test_system_components_integration(self, temp_workspace):
        """Test that all system components work together"""
        system = HierarchicalResearchSystem(
            cli_mode=False,
            privacy_mode=True,
            workspace_dir=temp_workspace
        )
        
        # Check that all components are properly initialized
        assert hasattr(system, 'model_config')
        assert hasattr(system, 'cost_tracker')
        assert hasattr(system, 'session_manager')
        assert hasattr(system, 'memory_manager')
        assert hasattr(system, 'research_toolkit')
        assert hasattr(system, 'supervisor')
        assert hasattr(system, 'report_generator')
        
        # Check that components can interact
        status = system.get_system_status()
        assert isinstance(status, dict)
        assert 'model_config' in status
        assert 'cost_summary' in status
    
    @pytest.mark.asyncio
    async def test_error_propagation(self, temp_workspace):
        """Test error propagation through the system"""
        system = HierarchicalResearchSystem(workspace_dir=temp_workspace)
        
        # Mock a failing component
        system.supervisor.execute_workflow = AsyncMock(
            side_effect=Exception("Workflow failed")
        )
        
        project = system.start_project(
            topic="Test Topic",
            target_length=25000
        )
        
        result = await system.generate_report(project.id)
        
        assert result["status"] == "failed"
        assert "error" in result
    
    def test_system_configuration_validation(self):
        """Test system configuration validation"""
        # Test with missing environment variables
        with patch.dict('os.environ', {}, clear=True):
            system = HierarchicalResearchSystem()
            
            # Should still initialize but in privacy mode
            assert system.privacy_mode == True
        
        # Test with valid configuration
        with patch.dict('os.environ', {
            'ANTHROPIC_API_KEY': 'test_key',
            'PRIVACY_MODE': 'false'
        }):
            system = HierarchicalResearchSystem()
            
            # Should respect environment settings
            assert system.privacy_mode == False


class TestCLIIntegration:
    """Test CLI integration with main system"""
    
    @pytest.mark.asyncio
    async def test_cli_startup_flow(self, temp_workspace):
        """Test CLI startup flow"""
        system = HierarchicalResearchSystem(
            cli_mode=True,
            workspace_dir=temp_workspace
        )
        
        # Mock CLI interactions
        with patch.object(system.cli_controller, 'start_interactive_session') as mock_start:
            mock_start.return_value = {"status": "completed"}
            
            result = await system.interactive_research()
            
            assert result["status"] == "completed"
            mock_start.assert_called_once()
    
    def test_cli_command_registration(self, temp_workspace):
        """Test that CLI commands are properly registered"""
        system = HierarchicalResearchSystem(
            cli_mode=True,
            workspace_dir=temp_workspace
        )
        
        assert hasattr(system, 'cli_controller')
        assert hasattr(system.cli_controller, 'console')
        assert hasattr(system.cli_controller, 'state_manager')
    
    @pytest.mark.asyncio
    async def test_session_management_integration(self, temp_workspace):
        """Test session management integration"""
        system = HierarchicalResearchSystem(
            cli_mode=True,
            workspace_dir=temp_workspace
        )
        
        # Create a session
        session = system.session_manager.create_session(
            name="Test Integration Session",
            topic="Test Topic",
            requirements={"target_length": 25000}
        )
        
        # Verify integration with research system
        system.current_session = session
        
        assert system.current_session.name == "Test Integration Session"
        assert system.current_session.topic == "Test Topic"


class TestEnvironmentHandling:
    """Test environment variable handling"""
    
    def test_development_environment(self):
        """Test development environment setup"""
        with patch.dict('os.environ', {
            'ENVIRONMENT': 'development',
            'DEBUG': 'true',
            'ANTHROPIC_API_KEY': 'test_key'
        }):
            system = HierarchicalResearchSystem()
            
            # Should handle development settings
            assert system is not None
    
    def test_production_environment(self):
        """Test production environment setup"""
        with patch.dict('os.environ', {
            'ENVIRONMENT': 'production',
            'DEBUG': 'false',
            'ANTHROPIC_API_KEY': 'prod_key',
            'PRIVACY_MODE': 'false'
        }):
            system = HierarchicalResearchSystem()
            
            # Should handle production settings
            assert system.privacy_mode == False
    
    def test_missing_environment_variables(self):
        """Test handling of missing environment variables"""
        with patch.dict('os.environ', {}, clear=True):
            # Should not raise an exception
            system = HierarchicalResearchSystem()
            
            # Should default to safe settings
            assert system.privacy_mode == True
    
    def test_invalid_environment_variables(self):
        """Test handling of invalid environment variable values"""
        with patch.dict('os.environ', {
            'PRIVACY_MODE': 'invalid_value',
            'DEBUG': 'not_a_boolean'
        }):
            # Should handle gracefully
            system = HierarchicalResearchSystem()
            
            # Should use safe defaults
            assert isinstance(system.privacy_mode, bool)


class TestPerformanceAndReliability:
    """Test performance and reliability aspects"""
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, temp_workspace):
        """Test system handling of concurrent operations"""
        system = HierarchicalResearchSystem(workspace_dir=temp_workspace)
        
        # Create multiple projects concurrently
        projects = []
        for i in range(3):
            project = system.start_project(
                topic=f"Test Topic {i}",
                target_length=1000  # Small for testing
            )
            projects.append(project)
        
        assert len(system.projects) == 3
        assert all(p.topic.startswith("Test Topic") for p in projects)
    
    def test_memory_usage(self, temp_workspace):
        """Test memory usage with large configurations"""
        system = HierarchicalResearchSystem(workspace_dir=temp_workspace)
        
        # Create many projects to test memory handling
        for i in range(10):
            project = system.start_project(
                topic=f"Memory Test Topic {i}",
                target_length=1000
            )
            # Basic check that system still functions
            assert project.id in system.projects
        
        # System should still be responsive
        status = system.get_system_status()
        assert status is not None
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, temp_workspace):
        """Test system recovery from errors"""
        system = HierarchicalResearchSystem(workspace_dir=temp_workspace)
        
        # Create a project that will fail
        project = system.start_project(
            topic="Error Recovery Test",
            target_length=1000
        )
        
        # Mock a failure
        system.supervisor.execute_workflow = AsyncMock(
            side_effect=Exception("Simulated failure")
        )
        
        result = await system.generate_report(project.id)
        
        # System should handle the error and continue functioning
        assert result["status"] == "failed"
        
        # System should still be able to create new projects
        new_project = system.start_project(
            topic="Recovery Test",
            target_length=1000
        )
        
        assert new_project.id in system.projects