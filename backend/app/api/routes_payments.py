from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
from ..services.transaction_service import transaction_service
from ..api.routes_auth import resolve_user_id

router = APIRouter(prefix="/api/payments", tags=["Unified Payments"])

class MockPaymentRequest(BaseModel):
    order_or_booking_id: Optional[str] = None
    orderId: Optional[str] = None
    amount: float
    currency: str = "INR"
    payment_method: str = "upi"
    paymentMethod: Optional[str] = None
    simulated_scenario: str = "success"
    simScenario: Optional[str] = None
    idempotency_key: Optional[str] = None
    idempotencyKey: Optional[str] = None

@router.get("")
def get_user_payments(
    status: Optional[str] = Query(None, description="Filter: SUCCESS, FAILED, PENDING, CANCELLED, REFUNDED"),
    transaction_type: Optional[str] = Query(None, description="Filter: BUY or RENT"),
    search: Optional[str] = Query(None, description="Search by transaction ID, order ID, or vehicle ID"),
    sort: Optional[str] = Query("date_desc", description="Sort: date_desc, date_asc, amount_desc, amount_asc"),
    authorization: Optional[str] = Header(None)
):
    user_id = resolve_user_id(authorization)
    payments = transaction_service.get_user_payments(
        user_id=user_id,
        status=status,
        transaction_type=transaction_type,
        search=search,
        sort_by=sort
    )
    return {
        "userId": user_id,
        "total": len(payments),
        "payments": [p.model_dump() for p in payments]
    }

@router.get("/order/{order_id}")
def get_payment_by_order(order_id: str, authorization: Optional[str] = Header(None)):
    user_id = resolve_user_id(authorization)
    payment = transaction_service.get_payment_by_order(order_id, user_id=user_id)
    if not payment:
        raise HTTPException(status_code=404, detail="No payment found for specified order")
    return payment.model_dump()

@router.get("/{payment_id}")
def get_payment_by_id(payment_id: str, authorization: Optional[str] = Header(None)):
    user_id = resolve_user_id(authorization)
    payment = transaction_service.get_payment(payment_id, user_id=user_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    return payment.model_dump()

@router.post("/mock/confirm")
async def confirm_mock_payment_endpoint(
    req: MockPaymentRequest,
    idempotency_header: Optional[str] = Header(None, alias="Idempotency-Key"),
    authorization: Optional[str] = Header(None)
):
    user_id = resolve_user_id(authorization)
    order_id = req.orderId or req.order_or_booking_id
    if not order_id:
        raise HTTPException(status_code=400, detail="orderId is required.")

    method = req.paymentMethod or req.payment_method or "upi"
    scenario = req.simScenario or req.simulated_scenario or "success"
    key = idempotency_header or req.idempotencyKey or req.idempotency_key or f"idemp_pay_{order_id}"

    success, payment, linked_entity = await transaction_service.confirm_mock_payment(
        order_or_booking_id=order_id,
        amount=req.amount,
        payment_method=method,
        simulated_scenario=scenario,
        idempotency_key=key,
        user_id=user_id,
        currency=req.currency
    )

    p_dict = payment.model_dump()
    p_dict["transaction_reference"] = payment.paymentReference
    p_dict["transactionReference"] = payment.paymentReference

    return {
        "status": "SUCCESS" if success else "FAILED",
        "payment": p_dict,
        "workflow_state": "CONFIRMED" if success else "PAYMENT_FAILED",
        "linked_entity": linked_entity.model_dump() if linked_entity else None
    }

# Backward compatibility alias
@router.post("/mock")
async def execute_mock_payment_legacy(
    req: MockPaymentRequest,
    idempotency_header: Optional[str] = Header(None, alias="Idempotency-Key"),
    authorization: Optional[str] = Header(None)
):
    return await confirm_mock_payment_endpoint(req, idempotency_header, authorization)

@router.post("/{payment_id}/recheck")
def recheck_payment_status(payment_id: str, authorization: Optional[str] = Header(None)):
    user_id = resolve_user_id(authorization)
    payment = transaction_service.recheck_payment(payment_id, user_id=user_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found.")
    return {
        "status": payment.paymentStatus.value,
        "payment": payment.model_dump()
    }
