from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class PaymentMethod(str, Enum):
    UPI_SIMULATOR = "upi"
    CARD_SIMULATOR = "card"
    NETBANKING_SIMULATOR = "netbanking"

class SimulatedScenario(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"

class PaymentStatus(str, Enum):
    INITIATED = "INITIATED"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class MockPayment(BaseModel):
    id: str
    transaction_reference: str
    order_or_booking_id: str
    amount: float
    currency: str = "INR"
    payment_method: PaymentMethod
    simulated_scenario: SimulatedScenario
    status: PaymentStatus
    idempotency_key: str
    error_message: Optional[str] = None
    gateway_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

