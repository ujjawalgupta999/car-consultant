from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ListingStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    ACTIVE = "ACTIVE"
    SOLD = "SOLD"
    REJECTED = "REJECTED"
    REMOVED = "REMOVED"

class ApprovalStatus(str, Enum):
    PENDING = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class VehicleListing(BaseModel):
    id: str = Field(..., description="Unique listing ID")
    sellerId: str = Field(..., description="Authenticated user ID of the seller")
    brand: str
    model: str
    variant: Optional[str] = "Standard"
    year: int = 2022
    registration_year: Optional[int] = None
    fuel_type: str = "Petrol"
    transmission: str = "Automatic"
    kms_driven: int = 25000
    condition: str = "Excellent" # "Excellent", "Good", "Fair"
    ownership_count: int = 1
    location: str = "Delhi NCR"
    expected_price: float = 1200000.0
    images: List[str] = Field(default_factory=list)
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    is_registered_in_user_name: bool = True
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    status: ListingStatus = ListingStatus.ACTIVE
    demo_mode: bool = True
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

