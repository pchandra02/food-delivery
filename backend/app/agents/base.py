from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig

@dataclass
class AgentState:
    """State passed between agents in the workflow"""
    messages: List[BaseMessage]
    current_agent: str
    metadata: Dict[str, Any]
    next_agent: Optional[str] = None

class BaseAgent:
    """Base class for all specialized agents"""
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the current state and return the next state"""
        raise NotImplementedError("Subclasses must implement process()")
    
    def _get_last_human_message(self, messages: List[BaseMessage]) -> Optional[str]:
        """Get the content of the last human message"""
        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                return message.content
        return None
    
    def _add_ai_message(self, messages: List[BaseMessage], content: str) -> List[BaseMessage]:
        """Add an AI message to the message list"""
        return messages + [AIMessage(content=content)]
    
    def should_handle(self, state: Dict[str, Any]) -> bool:
        """Determine if this agent should handle the current state"""
        raise NotImplementedError("Each agent must implement should_handle method")
    
    def get_next_agent(self, state: Dict[str, Any]) -> Optional[str]:
        """Determine the next agent in the chain"""
        return state.get("next_agent") 