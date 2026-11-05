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
    id: str = Field(..., description="Unique purchase record ID")
    userId: str = Field(..., description="Authenticated user ID")
    vehicleId: str = Field(..., description="Vehicle ID")
    orderId: str = Field(..., description="Unique order ID from checkout")
    vehicleSnapshot: VehicleSnapshot
    purchasePrice: float
    depositAmount: float = 25000.0
    paymentStatus: str = "SUCCESS" # SUCCESS, PENDING, FAILED
    purchaseStatus: PurchaseStatus = PurchaseStatus.CONFIRMED
    purchaseDate: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    transactionReference: str
    deliveryCity: Optional[str] = None
    demo_mode: bool = True
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
