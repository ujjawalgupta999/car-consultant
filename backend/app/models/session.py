from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from .preferences import UserPreferences

class WorkflowState(str, Enum):
    NEW = "NEW"
    INTERVIEWING = "INTERVIEWING"
    READY_TO_SEARCH = "READY_TO_SEARCH"
    SEARCHING = "SEARCHING"
    RANKING = "RANKING"
    RECOMMENDATIONS_READY = "RECOMMENDATIONS_READY"
    VEHICLE_SELECTED = "VEHICLE_SELECTED"
    BOOKING_IN_PROGRESS = "BOOKING_IN_PROGRESS"
    CHECKOUT_READY = "CHECKOUT_READY"
    PAYMENT_PROCESSING = "PAYMENT_PROCESSING"
    CONFIRMED = "CONFIRMED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    CANCELLED = "CANCELLED"

class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    id: str
    role: ChatRole
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    a2ui_surfaces: List[str] = Field(default_factory=list)
    mcp_app: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class Session(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    workflow_state: WorkflowState = WorkflowState.NEW
    preferences: UserPreferences
    search_parameters: Optional[Dict[str, Any]] = None
    search_results: List[Dict[str, Any]] = Field(default_factory=list)
    selected_vehicle_id: Optional[str] = None
    active_booking_id: Optional[str] = None
    active_order_id: Optional[str] = None
    active_workflow: Optional[str] = None
    pending_question: Optional[str] = None
    workflow_data: Dict[str, Any] = Field(default_factory=dict)
    last_intent: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

