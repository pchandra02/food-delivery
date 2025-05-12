from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from ..agents.orchestrator import AgentOrchestrator
import aiofiles
import os
from datetime import datetime
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
orchestrator = AgentOrchestrator()

class ChatRequest(BaseModel):
    message: str
    metadata: Dict[str, Any] = {}

class ChatResponse(BaseModel):
    response: str
    metadata: Dict[str, Any] = {}

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Process the message through the agent system
        state = await orchestrator.process_message(request.message, request.metadata)
        
        # Get the last message from the state
        if not state.messages:
            raise HTTPException(status_code=500, detail="No response generated")
            
        last_message = state.messages[-1]
        
        return ChatResponse(
            response=last_message.content,
            metadata=state.metadata
        )
    except Exception as e:
        # Log the full error details
        error_msg = f"Error processing chat request: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = "storage/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join(upload_dir, filename)
        
        # Save the file
        async with aiofiles.open(filepath, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        # Return the file path for the agent system to use
        return {"filepath": filepath}
    except Exception as e:
        error_msg = f"Error uploading image: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=str(e)) 