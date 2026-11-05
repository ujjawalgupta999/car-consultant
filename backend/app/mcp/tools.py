from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
from ..repositories.marketplace import marketplace_repo
from ..repositories.session import session_repo
from ..marketplace.availability import is_vehicle_available_for_dates
from ..ranking.engine import RankingEngine
from ..services.pricing import calculate_rental_total, calculate_purchase_summary, ADDON_CATALOG
from ..services.payment_simulator import payment_simulator
from ..models.payment import PaymentMethod, SimulatedScenario
from ..models.booking import RentalBooking, BookingStatus
from ..models.order import PurchaseOrder, OrderStatus

def tool_search_vehicles(
    intent: str = "rent",
    location: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    transmission: Optional[str] = None,
    fuel_type: Optional[str] = None,
    seats: Optional[int] = None,
    seats_min: Optional[int] = None,
    seats_max: Optional[int] = None,
    seats_match_type: Optional[str] = "exact",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    vehicles = marketplace_repo.search_vehicles(
        intent=intent,
        location=location,
        category=category,
        min_price=min_price,
        max_price=max_price,
        transmission=transmission,
        fuel_type=fuel_type,
        seats=seats,
        seats_min=seats_min,
        seats_max=seats_max,
        seats_match_type=seats_match_type,
        start_date=start_date,
        end_date=end_date
    )
    return {
        "status": "success",
        "count": len(vehicles),
        "vehicles": [v.model_dump() for v in vehicles[:10]]
    }

def tool_get_vehicle_details(vehicle_id: str) -> Dict[str, Any]:
    v = marketplace_repo.get_vehicle_by_id(vehicle_id)
    if not v:
        return {"status": "error", "message": f"Vehicle '{vehicle_id}' not found."}
    return {"status": "success", "vehicle": v.model_dump()}

def tool_check_vehicle_availability(
    vehicle_id: str,
    start_date: str,
    end_date: str
) -> Dict[str, Any]:
    v = marketplace_repo.get_vehicle_by_id(vehicle_id)
    if not v:
        return {"status": "error", "message": f"Vehicle '{vehicle_id}' not found."}
    is_avail, conflicts = is_vehicle_available_for_dates(v, start_date, end_date)
    return {
        "status": "success",
        "vehicle_id": vehicle_id,
        "is_available": is_avail,
        "conflicts": [c.model_dump() for c in conflicts]
    }

def tool_compare_vehicles(vehicle_ids: List[str]) -> Dict[str, Any]:
    compared = []
    for vid in vehicle_ids[:4]:
        v = marketplace_repo.get_vehicle_by_id(vid)
        if v:
            compared.append(v.model_dump())
    return {
        "status": "success",
        "compared_count": len(compared),
        "vehicles": compared
    }

def tool_calculate_booking_total(
    vehicle_id: str,
    duration_days: int,
    addon_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    v = marketplace_repo.get_vehicle_by_id(vehicle_id)
    if not v:
        return {"status": "error", "message": f"Vehicle '{vehicle_id}' not found."}
    addons = addon_ids or []
    breakdown = calculate_rental_total(v, duration_days, addons)
    return {
        "status": "success",
        "vehicle_id": vehicle_id,
        "pricing": breakdown.model_dump()
    }

def tool_create_booking(
    session_id: str,
    vehicle_id: str,
    customer_name: str,
    customer_email: str,
    customer_phone: str,
    driver_license_number: str,
    pickup_date: str,
    return_date: str,
    duration_days: int,
    pickup_location: str,
    return_location: str,
    addon_ids: Optional[List[str]] = None,
    idempotency_key: Optional[str] = None
) -> Dict[str, Any]:
    v = marketplace_repo.get_vehicle_by_id(vehicle_id)
    if not v:
        return {"status": "error", "message": f"Vehicle '{vehicle_id}' not found."}

    addons = addon_ids or []
    breakdown = calculate_rental_total(v, duration_days, addons)

    key = idempotency_key or f"idemp_{uuid.uuid4().hex[:12]}"
    booking_id = f"BK-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"

    booking = RentalBooking(
        id=booking_id,
        session_id=session_id,
        vehicle_id=vehicle_id,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        driver_license_number=driver_license_number,
        pickup_date=pickup_date,
        return_date=return_date,
        duration_days=duration_days,
        pickup_location=pickup_location,
        return_location=return_location,
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

    saved_booking = session_repo.create_booking(booking)
    return {
        "status": "success",
        "booking_id": saved_booking.id,
        "booking": saved_booking.model_dump()
    }

def tool_create_purchase_order(
    session_id: str,
    vehicle_id: str,
    customer_name: str,
    customer_email: str,
    customer_phone: str,
    pan_or_id: str,
    delivery_city: str,
    financing_selected: bool = False,
    deposit_amount: float = 25000.0,
    idempotency_key: Optional[str] = None
) -> Dict[str, Any]:
    v = marketplace_repo.get_vehicle_by_id(vehicle_id)
    if not v:
        return {"status": "error", "message": f"Vehicle '{vehicle_id}' not found."}

    key = idempotency_key or f"idemp_{uuid.uuid4().hex[:12]}"
    order_id = f"ORD-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"

    order = PurchaseOrder(
        id=order_id,
        session_id=session_id,
        vehicle_id=vehicle_id,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        pan_or_id=pan_or_id,
        delivery_city=delivery_city,
        purchase_price=v.purchase_price,
        deposit_amount=deposit_amount,
        financing_selected=financing_selected,
        status=OrderStatus.PENDING_PAYMENT,
        idempotency_key=key
    )

    saved_order = session_repo.create_order(order)
    return {
        "status": "success",
        "order_id": saved_order.id,
        "order": saved_order.model_dump()
    }

def tool_get_booking_status(booking_id: str) -> Dict[str, Any]:
    b = session_repo.get_booking(booking_id)
    if b:
        return {"status": "success", "type": "rental", "record": b.model_dump()}
    o = session_repo.get_order(booking_id)
    if o:
        return {"status": "success", "type": "purchase", "record": o.model_dump()}
    return {"status": "error", "message": f"Record '{booking_id}' not found."}

def tool_simulate_mock_payment(
    order_or_booking_id: str,
    amount: float,
    payment_method: str = "upi",
    scenario: str = "success",
    idempotency_key: Optional[str] = None
) -> Dict[str, Any]:
    method_enum = PaymentMethod.UPI_SIMULATOR
    if payment_method == "card":
        method_enum = PaymentMethod.CARD_SIMULATOR
    elif payment_method == "netbanking":
        method_enum = PaymentMethod.NETBANKING_SIMULATOR

    scen_enum = SimulatedScenario.SUCCESS
    if scenario == "failure":
        scen_enum = SimulatedScenario.FAILURE
    elif scenario == "timeout":
        scen_enum = SimulatedScenario.TIMEOUT

    key = idempotency_key or f"idemp_pay_{uuid.uuid4().hex[:12]}"

    success, payment = payment_simulator.process_mock_payment(
        order_or_booking_id=order_or_booking_id,
        amount=amount,
        payment_method=method_enum,
        simulated_scenario=scen_enum,
        idempotency_key=key
    )

    if success:
        if order_or_booking_id.startswith("BK-"):
            session_repo.update_booking_status(
                order_or_booking_id,
                BookingStatus.CONFIRMED,
                payment.transaction_reference
            )
        elif order_or_booking_id.startswith("ORD-"):
            session_repo.update_order_status(
                order_or_booking_id,
                OrderStatus.CONFIRMED,
                payment.transaction_reference
            )

    return {
        "status": "success" if success else "failed",
        "payment": payment.model_dump()
    }

def tool_get_order_confirmation(reference_id: str) -> Dict[str, Any]:
    res = tool_get_booking_status(reference_id)
    if res.get("status") == "error":
        return res
    return {
        "status": "success",
        "reference_id": reference_id,
        "details": res.get("record"),
        "disclaimer": "Simulated booking confirmation - for hackathon demonstration purposes only."
    }

