from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class OrderStatus(str, Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"

class PurchaseOrder(BaseModel):
    id: str
    session_id: str
    vehicle_id: str
    customer_name: str
    customer_email: str
    customer_phone: str
    pan_or_id: str
    delivery_city: str
    purchase_price: float
    deposit_amount: float = 25000.0 # Standard refundable reservation token
    financing_selected: bool = False
    currency: str = "INR"
    status: OrderStatus = OrderStatus.PENDING_PAYMENT
    idempotency_key: str
    payment_reference: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

