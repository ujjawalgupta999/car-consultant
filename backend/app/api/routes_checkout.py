from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from ..services.transaction_service import transaction_service
from ..repositories.session import session_repo
from ..repositories.marketplace import marketplace_repo
from ..api.routes_auth import resolve_user_id

router = APIRouter(prefix="/api/checkout", tags=["Checkout"])

class CheckoutInitiationRequest(BaseModel):
    vehicle_id: str
    intent: str = "buy" # "buy" or "rent"
    customer_name: str
    customer_email: str
    customer_phone: str
    delivery_city: Optional[str] = "Delhi NCR"
    pickup_date: Optional[str] = None
    return_date: Optional[str] = None
    duration_days: int = 5
    session_id: Optional[str] = None

@router.post("")
def initiate_checkout(req: CheckoutInitiationRequest, authorization: Optional[str] = Header(None)):
    user_id = resolve_user_id(authorization)
    try:
        session_data = transaction_service.create_checkout_session(
            vehicle_id=req.vehicle_id,
            intent=req.intent,
            user_id=user_id,
            customer_name=req.customer_name,
            customer_email=req.customer_email,
            customer_phone=req.customer_phone,
            delivery_city=req.delivery_city,
            pickup_date=req.pickup_date,
            return_date=req.return_date,
            duration_days=req.duration_days,
            session_id=req.session_id
        )
        return session_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{order_id}")
def get_checkout_details(order_id: str, authorization: Optional[str] = Header(None)):
    """Retrieves full order summary for the checkout page."""
    user_id = resolve_user_id(authorization)

    # Check if order or booking exists
    if order_id.startswith("BK-") or order_id.startswith("bk_"):
        booking = session_repo.get_booking(order_id)
        if not booking:
            # Check rental records
            rental = next((r for r in session_repo._bookings.values() if r.id == order_id), None)
            if not rental:
                raise HTTPException(status_code=404, detail="Rental order not found")
            booking = rental
        vehicle = marketplace_repo.get_vehicle_by_id(booking.vehicle_id)
        return {
            "orderId": order_id,
            "transactionType": "RENT",
            "vehicleId": booking.vehicle_id,
            "vehicle": vehicle.model_dump() if vehicle else None,
            "pricing": {
                "dailyRate": booking.base_rate,
                "durationDays": booking.duration_days,
                "subtotal": booking.subtotal,
                "taxes": booking.taxes,
                "securityDeposit": 5000.0,
                "totalAmount": booking.total_amount,
                "currency": booking.currency
            },
            "rentalDetails": {
                "pickupDate": booking.pickup_date,
                "returnDate": booking.return_date,
                "durationDays": booking.duration_days,
                "pickupLocation": booking.pickup_location,
                "returnLocation": booking.return_location
            },
            "customer": {
                "name": booking.customer_name,
                "email": booking.customer_email,
                "phone": booking.customer_phone
            },
            "status": booking.status.value
        }
    else:
        order = session_repo.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        vehicle = marketplace_repo.get_vehicle_by_id(order.vehicle_id)
        return {
            "orderId": order_id,
            "transactionType": "BUY",
            "vehicleId": order.vehicle_id,
            "vehicle": vehicle.model_dump() if vehicle else None,
            "pricing": {
                "purchasePrice": order.purchase_price,
                "depositAmount": order.deposit_amount,
                "registrationAndInsurance": 85000.0,
                "totalAmount": order.deposit_amount,
                "currency": "INR"
            },
            "customer": {
                "name": order.customer_name,
                "email": order.customer_email,
                "phone": order.customer_phone,
                "city": order.delivery_city
            },
            "status": order.status.value
        }

