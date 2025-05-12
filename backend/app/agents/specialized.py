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
import os
from ..services.storage_service import StorageService
from ..services.vision_service import VisionService

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
        self.storage_service = StorageService()
        self.vision_service = VisionService()
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        assert_message_objects(state['messages'], "ImageReviewAgent.process entry")
        logger.info(f"ImageReviewAgent received state: {json.dumps(state, default=str)}")
        
        if "image_url" not in state["metadata"]:
            return {
                "messages": state['messages'] + [AIMessage(content="I've reviewed your request. Since no image was provided, I can't analyze it. Please provide an image URL if you'd like me to review it.")],
                "current_agent": state["current_agent"],
                "metadata": state["metadata"],
                "next_agent": None
            }

        try:
            # Upload the image to Azure Storage
            local_image_path = state["metadata"]["image_url"]
            blob_url = await self.storage_service.upload_file(local_image_path)
            
            # Update metadata with the blob URL
            state["metadata"]["blob_url"] = blob_url
            
            # Analyze the image using Google Vision API
            analysis = await self.vision_service.analyze_image(blob_url)
            
            # Generate a detailed response based on the analysis
            response_parts = []
            
            if analysis['issues_detected']:
                response_parts.append("I've detected some issues in the image:")
                # Add specific issues found
                for label in analysis['labels']:
                    if label['description'].lower() in ['damage', 'spill', 'leak', 'broken', 'dirty', 'mess']:
                        response_parts.append(f"- {label['description']} (confidence: {label['confidence']:.2f})")
            else:
                response_parts.append("No significant issues detected in the image.")
            
            # Add food-related observations
            food_related = [label for label in analysis['labels'] 
                          if label['description'].lower() in ['food', 'meal', 'dish', 'restaurant', 'delivery', 'package']]
            if food_related:
                response_parts.append("\nFood-related content detected:")
                for item in food_related:
                    response_parts.append(f"- {item['description']} (confidence: {item['confidence']:.2f})")
            
            response = "\n".join(response_parts)
            
            result = {
                "messages": state['messages'] + [AIMessage(content=response)],
                "current_agent": state["current_agent"],
                "metadata": state["metadata"],
                "next_agent": None
            }
            
            # Clean up the local file
            os.remove(local_image_path)
            
            assert_message_objects(result['messages'], "ImageReviewAgent.process return")
            logger.info(f"ImageReviewAgent returning state: {json.dumps(result, default=str)}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return {
                "messages": state['messages'] + [AIMessage(content=f"Sorry, I encountered an error while analyzing the image: {str(e)}")],
                "current_agent": state["current_agent"],
                "metadata": state["metadata"],
                "next_agent": None
            }
    
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