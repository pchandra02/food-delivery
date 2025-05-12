from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from app.models.schemas import (
    SupportTicketCreate,
    SupportTicketResponse,
    ChatMessage,
    ChatResponse,
    ImageAnalysis
)
from app.services.ai_service import AIService
from app.services.storage_service import FileStorageService
from typing import Optional
import uuid
from datetime import datetime
import os
from app.core.config import settings

router = APIRouter()
ai_service = AIService()
storage_service = FileStorageService()

@router.post("/tickets", response_model=SupportTicketResponse)
async def create_support_ticket(
    order_id: str = Form(...),
    issue_type: str = Form(...),
    description: str = Form(...),
    language: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    """Create a new support ticket with optional image upload."""
    ticket_id = str(uuid.uuid4())
    
    # Handle image upload if provided
    image_analysis = None
    if image:
        if not image.content_type.startswith("image/"):
            raise HTTPException(400, "File must be an image")
        
        # Save image temporarily
        image_path = f"temp/{ticket_id}_{image.filename}"
        os.makedirs("temp", exist_ok=True)
        with open(image_path, "wb") as f:
            f.write(await image.read())
        
        # Analyze image
        image_analysis = await ai_service.analyze_image(image_path)
        print(image_analysis.analysis_summary)
        
        # Clean up
        # os.remove(image_path)
    
    # Construct the ticket object
    ticket = SupportTicketCreate(
        order_id=order_id,
        issue_type=issue_type,
        description=description,
        language=language
    )
    
    # Generate AI response
    ai_response = await ai_service.generate_response(
        ticket.issue_type,
        ticket.description,
        ticket.language,
        image_analysis
    )
    
    # Create ticket response
    ticket_response = SupportTicketResponse(
        ticket_id=ticket_id,
        status="open",
        ai_analysis=ai_response,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        requires_human=ai_response["requires_human"],
        **ticket.dict()
    )
    
    # Store ticket
    storage_service.save_ticket(ticket_id, ticket_response.dict())
    
    return ticket_response

@router.get("/tickets/{ticket_id}", response_model=SupportTicketResponse)
async def get_ticket(ticket_id: str):
    """Get ticket details by ID."""
    ticket = storage_service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    return ticket

@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(message: ChatMessage):
    """Chat with the AI bot about an existing ticket or start a new conversation."""
    if message.ticket_id:
        ticket = storage_service.get_ticket(message.ticket_id)
        if not ticket:
            raise HTTPException(404, "Ticket not found")
    
    # Generate response
    response = await ai_service.generate_response(
        ticket["issue_type"] if message.ticket_id else None,
        message.message,
        message.language
    )
    
    return ChatResponse(
        response=response["response"],
        suggested_actions=response["suggested_actions"],
        confidence_score=response["confidence_score"],
        requires_human=response["requires_human"],
        ticket_id=message.ticket_id
    )

@router.post("/analyze-image", response_model=ImageAnalysis)
async def analyze_image(image: UploadFile = File(...)):
    """Analyze an image for issues."""
    if not image.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
    
    # Save image temporarily
    image_path = f"temp/{image.filename}"
    os.makedirs("temp", exist_ok=True)
    with open(image_path, "wb") as f:
        f.write(await image.read())
    
    try:
        # Analyze image
        analysis = await ai_service.analyze_image(image_path)
        return analysis
    finally:
        # Clean up
        if os.path.exists(image_path):
            os.remove(image_path) 