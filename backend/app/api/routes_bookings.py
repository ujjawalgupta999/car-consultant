from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from ..repositories.marketplace import marketplace_repo
from ..repositories.session import session_repo
from ..services.pricing import calculate_rental_total, calculate_purchase_summary
from ..models.booking import RentalBooking, BookingStatus
from ..models.order import PurchaseOrder, OrderStatus
from ..orchestration.state_machine import StateMachine
from ..models.session import WorkflowState
import uuid
from datetime import datetime

router = APIRouter(tags=["Bookings & Orders"])

class CalculatePriceRequest(BaseModel):
    vehicle_id: str
    duration_days: int
    addon_ids: Optional[List[str]] = None

class CreateBookingRequest(BaseModel):
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
    addon_ids: Optional[List[str]] = None
    idempotency_key: Optional[str] = None

class CreateOrderRequest(BaseModel):
    session_id: str
    vehicle_id: str
    customer_name: str
    customer_email: str
    customer_phone: str
    pan_or_id: str
    delivery_city: str
    financing_selected: bool = False
    deposit_amount: float = 25000.0
    idempotency_key: Optional[str] = None

@router.post("/api/bookings/calculate")
def calculate_price(req: CalculatePriceRequest):
    vehicle = marketplace_repo.get_vehicle_by_id(req.vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    addons = req.addon_ids or []
    breakdown = calculate_rental_total(vehicle, req.duration_days, addons)
    return breakdown.model_dump()

@router.post("/api/bookings", status_code=201)
def create_booking(
    req: CreateBookingRequest,
    idempotency_header: Optional[str] = Header(None, alias="Idempotency-Key")
):
    key = idempotency_header or req.idempotency_key or f"idemp_bk_{uuid.uuid4().hex[:12]}"
    
    vehicle = marketplace_repo.get_vehicle_by_id(req.vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    addons = req.addon_ids or []
    breakdown = calculate_rental_total(vehicle, req.duration_days, addons)

    booking_id = f"BK-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"
    booking = RentalBooking(
        id=booking_id,
        session_id=req.session_id,
        vehicle_id=req.vehicle_id,
        customer_name=req.customer_name,
        customer_email=req.customer_email,
        customer_phone=req.customer_phone,
        driver_license_number=req.driver_license_number,
        pickup_date=req.pickup_date,
        return_date=req.return_date,
        duration_days=req.duration_days,
        pickup_location=req.pickup_location,
        return_location=req.return_location,
        base_rate=breakdown.base_rate,
        subtotal=breakdown.subtotal,
        addon_ids=addons,
        addons_total=breakdown.addons_total,
        taxes=breakdown.taxes,
        total_amount=breakdown.total_amount,
        currency="INR",
        status=BookingStatus.PENDING_PAYMENT,
        idempotency_key=key
    )

    saved = session_repo.create_booking(booking)
    
    # Update session state to CHECKOUT_READY
    session = session_repo.get_session(req.session_id)
    if session:
        session.active_booking_id = saved.id
        session.selected_vehicle_id = req.vehicle_id
        session.workflow_state = WorkflowState.CHECKOUT_READY
        session_repo.save_session(session)

    return {
        "booking_id": saved.id,
        "booking": saved.model_dump(),
        "workflow_state": WorkflowState.CHECKOUT_READY.value
    }

@router.get("/api/bookings/{booking_id}")
def get_booking(booking_id: str):
    b = session_repo.get_booking(booking_id)
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")
    return b.model_dump()

@router.post("/api/orders", status_code=201)
def create_purchase_order(
    req: CreateOrderRequest,
    idempotency_header: Optional[str] = Header(None, alias="Idempotency-Key")
):
    key = idempotency_header or req.idempotency_key or f"idemp_ord_{uuid.uuid4().hex[:12]}"
    
    vehicle = marketplace_repo.get_vehicle_by_id(req.vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    order_id = f"ORD-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"
    order = PurchaseOrder(
        id=order_id,
        session_id=req.session_id,
        vehicle_id=req.vehicle_id,
        customer_name=req.customer_name,
        customer_email=req.customer_email,
        customer_phone=req.customer_phone,
        pan_or_id=req.pan_or_id,
        delivery_city=req.delivery_city,
        purchase_price=vehicle.purchase_price,
        deposit_amount=req.deposit_amount,
        financing_selected=req.financing_selected,
        status=OrderStatus.PENDING_PAYMENT,
        idempotency_key=key
    )

    saved = session_repo.create_order(order)
    
    session = session_repo.get_session(req.session_id)
    if session:
        session.active_order_id = saved.id
        session.selected_vehicle_id = req.vehicle_id
        session.workflow_state = WorkflowState.CHECKOUT_READY
        session_repo.save_session(session)

    return {
        "order_id": saved.id,
        "order": saved.model_dump(),
        "workflow_state": WorkflowState.CHECKOUT_READY.value
    }

@router.get("/api/orders/{order_id}")
def get_order(order_id: str):
    o = session_repo.get_order(order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    return o.model_dump()

