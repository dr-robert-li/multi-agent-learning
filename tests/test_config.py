"""
Tests for configuration systems
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from src.config.models import ModelConfig
from src.config.costs import CostTracker


class TestModelConfig:
    """Test ModelConfig functionality"""
    
    def test_model_config_initialization(self):
        """Test ModelConfig initialization"""
        with patch.dict(os.environ, {
            'PERPLEXITY_API_KEY': 'test_perplexity_key',
            'ANTHROPIC_API_KEY': 'test_anthropic_key',
            'PRIVACY_MODE': 'false'
        }):
            config = ModelConfig()
            
            assert not config.privacy_mode
            assert hasattr(config, 'anthropic_models')
            assert hasattr(config, 'perplexity_models')
    
    def test_privacy_mode_enabled(self):
        """Test privacy mode configuration"""
        with patch.dict(os.environ, {
            'PRIVACY_MODE': 'true',
            'ANTHROPIC_API_KEY': 'test_key'
        }):
            config = ModelConfig()
            
            assert config.privacy_mode
    
    def test_get_research_model(self):
        """Test getting research model"""
        with patch.dict(os.environ, {
            'PERPLEXITY_API_KEY': 'test_key',
            'PRIVACY_MODE': 'false'
        }):
            config = ModelConfig()
            
            model = config.get_research_model()
            assert model is not None
    
    def test_get_analysis_model(self):
        """Test getting analysis model"""
        with patch.dict(os.environ, {
            'ANTHROPIC_API_KEY': 'test_key',
            'PRIVACY_MODE': 'false'
        }):
            config = ModelConfig()
            
            model = config.get_analysis_model()
            assert model is not None
    
    def test_get_routine_model(self):
        """Test getting routine model"""
        with patch.dict(os.environ, {
            'ANTHROPIC_API_KEY': 'test_key',
            'PRIVACY_MODE': 'false'
        }):
            config = ModelConfig()
            
            model = config.get_routine_model()
            assert model is not None
    
    def test_model_fallback_in_privacy_mode(self):
        """Test model fallback when privacy mode is enabled"""
        with patch.dict(os.environ, {
            'PRIVACY_MODE': 'true'
        }):
            config = ModelConfig()
            
            # Should fall back to local models
            research_model = config.get_research_model()
            analysis_model = config.get_analysis_model()
            
            assert research_model is not None
            assert analysis_model is not None
    
    def test_get_model_info(self):
        """Test getting model information"""
        with patch.dict(os.environ, {
            'ANTHROPIC_API_KEY': 'test_key',
            'PERPLEXITY_API_KEY': 'test_key',
            'PRIVACY_MODE': 'false'
        }):
            config = ModelConfig()
            
            info = config.get_model_info()
            
            assert isinstance(info, dict)
            assert 'available_models' in info
            assert 'privacy_mode' in info
            assert info['privacy_mode'] == False
    
    def test_missing_api_keys(self):
        """Test behavior when API keys are missing"""
        with patch.dict(os.environ, {}, clear=True):
            config = ModelConfig()
            
            # Should still initialize but with limited functionality
            assert config.privacy_mode  # Should default to privacy mode
    
    def test_custom_perplexity_model(self):
        """Test ChatPerplexity custom model implementation"""
        config = ModelConfig()
        
        # Test if custom Perplexity model is properly configured
        if hasattr(config, 'perplexity_models'):
            assert 'sonar-deep-research' in str(config.perplexity_models)


class TestCostTracker:
    """Test CostTracker functionality"""
    
    def test_cost_tracker_initialization(self):
        """Test CostTracker initialization"""
        tracker = CostTracker()
        
        assert hasattr(tracker, 'session_costs')
        assert hasattr(tracker, 'total_costs')
        assert tracker.session_costs == {}
        assert tracker.total_costs == {}
    
    def test_track_api_call(self):
        """Test tracking API calls"""
        tracker = CostTracker()
        
        tracker.track_api_call(
            provider="anthropic",
            model="claude-3-sonnet-20240229",
            input_tokens=100,
            output_tokens=50,
            cost=0.15
        )
        
        assert "anthropic" in tracker.session_costs
        assert tracker.session_costs["anthropic"]["total_cost"] == 0.15
        assert tracker.session_costs["anthropic"]["total_calls"] == 1
    
    def test_multiple_api_calls(self):
        """Test tracking multiple API calls"""
        tracker = CostTracker()
        
        # Track multiple calls
        tracker.track_api_call("anthropic", "claude-3-sonnet", 100, 50, 0.15)
        tracker.track_api_call("anthropic", "claude-3-sonnet", 200, 100, 0.30)
        tracker.track_api_call("perplexity", "sonar-deep-research", 150, 75, 0.20)
        
        # Check anthropic totals
        assert tracker.session_costs["anthropic"]["total_cost"] == 0.45
        assert tracker.session_costs["anthropic"]["total_calls"] == 2
        
        # Check perplexity totals
        assert tracker.session_costs["perplexity"]["total_cost"] == 0.20
        assert tracker.session_costs["perplexity"]["total_calls"] == 1
    
    def test_get_session_summary(self):
        """Test getting session summary"""
        tracker = CostTracker()
        
        tracker.track_api_call("anthropic", "claude-3-sonnet", 100, 50, 0.15)
        tracker.track_api_call("perplexity", "sonar-deep-research", 150, 75, 0.20)
        
        summary = tracker.get_session_summary()
        
        assert summary["total_cost"] == 0.35
        assert summary["total_calls"] == 2
        assert "providers" in summary
        assert len(summary["providers"]) == 2
    
    def test_get_provider_costs(self):
        """Test getting costs for specific provider"""
        tracker = CostTracker()
        
        tracker.track_api_call("anthropic", "claude-3-sonnet", 100, 50, 0.15)
        tracker.track_api_call("anthropic", "claude-3-haiku", 50, 25, 0.05)
        
        anthropic_costs = tracker.get_provider_costs("anthropic")
        
        assert anthropic_costs["total_cost"] == 0.20
        assert anthropic_costs["total_calls"] == 2
        assert len(anthropic_costs["models"]) == 2
    
    def test_reset_session_costs(self):
        """Test resetting session costs"""
        tracker = CostTracker()
        
        tracker.track_api_call("anthropic", "claude-3-sonnet", 100, 50, 0.15)
        
        assert tracker.session_costs["anthropic"]["total_cost"] == 0.15
        
        tracker.reset_session_costs()
        
        assert tracker.session_costs == {}
    
    def test_cost_tracking_with_zero_cost(self):
        """Test tracking calls with zero cost (e.g., local models)"""
        tracker = CostTracker()
        
        tracker.track_api_call("local", "gemma-3n", 100, 50, 0.0)
        
        assert tracker.session_costs["local"]["total_cost"] == 0.0
        assert tracker.session_costs["local"]["total_calls"] == 1
    
    def test_budget_checking(self):
        """Test budget checking functionality"""
        tracker = CostTracker()
        
        # Set budget limit
        budget_limit = 1.00
        
        tracker.track_api_call("anthropic", "claude-3-sonnet", 100, 50, 0.50)
        
        summary = tracker.get_session_summary()
        is_over_budget = summary["total_cost"] > budget_limit
        
        assert not is_over_budget
        
        # Add more expensive call
        tracker.track_api_call("anthropic", "claude-3-sonnet", 200, 100, 0.60)
        
        summary = tracker.get_session_summary()
        is_over_budget = summary["total_cost"] > budget_limit
        
        assert is_over_budget
    
    def test_model_usage_statistics(self):
        """Test model usage statistics"""
        tracker = CostTracker()
        
        # Track different models
        tracker.track_api_call("anthropic", "claude-3-sonnet", 100, 50, 0.15)
        tracker.track_api_call("anthropic", "claude-3-haiku", 200, 100, 0.05)
        tracker.track_api_call("perplexity", "sonar-deep-research", 150, 75, 0.20)
        
        summary = tracker.get_session_summary()
        
        # Check that all models are tracked
        model_names = []
        for provider_data in summary["providers"].values():
            model_names.extend(provider_data["models"].keys())
        
        assert "claude-3-sonnet" in model_names
        assert "claude-3-haiku" in model_names
        assert "sonar-deep-research" in model_names
    
    def test_token_usage_tracking(self):
        """Test token usage tracking"""
        tracker = CostTracker()
        
        tracker.track_api_call("anthropic", "claude-3-sonnet", 1000, 500, 0.50)
        tracker.track_api_call("anthropic", "claude-3-sonnet", 800, 400, 0.40)
        
        anthropic_costs = tracker.get_provider_costs("anthropic")
        sonnet_stats = anthropic_costs["models"]["claude-3-sonnet"]
        
        assert sonnet_stats["total_input_tokens"] == 1800
        assert sonnet_stats["total_output_tokens"] == 900
        assert sonnet_stats["total_cost"] == 0.90