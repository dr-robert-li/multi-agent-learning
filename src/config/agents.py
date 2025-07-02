"""
Agent configuration for Hierarchical Research AI
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    """Configuration for individual agents"""
    
    name: str
    description: str
    model_type: str = "default"
    temperature: float = 0.1
    max_tokens: int = 4000
    tools: list = field(default_factory=list)
    system_prompt: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "name": self.name,
            "description": self.description,
            "model_type": self.model_type,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "tools": self.tools,
            "system_prompt": self.system_prompt
        }


@dataclass
class TeamConfig:
    """Configuration for agent teams"""
    
    name: str
    description: str
    agents: list = field(default_factory=list)
    supervisor_model: str = "default"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "name": self.name,
            "description": self.description,
            "agents": self.agents,
            "supervisor_model": self.supervisor_model
        }