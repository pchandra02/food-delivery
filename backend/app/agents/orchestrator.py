from typing import Dict, Any, List, Optional, Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from .base import AgentState, BaseAgent
from .specialized import (
    LanguageDetectionAgent,
    ClassificationAgent,
    ImageReviewAgent
)
from langchain_core.messages import HumanMessage, BaseMessage
import logging
import json
import sys

# Configure logging to output to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AgentStateType(TypedDict):
    """Type definition for the state in the graph"""
    messages: List[Any]
    current_agent: str
    metadata: Dict[str, Any]
    next_agent: Optional[str]

def ensure_message_objects(messages):
    fixed = False
    new_messages = []
    for m in messages:
        if isinstance(m, BaseMessage):
            new_messages.append(m)
        elif isinstance(m, dict) and 'content' in m:
            # Try to reconstruct as HumanMessage
            new_messages.append(HumanMessage(content=m['content']))
            fixed = True
        elif isinstance(m, str):
            logger.warning(f"Message was a string, converting to HumanMessage: {m}")
            new_messages.append(HumanMessage(content=m))
            fixed = True
        else:
            logger.error(f"Unknown message type: {type(m)}; value: {m}")
            new_messages.append(HumanMessage(content=str(m)))
            fixed = True
    if fixed:
        logger.warning("Some messages were not BaseMessage objects and have been converted.")
    return new_messages

def log_state(state: Dict[str, Any], prefix: str):
    # Log state without serializing messages directly
    log_state = state.copy()
    log_state['messages'] = [m.content if isinstance(m, BaseMessage) else str(m) for m in state['messages']]
    logger.info(f"{prefix} state: {json.dumps(log_state, default=str)}")

def assert_message_objects(messages, context):
    if not isinstance(messages, list) or not all(isinstance(m, BaseMessage) for m in messages):
        raise TypeError(f"[ASSERTION FAILED] {context}: messages must be a list of BaseMessage objects, got: {[type(m) for m in messages]}")

class AgentOrchestrator:
    """Orchestrates the flow between different specialized agents"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {
            "language_detection": LanguageDetectionAgent(),
            "classification": ClassificationAgent(),
            "image_review": ImageReviewAgent(),
            # Add other agents here as they are implemented
        }
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph for agent orchestration"""
        logger.info("Building graph...")
        
        # Create the graph with state channels
        workflow = StateGraph(AgentStateType)
        
        # Add all nodes first
        for agent_name in self.agents.keys():
            logger.info(f"Adding node: {agent_name}")
            workflow.add_node(agent_name, self._wrap_agent_process(self.agents[agent_name].process, agent_name))
        
        # Add the router node
        logger.info("Adding router node")
        workflow.add_node("router", self._get_next_node)
        
        # Add edges from each agent to the router
        for agent_name in self.agents.keys():
            logger.info(f"Adding edge: {agent_name} -> router")
            workflow.add_edge(agent_name, "router")
        
        # Add edges from router to each agent or END
        logger.info("Adding conditional edges from router")
        workflow.add_conditional_edges(
            "router",
            lambda x: x["next_agent"],
            {
                "language_detection": "language_detection",
                "classification": "classification",
                "image_review": "image_review",
                END: END
            }
        )
        
        # Set the entry point
        workflow.set_entry_point("language_detection")
        
        # Compile the graph
        logger.info("Compiling graph...")
        return workflow.compile()
    
    def _wrap_agent_process(self, process_func, agent_name):
        async def wrapped(state: Dict[str, Any]):
            assert_message_objects(state['messages'], f"Before agent '{agent_name}'")
            logger.info(f"[CHECK] Before agent '{agent_name}', messages types: {[type(m) for m in state['messages']]}")
            state['messages'] = ensure_message_objects(state['messages'])
            result = await process_func(state)
            assert_message_objects(result['messages'], f"After agent '{agent_name}'")
            logger.info(f"[CHECK] After agent '{agent_name}', messages types: {[type(m) for m in result['messages']]}")
            result['messages'] = ensure_message_objects(result['messages'])
            return result
        return wrapped
    
    def _get_next_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the next node in the graph based on the state"""
        log_state(state, "Router received")
        
        if state["next_agent"] is None:
            logger.info("No next agent specified, ending workflow")
            return {"next_agent": END}
        
        if state["next_agent"] not in self.agents:
            logger.warning(f"Invalid next agent: {state['next_agent']}, ending workflow")
            return {"next_agent": END}
            
        logger.info(f"Routing to next agent: {state['next_agent']}")
        return {"next_agent": state["next_agent"]}
    
    async def process_message(self, message: str, metadata: Dict[str, Any] = None) -> AgentState:
        """Process a new message through the agent system"""
        try:
            logger.info(f"Processing message: {message}")
            logger.info(f"Initial metadata: {metadata}")
            
            # Create initial state as a dictionary
            initial_state = {
                "messages": [HumanMessage(content=message)],
                "current_agent": "language_detection",
                "metadata": metadata or {},
                "next_agent": None
            }
            
            assert_message_objects(initial_state['messages'], "Initial state before graph invoke")
            log_state(initial_state, "Initial")
            
            # Run the graph with the state directly
            logger.info("Invoking graph...")
            final_state_dict = await self.graph.ainvoke(initial_state)
            assert_message_objects(final_state_dict['messages'], "Final state after graph invoke")
            log_state(final_state_dict, "Graph returned")
            
            # Ensure next_agent is None if it's END
            if final_state_dict["next_agent"] == END:
                final_state_dict["next_agent"] = None
            
            # Create AgentState directly from the dictionary
            return AgentState(**final_state_dict)
            
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}", exc_info=True)
            raise 