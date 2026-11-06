import uuid
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from ..models.payment import PaymentRecord, PaymentStatus, TransactionType, PaymentMethod, SimulatedScenario
from ..models.purchase import PurchaseRecord
from ..models.rental import RentalRecord
from ..models.booking import RentalBooking, BookingStatus
from ..models.order import PurchaseOrder, OrderStatus
from ..models.session import WorkflowState
from ..repositories.session import session_repo
from ..repositories.user_data_repo import user_data_repo
from ..repositories.marketplace import marketplace_repo

logger = logging.getLogger("car_consultant.transaction_service")

class TransactionService:
    def __init__(self):
        pass

    def process_payment_records(
        self,
        order_or_booking_id: str,
        amount: float,
        payment_method: str = "upi",
        simulated_scenario: str = "success",
        idempotency_key: Optional[str] = None,
        user_id: Optional[str] = None,
        currency: str = "INR"
    ) -> Tuple[bool, PaymentRecord, Optional[Any], Optional[str], Optional[str], str]:
        """
        Synchronous authoritative payment processing and record generation.
        Returns: (success, payment, linked_entity, target_session_id, error_msg, vehicle_id)
        """
        target_user = user_id or "usr_demo_01"
        key = idempotency_key or f"idemp_pay_{order_or_booking_id}"

        # 1. Strict Idempotency Check
        existing_payment = user_data_repo._payments_by_idemp.get(key) or user_data_repo.get_payment_by_order(order_or_booking_id, target_user)
        if existing_payment and existing_payment.paymentStatus == PaymentStatus.SUCCESS:
            logger.info(f"Idempotent payment hit for order '{order_or_booking_id}' (ref: {existing_payment.transactionId})")
            linked_entity = None
            if existing_payment.transactionType == TransactionType.BUY:
                linked_entity = user_data_repo._purchases_by_order.get(order_or_booking_id)
            else:
                linked_entity = user_data_repo._rentals_by_order.get(order_or_booking_id)
            return True, existing_payment, linked_entity, None, None, existing_payment.vehicleId

        is_rent = order_or_booking_id.startswith("BK-") or order_or_booking_id.startswith("bk_") or order_or_booking_id.startswith("BOOK-")
        txn_type = TransactionType.RENT if is_rent else TransactionType.BUY

        # Find target vehicle ID from booking or order
        vehicle_id = "CAR-001"
        target_session_id = None

        if is_rent:
            booking = session_repo.get_booking(order_or_booking_id)
            if booking:
                vehicle_id = booking.vehicle_id
                target_session_id = booking.session_id
        else:
            order = session_repo.get_order(order_or_booking_id)
            if order:
                vehicle_id = order.vehicle_id
                target_session_id = order.session_id

        payment_id = f"PAY-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        txn_ref = f"TXN-MOCK-{uuid.uuid4().hex[:8].upper()}"
        disclaimer = "SIMULATED TEST TRANSACTION - NO REAL FUNDS TRANSFERRED - AMULATE HACKATHON 2026"
        scen_lower = (simulated_scenario or "success").lower()

        if scen_lower == "success":
            payment = PaymentRecord(
                id=payment_id,
                userId=target_user,
                orderId=order_or_booking_id,
                transactionId=txn_ref,
                vehicleId=vehicle_id,
                transactionType=txn_type,
                amount=amount,
                currency=currency,
                paymentMethod=payment_method,
                paymentStatus=PaymentStatus.SUCCESS,
                paymentProvider="MOCK_PAYMENT",
                paymentReference=txn_ref,
                idempotencyKey=key,
                gatewayMetadata={
                    "auth_code": f"AUTH_{uuid.uuid4().hex[:6].upper()}",
                    "simulated_provider": payment_method,
                    "disclaimer": disclaimer,
                    "processed_at": datetime.utcnow().isoformat() + "Z"
                },
                createdAt=datetime.utcnow().isoformat() + "Z",
                updatedAt=datetime.utcnow().isoformat() + "Z"
            )
            user_data_repo.record_payment(payment, idempotency_key=key)

            linked_entity = None
            if is_rent:
                session_repo.update_booking_status(order_or_booking_id, BookingStatus.CONFIRMED, txn_ref)
                linked_entity = user_data_repo.record_rental(
                    booking_id=order_or_booking_id,
                    transaction_reference=txn_ref,
                    user_id=target_user,
                    payment_id=payment.id
                )
            else:
                session_repo.update_order_status(order_or_booking_id, OrderStatus.CONFIRMED, txn_ref)
                linked_entity = user_data_repo.record_purchase(
                    order_id=order_or_booking_id,
                    transaction_reference=txn_ref,
                    user_id=target_user,
                    payment_id=payment.id
                )

            if target_session_id:
                session = session_repo.get_session(target_session_id)
                if session:
                    session.workflow_state = WorkflowState.CONFIRMED
                    session_repo.save_session(session)

            return True, payment, linked_entity, target_session_id, None, vehicle_id

        else:
            error_msg = (
                "Simulated Bank Decline: Insufficient mock sandbox balance."
                if scen_lower == "failure"
                else "Simulated Gateway Timeout: Bank partner took too long to respond. Please retry."
            )
            payment = PaymentRecord(
                id=payment_id,
                userId=target_user,
                orderId=order_or_booking_id,
                transactionId=txn_ref,
                vehicleId=vehicle_id,
                transactionType=txn_type,
                amount=amount,
                currency=currency,
                paymentMethod=payment_method,
                paymentStatus=PaymentStatus.FAILED,
                paymentProvider="MOCK_PAYMENT",
                paymentReference=txn_ref,
                errorMessage=error_msg,
                idempotencyKey=key,
                gatewayMetadata={
                    "error_code": "ERR_MOCK_DECLINE" if scen_lower == "failure" else "ERR_MOCK_TIMEOUT",
                    "disclaimer": disclaimer,
                    "failed_at": datetime.utcnow().isoformat() + "Z"
                },
                createdAt=datetime.utcnow().isoformat() + "Z",
                updatedAt=datetime.utcnow().isoformat() + "Z"
            )
            user_data_repo.record_payment(payment, idempotency_key=key)

            if target_session_id:
                session = session_repo.get_session(target_session_id)
                if session:
                    session.workflow_state = WorkflowState.PAYMENT_FAILED
                    session_repo.save_session(session)

            return False, payment, None, target_session_id, error_msg, vehicle_id

    async def confirm_mock_payment(
        self,
        order_or_booking_id: str,
        amount: float,
        payment_method: str = "upi",
        simulated_scenario: str = "success",
        idempotency_key: Optional[str] = None,
        user_id: Optional[str] = None,
        currency: str = "INR"
    ) -> Tuple[bool, PaymentRecord, Optional[Any]]:
        """
        Processes a mock payment idempotently and creates authoritative Purchase or Rental records.
        Broadcasts real-time events to active sessions so the website and AI consultant stay synchronized.
        """
        target_user = user_id or "usr_demo_01"
        success, payment, linked_entity, target_session_id, error_msg, vehicle_id = self.process_payment_records(
            order_or_booking_id=order_or_booking_id,
            amount=amount,
            payment_method=payment_method,
            simulated_scenario=simulated_scenario,
            idempotency_key=idempotency_key,
            user_id=target_user,
            currency=currency
        )

        event_payload = {
            "type": "PAYMENT_STATUS_UPDATED",
            "userId": target_user,
            "paymentId": payment.id,
            "orderId": order_or_booking_id,
            "status": "SUCCESS" if success else "FAILED",
            "transactionType": payment.transactionType.value,
            "amount": amount,
            "transactionReference": payment.paymentReference,
            "vehicleId": vehicle_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        if not success:
            event_payload["errorMessage"] = error_msg

        await self._broadcast_payment_event(event_payload, target_session_id)
        return success, payment, linked_entity

    async def _broadcast_payment_event(self, event_data: Dict[str, Any], session_id: Optional[str] = None):
        """Dispatches payment event to all active sessions so website & consultant stay synchronized."""
        from ..orchestration.orchestrator import orchestration_engine
        try:
            if session_id:
                await orchestration_engine.emit_event(session_id, "payment_status_updated", event_data)
            for s_id in list(orchestration_engine._event_subscribers.keys()):
                if s_id != session_id:
                    await orchestration_engine.emit_event(s_id, "payment_status_updated", event_data)
        except Exception as e:
            logger.warning(f"Error broadcasting payment event: {e}")

    def get_payment(self, payment_id: str, user_id: Optional[str] = None) -> Optional[PaymentRecord]:
        return user_data_repo.get_payment_by_id(payment_id, user_id)

    def get_payment_by_order(self, order_id: str, user_id: Optional[str] = None) -> Optional[PaymentRecord]:
        return user_data_repo.get_payment_by_order(order_id, user_id)

    def get_user_payments(
        self,
        user_id: str,
        status: Optional[str] = None,
        transaction_type: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = "date_desc"
    ) -> List[PaymentRecord]:
        return user_data_repo.get_user_payments(
            user_id=user_id,
            status=status,
            transaction_type=transaction_type,
            search=search,
            sort_by=sort_by
        )

    def recheck_payment(self, payment_id: str, user_id: Optional[str] = None) -> Optional[PaymentRecord]:
        """Checks authoritative status of a transaction."""
        payment = user_data_repo.get_payment_by_id(payment_id, user_id)
        if not payment:
            return None
        if payment.paymentStatus in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
            payment.paymentStatus = PaymentStatus.SUCCESS
            payment.updatedAt = datetime.utcnow().isoformat() + "Z"
            user_data_repo.record_payment(payment)
        return payment

    def create_checkout_session(
        self,
        vehicle_id: str,
        intent: str, # "buy" or "rent"
        user_id: str,
        customer_name: str,
        customer_email: str,
        customer_phone: str,
        delivery_city: Optional[str] = None,
        pickup_date: Optional[str] = None,
        return_date: Optional[str] = None,
        duration_days: int = 5,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Centralized endpoint for creating a checkout session.
        Shared by vehicle details page, Buy Cars, Rent Cars, and Aura AI Consultant.
        """
        vehicle = marketplace_repo.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle '{vehicle_id}' not found.")

        is_rent = (intent.lower() == "rent")
        sess_id = session_id or f"sess_{uuid.uuid4().hex[:8]}"

        if is_rent:
            daily_rate = vehicle.rental_price_per_day
            subtotal = daily_rate * duration_days
            taxes = subtotal * 0.18
            security_deposit = 5000.0
            total_amount = subtotal + taxes

            booking_id = f"BK-2026-{uuid.uuid4().hex[:6].upper()}"
            booking = RentalBooking(
                id=booking_id,
                session_id=sess_id,
                vehicle_id=vehicle_id,
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                driver_license_number="DL-VERIFIED-HACKATHON",
                pickup_date=pickup_date or datetime.utcnow().strftime("%Y-%m-%d"),
                return_date=return_date or datetime.utcnow().strftime("%Y-%m-%d"),
                duration_days=duration_days,
                pickup_location=delivery_city or vehicle.location or "Delhi NCR",
                return_location=delivery_city or vehicle.location or "Delhi NCR",
                base_rate=daily_rate,
                subtotal=subtotal,
                taxes=taxes,
                total_amount=total_amount,
                currency="INR",
                status=BookingStatus.PENDING_PAYMENT,
                idempotency_key=f"idemp_bk_{booking_id}"
            )
            session_repo.create_booking(booking)

            return {
                "orderId": booking_id,
                "transactionType": "RENT",
                "vehicleId": vehicle.id,
                "vehicle": vehicle.model_dump(),
                "pricing": {
                    "dailyRate": daily_rate,
                    "durationDays": duration_days,
                    "subtotal": subtotal,
                    "taxes": taxes,
                    "securityDeposit": security_deposit,
                    "totalAmount": total_amount,
                    "currency": "INR"
                },
                "customer": {
                    "name": customer_name,
                    "email": customer_email,
                    "phone": customer_phone,
                    "city": delivery_city or vehicle.location or "Delhi NCR"
                },
                "status": "PENDING"
            }
        else:
            deposit_amount = 25000.0
            order_id = f"ORD-2026-{uuid.uuid4().hex[:6].upper()}"
            order = PurchaseOrder(
                id=order_id,
                session_id=sess_id,
                vehicle_id=vehicle_id,
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                pan_or_id="ABCDE1234F",
                delivery_city=delivery_city or vehicle.location or "Delhi NCR",
                purchase_price=vehicle.purchase_price,
                deposit_amount=deposit_amount,
                financing_selected=False,
                status=OrderStatus.PENDING_PAYMENT,
                idempotency_key=f"idemp_ord_{order_id}"
            )
            session_repo.create_order(order)

            return {
                "orderId": order_id,
                "transactionType": "BUY",
                "vehicleId": vehicle.id,
                "vehicle": vehicle.model_dump(),
                "pricing": {
                    "purchasePrice": vehicle.purchase_price,
                    "depositAmount": deposit_amount,
                    "registrationAndInsurance": 85000.0,
                    "totalAmount": deposit_amount,
                    "currency": "INR"
                },
                "customer": {
                    "name": customer_name,
                    "email": customer_email,
                    "phone": customer_phone,
                    "city": delivery_city or vehicle.location or "Delhi NCR"
                },
                "status": "PENDING"
            }

transaction_service = TransactionService()
