"""
Base Agent Class

Provides common functionality for all agents in the system.
"""

from typing import Dict, Any, List, Optional, TypedDict
from abc import ABC, abstractmethod
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
import structlog

logger = structlog.get_logger()


class AgentState(TypedDict):
    """Common state structure for all agents"""
    messages: List[BaseMessage]
    research_topic: str
    current_task: str
    outputs: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str]


class BaseAgent(ABC):
    """Base class for all research agents"""
    
    def __init__(self, 
                 name: str,
                 model: BaseChatModel,
                 role_description: str,
                 tools: Optional[List[Any]] = None):
        self.name = name
        self.model = model
        self.role_description = role_description
        self.tools = tools or []
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for the agent"""
        return f"""You are {self.name}, a specialized research agent.

Role: {self.role_description}

Your responsibilities include:
1. Executing your specific research tasks with high quality
2. Providing detailed, accurate, and well-structured outputs
3. Collaborating effectively with other agents in the system
4. Maintaining academic rigor and professional standards
5. Documenting your process and findings clearly

Always strive for excellence in your research contributions."""
    
    async def process(self, state: AgentState) -> AgentState:
        """Process the current state and return updated state"""
        logger.info(f"{self.name} processing", task=state.get("current_task"))
        
        try:
            # Prepare messages
            messages = self._prepare_messages(state)
            
            # Execute agent logic
            result = await self._execute(messages, state)
            
            # Update state with results
            state = self._update_state(state, result)
            
        except Exception as e:
            logger.error(f"{self.name} error", error=str(e))
            state["errors"].append(f"{self.name}: {str(e)}")
        
        return state
    
    def _prepare_messages(self, state: AgentState) -> List[BaseMessage]:
        """Prepare messages for the model"""
        messages = [SystemMessage(content=self.system_prompt)]
        
        # Add task-specific context
        task_message = HumanMessage(
            content=f"""Research Topic: {state['research_topic']}
Current Task: {state['current_task']}

Please proceed with your specialized role and provide detailed output."""
        )
        messages.append(task_message)
        
        # Add relevant previous messages
        messages.extend(state.get("messages", [])[-5:])  # Last 5 messages for context
        
        return messages
    
    @abstractmethod
    async def _execute(self, messages: List[BaseMessage], state: AgentState) -> Dict[str, Any]:
        """Execute agent-specific logic"""
        pass
    
    def _update_state(self, state: AgentState, result: Dict[str, Any]) -> AgentState:
        """Update state with agent results"""
        # Add agent output to state
        if self.name not in state["outputs"]:
            state["outputs"][self.name] = []
        
        state["outputs"][self.name].append(result)
        
        # Update metadata
        state["metadata"][f"{self.name}_completed"] = True
        state["metadata"][f"{self.name}_timestamp"] = result.get("timestamp")
        
        return state
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities and metadata"""
        return {
            "name": self.name,
            "role": self.role_description,
            "tools": [tool.__class__.__name__ for tool in self.tools],
            "model": self.model._llm_type if hasattr(self.model, '_llm_type') else "unknown"
        }