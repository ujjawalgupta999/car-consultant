from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class OwnershipSource(str, Enum):
    PURCHASED_PLATFORM = "PURCHASED_PLATFORM"
    MANUALLY_ADDED = "MANUALLY_ADDED"
    LISTED_FOR_SALE = "LISTED_FOR_SALE"
    SOLD = "SOLD"

class OwnedVehicle(BaseModel):
    id: str = Field(..., description="Unique ownership ID")
    userId: str = Field(..., description="Authenticated user ID")
    vehicleId: Optional[str] = None
    brand: str
    model: str
    variant: Optional[str] = "Standard"
    year: int
    registrationNumber: Optional[str] = None
    source: OwnershipSource = OwnershipSource.PURCHASED_PLATFORM
    purchaseDate: Optional[str] = None
    purchasePrice: Optional[float] = None
    currentEstimatedValue: Optional[float] = None
    image: str
    status: str = "Active" # "Active", "Listed for Sale", "Sold"
    linkedOrderId: Optional[str] = None
    linkedListingId: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

