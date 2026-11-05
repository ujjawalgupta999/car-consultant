import uuid
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from ..models.session import Session, WorkflowState, ChatMessage, ChatRole
from ..models.preferences import UserPreferences, IntentType
from ..models.booking import RentalBooking, BookingStatus
from ..models.order import PurchaseOrder, OrderStatus

class SessionRepository:
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._messages: Dict[str, List[ChatMessage]] = {}
        self._bookings: Dict[str, RentalBooking] = {}
        self._booking_idempotency: Dict[str, RentalBooking] = {}
        self._orders: Dict[str, PurchaseOrder] = {}
        self._order_idempotency: Dict[str, PurchaseOrder] = {}

    def get_or_create_session(self, session_id: Optional[str] = None) -> Session:
        if not session_id or session_id not in self._sessions:
            sid = session_id or f"sess_{uuid.uuid4().hex[:8]}"
            prefs = UserPreferences(session_id=sid, intent=IntentType.RENT)
            session = Session(
                session_id=sid,
                workflow_state=WorkflowState.NEW,
                preferences=prefs
            )
            self._sessions[sid] = session
            self._messages[sid] = []
            return session
        return self._sessions[session_id]

    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def save_session(self, session: Session):
        session.updated_at = datetime.utcnow().isoformat() + "Z"
        self._sessions[session.session_id] = session

    def add_message(self, session_id: str, message: ChatMessage) -> ChatMessage:
        if session_id not in self._messages:
            self._messages[session_id] = []
        self._messages[session_id].append(message)
        return message

    def get_messages(self, session_id: str) -> List[ChatMessage]:
        return self._messages.get(session_id, [])

    # Rental Bookings
    def create_booking(self, booking: RentalBooking) -> RentalBooking:
        # Check idempotency
        if booking.idempotency_key in self._booking_idempotency:
            return self._booking_idempotency[booking.idempotency_key]
        self._bookings[booking.id] = booking
        self._booking_idempotency[booking.idempotency_key] = booking
        return booking

    def get_booking(self, booking_id: str) -> Optional[RentalBooking]:
        return self._bookings.get(booking_id)

    def update_booking_status(self, booking_id: str, status: BookingStatus, payment_ref: Optional[str] = None) -> Optional[RentalBooking]:
        b = self.get_booking(booking_id)
        if b:
            b.status = status
            if payment_ref:
                b.payment_reference = payment_ref
            b.updated_at = datetime.utcnow().isoformat() + "Z"
            self._bookings[booking_id] = b
            self._booking_idempotency[b.idempotency_key] = b
        return b

    # Purchase Orders
    def create_order(self, order: PurchaseOrder) -> PurchaseOrder:
        # Check idempotency
        if order.idempotency_key in self._order_idempotency:
            return self._order_idempotency[order.idempotency_key]
        self._orders[order.id] = order
        self._order_idempotency[order.idempotency_key] = order
        return order

    def get_order(self, order_id: str) -> Optional[PurchaseOrder]:
        return self._orders.get(order_id)

    def update_order_status(self, order_id: str, status: OrderStatus, payment_ref: Optional[str] = None) -> Optional[PurchaseOrder]:
        o = self.get_order(order_id)
        if o:
            o.status = status
            if payment_ref:
                o.payment_reference = payment_ref
            o.updated_at = datetime.utcnow().isoformat() + "Z"
            self._orders[order_id] = o
            self._order_idempotency[o.idempotency_key] = o
        return o

session_repo = SessionRepository()

