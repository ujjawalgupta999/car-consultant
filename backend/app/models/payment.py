from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class PaymentMethod(str, Enum):
    UPI = "upi"
    CARD = "card"
    NETBANKING = "netbanking"
    UPI_SIMULATOR = "upi"
    CARD_SIMULATOR = "card"
    NETBANKING_SIMULATOR = "netbanking"

class SimulatedScenario(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    # Legacy alias
    INITIATED = "PENDING"

class TransactionType(str, Enum):
    BUY = "BUY"
    RENT = "RENT"

class PaymentRecord(BaseModel):
    id: str = Field(..., description="Unique payment identifier (e.g., PAY-20261106-XXXXXX)")
    userId: str = Field(..., description="Authenticated user ID")
    orderId: str = Field(..., description="Associated purchase order or rental booking ID")
    transactionId: str = Field(..., description="Authoritative transaction ID (e.g., TXN-MOCK-XXXXXX)")
    vehicleId: str = Field(..., description="Target vehicle ID")
    transactionType: TransactionType = Field(default=TransactionType.BUY, description="BUY or RENT")
    amount: float = Field(..., description="Settled transaction amount in currency units")
    currency: str = Field(default="INR", description="Three-letter currency code")
    paymentMethod: str = Field(default="upi", description="Payment method: upi, card, or netbanking")
    paymentStatus: PaymentStatus = Field(default=PaymentStatus.SUCCESS, description="Authoritative payment status")
    paymentProvider: str = Field(default="MOCK_PAYMENT", description="Payment provider or mock rail indicator")
    paymentReference: str = Field(..., description="Gateway transaction reference code")
    idempotencyKey: Optional[str] = Field(default=None, description="Idempotency key to prevent duplicate charges")
    errorMessage: Optional[str] = Field(default=None, description="Error reason if payment failed or was declined")
    gatewayMetadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata from payment processing simulator")
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updatedAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

# Legacy compatibility alias
class MockPayment(BaseModel):
    id: str
    transaction_reference: str
    order_or_booking_id: str
    amount: float
    currency: str = "INR"
    payment_method: PaymentMethod = PaymentMethod.UPI_SIMULATOR
    simulated_scenario: SimulatedScenario = SimulatedScenario.SUCCESS
    status: PaymentStatus = PaymentStatus.SUCCESS
    idempotency_key: str
    error_message: Optional[str] = None
    gateway_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
