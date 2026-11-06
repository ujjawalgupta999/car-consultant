from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from .purchase import VehicleSnapshot

class RentalStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class RentalRecord(BaseModel):
    id: str = Field(..., description="Unique rental record ID (e.g., RNT-2026-XXXXXX)")
    userId: str = Field(..., description="Authenticated user ID")
    vehicleId: str = Field(..., description="Rented vehicle ID")
    paymentId: str = Field(default="", description="Linked PaymentRecord ID")
    orderId: str = Field(..., description="Rental booking ID (e.g., BK-2026-XXXXX)")
    vehicleSnapshot: VehicleSnapshot = Field(..., description="Snapshot of vehicle at time of booking")
    pickupDate: str = Field(..., description="Rental start/pickup date (YYYY-MM-DD)")
    returnDate: str = Field(..., description="Rental return/end date (YYYY-MM-DD)")
    durationDays: int = Field(default=1, description="Rental duration in days")
    pickupLocation: str = Field(default="Delhi NCR", description="City/hub where vehicle is picked up")
    returnLocation: str = Field(default="Delhi NCR", description="City/hub where vehicle is returned")
    dailyRentalPrice: float = Field(default=0.0, description="Daily rental rate in INR")
    rentalAmount: float = Field(..., description="Total rental charges settled")
    securityDeposit: float = Field(default=5000.0, description="Refundable security deposit")
    rentalStatus: RentalStatus = Field(default=RentalStatus.CONFIRMED, description="Booking fulfillment state")
    paymentStatus: str = Field(default="SUCCESS", description="SUCCESS, PENDING, FAILED")
    transactionReference: str = Field(..., description="Payment gateway transaction reference")
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updatedAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

