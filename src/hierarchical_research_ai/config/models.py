"""
Model Configuration System

Manages multi-LLM integration with Perplexity, Anthropic, and Ollama models.
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_core.language_models import BaseChatModel
import httpx
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
import json
import tiktoken

load_dotenv()


class ChatPerplexity(BaseChatModel):
    """Custom Perplexity chat model implementation with cost tracking"""
    
    model: str
    api_key: str
    base_url: str = "https://api.perplexity.ai"
    temperature: float = 0.2
    max_tokens: int = 4000
    reasoning_effort: str = "medium"  # low, medium, high (for sonar-deep-research)
    cost_tracker: Optional[Any] = None
    tokenizer: Optional[Any] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set longer timeout for deep research models (15 minutes for deep research)
        timeout = 900.0 if 'large' in self.model or 'deep' in self.model else 30.0
        # Set client without triggering pydantic validation
        object.__setattr__(self, 'client', httpx.Client(
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=timeout
        ))
        
        # Initialize tokenizer for cost calculation
        try:
            object.__setattr__(self, 'tokenizer', tiktoken.get_encoding("cl100k_base"))
        except:
            object.__setattr__(self, 'tokenizer', None)
    
    def _generate(self, messages: list[BaseMessage], **kwargs) -> ChatResult:
        """Generate chat response from Perplexity API"""
        # Combine all messages into a single user message for Perplexity
        combined_content = ""
        for i, m in enumerate(messages):
            if i == 0 and hasattr(m, 'type') and m.type == 'system':
                # System message becomes instruction at the top
                combined_content += f"Instructions: {m.content}\n\n"
            else:
                # All other messages are treated as user content
                combined_content += f"{m.content}\n\n"
        
        formatted_messages = [
            {"role": "user", "content": combined_content.strip()}
        ]
        
        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            **kwargs
        }
        
        # Add reasoning_effort for sonar-deep-research model
        if self.model == "sonar-deep-research":
            payload["reasoning_effort"] = self.reasoning_effort
        
        response = self.client.post(
            f"{self.base_url}/chat/completions",
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Track costs if available
        self._track_usage(combined_content, content, result.get("usage", {}))
        
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=content))]
        )
    
    async def _agenerate(self, messages: list[BaseMessage], **kwargs) -> ChatResult:
        """Async generate chat response"""
        # Set longer timeout for deep research models (15 minutes for deep research)
        timeout = 900.0 if 'large' in self.model or 'deep' in self.model else 30.0
        
        async with httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=timeout
        ) as client:
            # Combine all messages into a single user message for Perplexity
            combined_content = ""
            for i, m in enumerate(messages):
                if i == 0 and hasattr(m, 'type') and m.type == 'system':
                    # System message becomes instruction at the top
                    combined_content += f"Instructions: {m.content}\n\n"
                else:
                    # All other messages are treated as user content
                    combined_content += f"{m.content}\n\n"
            
            formatted_messages = [
                {"role": "user", "content": combined_content.strip()}
            ]
            
            # Prepare request payload
            payload = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                **kwargs
            }
            
            # Add reasoning_effort for sonar-deep-research model
            if self.model == "sonar-deep-research":
                payload["reasoning_effort"] = self.reasoning_effort
            
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Track costs if available
            self._track_usage(combined_content, content, result.get("usage", {}))
            
            return ChatResult(
                generations=[ChatGeneration(message=AIMessage(content=content))]
            )
    
    def _track_usage(self, input_content: str, output_content: str, usage: Dict[str, Any]):
        """Track usage for cost calculation"""
        if not self.cost_tracker:
            return
            
        # Calculate tokens if not provided in usage
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        # If no usage info provided, estimate using tokenizer
        if not input_tokens and self.tokenizer:
            input_tokens = len(self.tokenizer.encode(input_content))
        if not output_tokens and self.tokenizer:
            output_tokens = len(self.tokenizer.encode(output_content))
        
        # Track searches (assume 1 search per API call for search models)
        searches = 1 if "sonar" in self.model else 0
        
        # Track reasoning tokens for deep research
        reasoning_tokens = usage.get("reasoning_tokens", 0)
        
        self.cost_tracker.track_usage(
            model_name=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            searches=searches,
            reasoning_tokens=reasoning_tokens
        )
    
    @property
    def _llm_type(self) -> str:
        return "perplexity"


class ChatAnthropicWithCosts(ChatAnthropic):
    """Anthropic model with cost tracking"""
    
    def __init__(self, cost_tracker=None, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, 'cost_tracker', cost_tracker)
        try:
            object.__setattr__(self, 'tokenizer', tiktoken.get_encoding("cl100k_base"))
        except:
            object.__setattr__(self, 'tokenizer', None)
    
    def _track_usage(self, input_content: str, output_content: str, usage: Dict[str, Any] = None):
        """Track usage for cost calculation"""
        if not self.cost_tracker:
            return
            
        # Estimate tokens using tokenizer
        input_tokens = 0
        output_tokens = 0
        
        if self.tokenizer:
            input_tokens = len(self.tokenizer.encode(input_content))
            output_tokens = len(self.tokenizer.encode(output_content))
        
        self.cost_tracker.track_usage(
            model_name=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            searches=0,
            reasoning_tokens=0
        )
    
    async def _agenerate(self, messages, **kwargs):
        """Override to add cost tracking"""
        # Get input content for tracking
        input_content = "\n".join([m.content for m in messages])
        
        # Call parent method
        result = await super()._agenerate(messages, **kwargs)
        
        # Extract output content and track
        output_content = result.generations[0].message.content
        self._track_usage(input_content, output_content)
        
        return result


class ModelConfig:
    """Centralized model configuration and management"""
    
    def __init__(self):
        self.privacy_mode = os.getenv("PRIVACY_MODE", "false").lower() == "true"
        self.cli_mode = os.getenv("CLI_MODE", "false").lower() == "true"
        
        # Initialize cost tracker
        from .costs import CostTracker
        self.cost_tracker = CostTracker()
        
        # Initialize models
        self._init_perplexity_models()
        self._init_anthropic_models()
        self._init_local_models()
    
    def _init_perplexity_models(self):
        """Initialize Perplexity models"""
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key and not self.privacy_mode:
            raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
        
        # Initialize perplexity_models dict
        self.perplexity_models = {}
        
        if api_key:
            # Deep research model - using sonar-deep-research (current model per Perplexity docs)
            # Note: llama-3.1-sonar-large-128k-online has been deprecated
            self.deep_research_model = ChatPerplexity(
                model="sonar-deep-research",
                api_key=api_key,
                base_url=os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai"),
                temperature=0.1,
                max_tokens=4000,  # Increased from 500 for comprehensive research output
                reasoning_effort="medium",  # Balanced approach for research quality
                cost_tracker=self.cost_tracker
            )
            
            # Fast search model - sonar-pro (8k output limit per documentation)
            self.fast_search_model = ChatPerplexity(
                model="sonar-pro",
                api_key=api_key,
                base_url=os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai"),
                temperature=0.2,
                max_tokens=8000,
                cost_tracker=self.cost_tracker
            )
            
            # Add to models dict
            self.perplexity_models = {
                "deep_research": self.deep_research_model,
                "fast_search": self.fast_search_model
            }
    
    def _init_anthropic_models(self):
        """Initialize Anthropic models"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key and not self.privacy_mode:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        # Initialize anthropic_models dict
        self.anthropic_models = {}
        
        if api_key:
            # Analysis model - Claude Sonnet 4
            self.analysis_model = ChatAnthropicWithCosts(
                model="claude-3-5-sonnet-20241022",  # Using available model
                api_key=api_key,
                temperature=0.1,
                max_tokens=8192,  # Claude Sonnet supports up to 8192 output tokens
                cost_tracker=self.cost_tracker
            )
            
            # Haiku model for fast operations
            self.haiku_model = ChatAnthropicWithCosts(
                model="claude-3-5-haiku-latest",  # Use latest Haiku model
                api_key=api_key,
                temperature=0.2,
                max_tokens=8192,  # Claude Haiku supports up to 8192 output tokens
                cost_tracker=self.cost_tracker
            )
            
            # Add to models dict
            self.anthropic_models = {
                "analysis": self.analysis_model,
                "haiku": self.haiku_model
            }
    
    def _init_local_models(self):
        """Initialize local Ollama models"""
        # Local Gemma model for privacy operations
        self.local_model = ChatOllama(
            model=os.getenv("OLLAMA_MODEL_NAME", "llama3.2:3b"),  # Using available local model
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.3
        )
    
    def get_routine_model(self) -> BaseChatModel:
        """Return local model if privacy mode enabled, otherwise Haiku"""
        if self.privacy_mode:
            return self.local_model
        return self.haiku_model
    
    def get_cli_model(self) -> BaseChatModel:
        """Return model for CLI conversation management"""
        return self.get_routine_model()
    
    def get_research_model(self) -> BaseChatModel:
        """Return appropriate research model based on privacy mode"""
        if self.privacy_mode:
            return self.local_model
        return self.deep_research_model
    
    def get_analysis_model(self) -> BaseChatModel:
        """Return appropriate analysis model based on privacy mode"""
        if self.privacy_mode:
            return self.local_model
        return self.analysis_model
    
    def get_model_info(self) -> Dict[str, Any]:
        """Return information about configured models"""
        return {
            "privacy_mode": self.privacy_mode,
            "cli_mode": self.cli_mode,
            "models": {
                "research": "local" if self.privacy_mode else "sonar-deep-research",
                "analysis": "local" if self.privacy_mode else "claude-sonnet-4",
                "routine": "local" if self.privacy_mode else "claude-3-5-haiku",
                "local": os.getenv("OLLAMA_MODEL_NAME", "llama3.2:3b")
            }
        }