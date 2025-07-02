"""
Cost Tracking System

Monitors and tracks API usage costs across different models.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import structlog  # type: ignore

logger = structlog.get_logger()


@dataclass
class ModelCosts:
    """Cost structure for different models"""
    model_name: str
    input_cost_per_1m: float  # Cost per 1M input tokens
    output_cost_per_1m: float  # Cost per 1M output tokens
    search_cost_per_1k: Optional[float] = None  # Cost per 1K searches (Perplexity)
    reasoning_cost_per_1m: Optional[float] = None  # Cost per 1M reasoning tokens


class CostTracker:
    """Tracks API usage costs across all models"""
    
    # Model cost definitions
    MODEL_COSTS = {
        "sonar-deep-research": ModelCosts(
            model_name="sonar-deep-research",
            input_cost_per_1m=2.0,
            output_cost_per_1m=8.0,
            search_cost_per_1k=5.0,
            reasoning_cost_per_1m=3.0
        ),
        "sonar-pro": ModelCosts(
            model_name="sonar-pro",
            input_cost_per_1m=3.0,
            output_cost_per_1m=15.0,
            search_cost_per_1k=5.0
        ),
        "claude-3-5-sonnet-20241022": ModelCosts(
            model_name="claude-3-5-sonnet",
            input_cost_per_1m=3.0,
            output_cost_per_1m=15.0
        ),
        "claude-3-haiku-20240307": ModelCosts(
            model_name="claude-3-5-haiku",
            input_cost_per_1m=0.8,
            output_cost_per_1m=4.0
        ),
        "local": ModelCosts(
            model_name="local",
            input_cost_per_1m=0.0,
            output_cost_per_1m=0.0
        )
    }
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_COST_TRACKING", "true").lower() == "true"
        self.log_file = os.getenv("COST_TRACKING_LOG_FILE", "./logs/cost_tracking.json")
        self.budget_alert_threshold = float(os.getenv("BUDGET_ALERT_THRESHOLD", "50.00"))
        
        # Initialize for backward compatibility with tests
        self.session_costs = {}
        self.total_costs = {}
        
        # Internal tracking structure  
        self._session_data = {
            "start_time": datetime.now().isoformat(),
            "models": {},
            "total": 0.0
        }
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def track_usage(self, model_name: str, input_tokens: int, output_tokens: int, 
                   searches: int = 0, reasoning_tokens: int = 0):
        """Track usage for a specific model"""
        if not self.enabled:
            return
        
        # Map model names to cost keys
        cost_key = model_name
        if "gemma" in model_name.lower() or "llama" in model_name.lower():
            cost_key = "local"
        
        if cost_key not in self.MODEL_COSTS:
            logger.warning(f"Unknown model for cost tracking: {model_name}")
            return
        
        costs = self.MODEL_COSTS[cost_key]
        
        # Calculate costs
        input_cost = (input_tokens / 1_000_000) * costs.input_cost_per_1m
        output_cost = (output_tokens / 1_000_000) * costs.output_cost_per_1m
        search_cost = 0.0
        reasoning_cost = 0.0
        
        if costs.search_cost_per_1k and searches > 0:
            search_cost = (searches / 1000) * costs.search_cost_per_1k
        
        if costs.reasoning_cost_per_1m and reasoning_tokens > 0:
            reasoning_cost = (reasoning_tokens / 1_000_000) * costs.reasoning_cost_per_1m
        
        total_cost = input_cost + output_cost + search_cost + reasoning_cost
        
        # Update session costs
        if model_name not in self._session_data["models"]:
            self._session_data["models"][model_name] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "searches": 0,
                "reasoning_tokens": 0,
                "cost": 0.0
            }
        
        model_stats = self._session_data["models"][model_name]
        model_stats["input_tokens"] += input_tokens
        model_stats["output_tokens"] += output_tokens
        model_stats["searches"] += searches
        model_stats["reasoning_tokens"] += reasoning_tokens
        model_stats["cost"] += total_cost
        
        self._session_data["total"] += total_cost
        
        # Check budget alert
        if self._session_data["total"] >= self.budget_alert_threshold:
            logger.warning(
                "Budget alert threshold exceeded",
                total_cost=self._session_data["total"],
                threshold=self.budget_alert_threshold
            )
        
        # Log to file
        self._log_to_file()
    
    def track_api_call(self, provider: str, model: str, input_tokens: int, 
                      output_tokens: int, cost: float):
        """Track API call (backward compatibility method)"""
        if not self.enabled:
            return
            
        # Update session costs for test compatibility
        if provider not in self.session_costs:
            self.session_costs[provider] = {
                "total_cost": 0.0,
                "total_calls": 0,
                "models": {}
            }
        
        provider_stats = self.session_costs[provider]
        provider_stats["total_cost"] += cost
        provider_stats["total_calls"] += 1
        
        if model not in provider_stats["models"]:
            provider_stats["models"][model] = {
                "cost": 0.0,
                "calls": 0,
                "input_tokens": 0,
                "output_tokens": 0
            }
        
        model_stats = provider_stats["models"][model]
        model_stats["cost"] += cost
        model_stats["calls"] += 1
        model_stats["input_tokens"] += input_tokens
        model_stats["output_tokens"] += output_tokens
    
    def _log_to_file(self):
        """Log current session costs to file"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self._session_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write cost tracking log: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session costs"""
        summary = {
            "total_cost": self._session_data["total"],
            "duration": str(datetime.now() - datetime.fromisoformat(self._session_data["start_time"])),
            "models": {}
        }
        
        for model, stats in self._session_data["models"].items():
            summary["models"][model] = {
                "cost": stats["cost"],
                "usage": {
                    "input_tokens": stats["input_tokens"],
                    "output_tokens": stats["output_tokens"],
                    "searches": stats["searches"],
                    "reasoning_tokens": stats["reasoning_tokens"]
                }
            }
        
        return summary
    
    def estimate_cost(self, model_name: str, estimated_input_tokens: int, 
                     estimated_output_tokens: int) -> float:
        """Estimate cost for a planned operation"""
        cost_key = model_name
        if "gemma" in model_name.lower() or "llama" in model_name.lower():
            cost_key = "local"
        
        if cost_key not in self.MODEL_COSTS:
            return 0.0
        
        costs = self.MODEL_COSTS[cost_key]
        
        input_cost = (estimated_input_tokens / 1_000_000) * costs.input_cost_per_1m
        output_cost = (estimated_output_tokens / 1_000_000) * costs.output_cost_per_1m
        
        return input_cost + output_cost
    
    def get_provider_costs(self, provider: str) -> Dict[str, Any]:
        """Get costs for a specific provider"""
        if provider not in self.session_costs:
            return {"total_cost": 0.0, "total_calls": 0, "models": {}}
        return self.session_costs[provider]
    
    def reset_session_costs(self):
        """Reset session costs (alias for backward compatibility)"""
        self.reset_session()
    
    def reset_session(self):
        """Reset session costs"""
        self.session_costs = {}
        self.total_costs = {}
        self._session_data = {
            "start_time": datetime.now().isoformat(),
            "models": {},
            "total": 0.0
        }