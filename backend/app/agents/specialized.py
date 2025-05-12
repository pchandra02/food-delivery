from typing import Dict, Any, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseAgent, AgentState
from ..core.config import settings
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

def assert_message_objects(messages, context):
    if not isinstance(messages, list) or not all(isinstance(m, BaseMessage) for m in messages):
        raise TypeError(f"[ASSERTION FAILED] {context}: messages must be a list of BaseMessage objects, got: {[type(m) for m in messages]}")

class LanguageDetectionAgent(BaseAgent):
    """Agent responsible for detecting the language of user input"""
    
    def __init__(self):
        super().__init__()
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            api_key=settings.OPENAI_API_KEY
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a language detection expert. Detect the language of the following text and respond with the ISO 639-1 language code."),
            ("human", "{text}")
        ])
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        assert_message_objects(state['messages'], "LanguageDetectionAgent.process entry")
        logger.info(f"LanguageDetectionAgent received state: {json.dumps(state, default=str)}")
        
        # Get the last human message
        last_message = state['messages'][-1].content
        
        # Process the message
        response = await self.llm.ainvoke(self.prompt.format(text=last_message))
        
        result = {
            "messages": state['messages'] + [AIMessage(content=f"I detected that your message is in {response.content}.")],
            "current_agent": state["current_agent"],
            "metadata": state["metadata"],
            "next_agent": "classification"
        }
        assert_message_objects(result['messages'], "LanguageDetectionAgent.process return")
        logger.info(f"LanguageDetectionAgent returning state: {json.dumps(result, default=str)}")
        return result
    
    def should_handle(self, state: Dict[str, Any]) -> bool:
        logger.info(f"LanguageDetectionAgent checking if should handle: {json.dumps(state, default=str)}")
        return state["current_agent"] == self.name

class ImageReviewAgent(BaseAgent):
    """Agent responsible for analyzing images for packaging/spillage issues"""
    
    def __init__(self):
        super().__init__()
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.llm = ChatOpenAI(
            model="gpt-4-vision-preview",
            api_key=settings.OPENAI_API_KEY
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at analyzing food delivery packaging issues. Analyze the image and identify any packaging damage or spillage issues."),
            ("human", "Please analyze this image: {image_url}")
        ])
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        assert_message_objects(state['messages'], "ImageReviewAgent.process entry")
        logger.info(f"ImageReviewAgent received state: {json.dumps(state, default=str)}")
        
        # Add a final response
        result = {
            "messages": state['messages'] + [AIMessage(content="I've reviewed your request. Since no image was provided, I can't analyze it. Please provide an image URL if you'd like me to review it.")],
            "current_agent": state["current_agent"],
            "metadata": state["metadata"],
            "next_agent": None  # End the workflow
        }
        assert_message_objects(result['messages'], "ImageReviewAgent.process return")
        logger.info(f"ImageReviewAgent returning state: {json.dumps(result, default=str)}")
        return result
    
    def should_handle(self, state: Dict[str, Any]) -> bool:
        logger.info(f"ImageReviewAgent checking if should handle: {json.dumps(state, default=str)}")
        return (state["current_agent"] == self.name and 
                "image_url" in state["metadata"])

class ClassificationAgent(BaseAgent):
    """Agent responsible for classifying the type of issue"""
    
    def __init__(self):
        super().__init__()
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            api_key=settings.OPENAI_API_KEY
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at classifying food delivery issues. 
            Classify the issue into one of these categories:
            - packaging_spillage
            - missing_incorrect_item
            - food_quality
            - refund_cancellation
            - rider_vendor_issue
            Respond with just the category name."""),
            ("human", "{text}")
        ])
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        assert_message_objects(state['messages'], "ClassificationAgent.process entry")
        logger.info(f"ClassificationAgent received state: {json.dumps(state, default=str)}")
        
        # Get the last human message
        last_message = state['messages'][-2].content  # Get the original message, not the language detection response
        
        # Process the message
        response = await self.llm.ainvoke(self.prompt.format(text=last_message))
        category = response.content.strip()
        
        result = {
            "messages": state['messages'] + [AIMessage(content=f"I've classified your issue as: {category}")],
            "current_agent": state["current_agent"],
            "metadata": state["metadata"],
            "next_agent": "image_review"
        }
        assert_message_objects(result['messages'], "ClassificationAgent.process return")
        logger.info(f"ClassificationAgent returning state: {json.dumps(result, default=str)}")
        return result
    
    def should_handle(self, state: Dict[str, Any]) -> bool:
        logger.info(f"ClassificationAgent checking if should handle: {json.dumps(state, default=str)}")
        return state["current_agent"] == self.name
    
    def _get_next_agent_for_category(self, category: str) -> str:
        category_to_agent = {
            "packaging_spillage": "image_review",
            "missing_incorrect_item": "order_reconciliation",
            "food_quality": "quality_feedback",
            "refund_cancellation": "refund_policy",
            "rider_vendor_issue": "sentiment_analysis"
        }
        return category_to_agent.get(category, "response") 