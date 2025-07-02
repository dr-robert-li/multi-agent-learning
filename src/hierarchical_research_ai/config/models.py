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

load_dotenv()


class ChatPerplexity(BaseChatModel):
    """Custom Perplexity chat model implementation"""
    
    model: str
    api_key: str
    base_url: str = "https://api.perplexity.ai"
    temperature: float = 0.2
    max_tokens: int = 4000
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set longer timeout for deep research models
        timeout = 300.0 if 'large' in self.model or 'deep' in self.model else 30.0
        # Set client without triggering pydantic validation
        object.__setattr__(self, 'client', httpx.Client(
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=timeout
        ))
    
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
        
        response = self.client.post(
            f"{self.base_url}/chat/completions",
            json={
                "model": self.model,
                "messages": formatted_messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                **kwargs
            }
        )
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=content))]
        )
    
    async def _agenerate(self, messages: list[BaseMessage], **kwargs) -> ChatResult:
        """Async generate chat response"""
        # Set longer timeout for deep research models
        timeout = 300.0 if 'large' in self.model or 'deep' in self.model else 30.0
        
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
            
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": formatted_messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    **kwargs
                }
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            return ChatResult(
                generations=[ChatGeneration(message=AIMessage(content=content))]
            )
    
    @property
    def _llm_type(self) -> str:
        return "perplexity"


class ModelConfig:
    """Centralized model configuration and management"""
    
    def __init__(self):
        self.privacy_mode = os.getenv("PRIVACY_MODE", "false").lower() == "true"
        self.cli_mode = os.getenv("CLI_MODE", "false").lower() == "true"
        
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
            # Deep research model - using llama-3.1-sonar-large-128k-online (working alternative)
            # Note: sonar-deep-research has timeout issues, using tested working model
            self.deep_research_model = ChatPerplexity(
                model="llama-3.1-sonar-large-128k-online",
                api_key=api_key,
                base_url=os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai"),
                temperature=0.1,
                max_tokens=4000  # Reduced to prevent timeouts
            )
            
            # Fast search model - sonar-pro (8k output limit per documentation)
            self.fast_search_model = ChatPerplexity(
                model="sonar-pro",
                api_key=api_key,
                base_url=os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai"),
                temperature=0.2,
                max_tokens=8000
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
            self.analysis_model = ChatAnthropic(
                model="claude-3-5-sonnet-20241022",  # Using available model
                api_key=api_key,
                temperature=0.1,
                max_tokens=8192  # Reduced to stay within model limits
            )
            
            # Haiku model for fast operations
            self.haiku_model = ChatAnthropic(
                model="claude-3-5-haiku-20241022",  # Use specific Haiku model version
                api_key=api_key,
                temperature=0.2,
                max_tokens=8192  # Reduced to stay within limits
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