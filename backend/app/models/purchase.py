from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class PurchaseStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    PENDING_DELIVERY = "PENDING_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class VehicleSnapshot(BaseModel):
    id: str
    brand: str
    model: str
    variant: Optional[str] = "Standard"
    year: int
    category: str
    image: str
    transmission: str
    fuel_type: str
    location: Optional[str] = None
    specs: Dict[str, Any] = Field(default_factory=dict)

class PurchaseRecord(BaseModel):
    id: str = Field(..., description="Unique purchase record ID (e.g., PUR-2026-XXXXXX)")
    userId: str = Field(..., description="Authenticated user ID")
    vehicleId: str = Field(..., description="Target vehicle ID")
    paymentId: str = Field(default="", description="Linked PaymentRecord ID")
    orderId: str = Field(..., description="Unique purchase order ID from checkout")
    vehicleSnapshot: VehicleSnapshot = Field(..., description="Immutable snapshot of vehicle specs and media")
    purchasePrice: float = Field(..., description="Vehicle purchase price in INR")
    depositAmount: float = Field(default=25000.0, description="Token deposit paid during checkout")
    paymentStatus: str = Field(default="SUCCESS", description="SUCCESS, PENDING, FAILED")
    purchaseStatus: PurchaseStatus = Field(default=PurchaseStatus.CONFIRMED, description="Fulfillment state")
    purchaseDate: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    transactionReference: str = Field(..., description="Payment transaction reference code")
    deliveryCity: Optional[str] = Field(default=None, description="Destination city for delivery")
    demo_mode: bool = Field(default=True, description="Indicates simulated hackathon transaction")
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updatedAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    # Legacy alias
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
