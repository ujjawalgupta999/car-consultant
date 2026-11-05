from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from ..services.payment_simulator import payment_simulator
from ..repositories.session import session_repo
from ..models.payment import PaymentMethod, SimulatedScenario, PaymentStatus
from ..models.booking import BookingStatus
from ..models.order import OrderStatus
from ..models.session import WorkflowState

router = APIRouter(prefix="/api/payments", tags=["Mock Payments"])

class MockPaymentRequest(BaseModel):
    order_or_booking_id: str
    amount: float
    currency: str = "INR"
    payment_method: str = "upi"
    simulated_scenario: str = "success"
    idempotency_key: Optional[str] = None

@router.post("/mock")
def execute_mock_payment(
    req: MockPaymentRequest,
    idempotency_header: Optional[str] = Header(None, alias="Idempotency-Key")
):
    key = idempotency_header or req.idempotency_key or f"idemp_pay_{req.order_or_booking_id}"
    
    method_enum = PaymentMethod.UPI_SIMULATOR
    if req.payment_method == "card":
        method_enum = PaymentMethod.CARD_SIMULATOR
    elif req.payment_method == "netbanking":
        method_enum = PaymentMethod.NETBANKING_SIMULATOR

    scen_enum = SimulatedScenario.SUCCESS
    if req.simulated_scenario == "failure":
        scen_enum = SimulatedScenario.FAILURE
    elif req.simulated_scenario == "timeout":
        scen_enum = SimulatedScenario.TIMEOUT

    success, payment = payment_simulator.process_mock_payment(
        order_or_booking_id=req.order_or_booking_id,
        amount=req.amount,
        payment_method=method_enum,
        simulated_scenario=scen_enum,
        idempotency_key=key,
        currency=req.currency
    )

    # Determine target session if possible
    # Update entity status
    if req.order_or_booking_id.startswith("BK-"):
        booking = session_repo.get_booking(req.order_or_booking_id)
        if booking:
            session = session_repo.get_session(booking.session_id)
            if success:
                session_repo.update_booking_status(
                    req.order_or_booking_id,
                    BookingStatus.CONFIRMED,
                    payment.transaction_reference
                )
                if session:
                    session.workflow_state = WorkflowState.CONFIRMED
                    session_repo.save_session(session)
            else:
                if session:
                    session.workflow_state = WorkflowState.PAYMENT_FAILED
                    session_repo.save_session(session)

    elif req.order_or_booking_id.startswith("ORD-"):
        order = session_repo.get_order(req.order_or_booking_id)
        if order:
            session = session_repo.get_session(order.session_id)
            if success:
                session_repo.update_order_status(
                    req.order_or_booking_id,
                    OrderStatus.CONFIRMED,
                    payment.transaction_reference
                )
                if session:
                    session.workflow_state = WorkflowState.CONFIRMED
                    session_repo.save_session(session)
            else:
                if session:
                    session.workflow_state = WorkflowState.PAYMENT_FAILED
                    session_repo.save_session(session)

    return {
        "status": "SUCCESS" if success else "FAILED",
        "payment": payment.model_dump(),
        "workflow_state": WorkflowState.CONFIRMED.value if success else WorkflowState.PAYMENT_FAILED.value
    }

@router.get("/{payment_id}")
def get_payment(payment_id: str):
    p = payment_simulator.get_payment(payment_id)
    if not p:
        raise HTTPException(status_code=404, detail="Payment record not found")
    return p.model_dump()

