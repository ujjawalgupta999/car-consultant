from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class BookingStatus(str, Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class AddOn(BaseModel):
    id: str
    name: str
    price_per_day: float
    description: str

class PriceBreakdown(BaseModel):
    base_rate: float
    duration_days: int
    subtotal: float
    addons_total: float
    taxes: float
    total_amount: float
    currency: str = "INR"

class RentalBooking(BaseModel):
    id: str
    session_id: str
    vehicle_id: str
    customer_name: str
    customer_email: str
    customer_phone: str
    driver_license_number: str
    pickup_date: str
    return_date: str
    duration_days: int
    pickup_location: str
    return_location: str
    base_rate: float
    subtotal: float
    addon_ids: List[str] = Field(default_factory=list)
    addons_total: float = 0.0
    taxes: float = 0.0
    total_amount: float
    currency: str = "INR"
    status: BookingStatus = BookingStatus.PENDING_PAYMENT
    idempotency_key: str
    payment_reference: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

