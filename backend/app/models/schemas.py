from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from fastapi import Form

class IssueType(str, Enum):
    PACKAGING_SPILLAGE = "packaging_spillage"
    MISSING_ITEM = "missing_item"
    FOOD_QUALITY = "food_quality"
    ORDER_CANCELLATION = "order_cancellation"
    REFUND_QUERY = "refund_query"
    WRONG_ADDRESS = "wrong_address"
    VENDOR_ISSUE = "vendor_issue"
    RIDER_ISSUE = "rider_issue"
    DELIVERY_STATUS = "delivery_status"
    ESCALATION = "escalation"

class Language(str, Enum):
    ENGLISH = "en"
    ARABIC = "ar"

class SupportTicketBase(BaseModel):
    order_id: str = Field(..., description="Order ID for reference")
    issue_type: IssueType = Field(..., description="Type of issue reported")
    description: str = Field(..., description="Detailed description of the issue")
    language: Language = Field(default=Language.ENGLISH, description="Language preference")
    image_url: Optional[str] = Field(None, description="URL of uploaded image if any")

class SupportTicketCreate(SupportTicketBase):
    pass

class SupportTicketResponse(SupportTicketBase):
    ticket_id: str
    status: str
    ai_analysis: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    resolution: Optional[str] = None
    requires_human: bool = False

class ChatMessage(BaseModel):
    message: str
    language: Language = Language.ENGLISH
    ticket_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    suggested_actions: List[str]
    confidence_score: float
    requires_human: bool = False
    ticket_id: Optional[str] = None

class ImageAnalysis(BaseModel):
    issue_detected: bool
    confidence_score: float
    detected_issues: List[str]
    image_quality: str
    analysis_summary: str 