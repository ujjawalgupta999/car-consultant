import uuid
from typing import Dict, Optional, Tuple
from datetime import datetime
from ..models.payment import MockPayment, PaymentMethod, SimulatedScenario, PaymentStatus

class PaymentSimulator:
    def __init__(self):
        # In-memory store for idempotency keys -> MockPayment
        self._idempotency_store: Dict[str, MockPayment] = {}
        # Store for payment_id -> MockPayment
        self._payments: Dict[str, MockPayment] = {}

    def process_mock_payment(
        self,
        order_or_booking_id: str,
        amount: float,
        payment_method: PaymentMethod,
        simulated_scenario: SimulatedScenario,
        idempotency_key: str,
        currency: str = "INR"
    ) -> Tuple[bool, MockPayment]:
        # 1. Idempotency Check
        if idempotency_key in self._idempotency_store:
            cached = self._idempotency_store[idempotency_key]
            return (cached.status == PaymentStatus.SUCCESS), cached

        # 2. Simulate Scenario
        payment_id = f"PAY-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        txn_ref = f"TXN-MOCK-{uuid.uuid4().hex[:8].upper()}"

        disclaimer = "SIMULATED TEST TRANSACTION - NO REAL FUNDS TRANSFERRED"

        if simulated_scenario == SimulatedScenario.SUCCESS:
            payment = MockPayment(
                id=payment_id,
                transaction_reference=txn_ref,
                order_or_booking_id=order_or_booking_id,
                amount=amount,
                currency=currency,
                payment_method=payment_method,
                simulated_scenario=simulated_scenario,
                status=PaymentStatus.SUCCESS,
                idempotency_key=idempotency_key,
                gateway_metadata={
                    "auth_code": f"AUTH_{uuid.uuid4().hex[:6].upper()}",
                    "simulated_provider": payment_method.value,
                    "disclaimer": disclaimer,
                    "processed_at": datetime.utcnow().isoformat() + "Z"
                }
            )
            self._idempotency_store[idempotency_key] = payment
            self._payments[payment_id] = payment
            return True, payment

        elif simulated_scenario == SimulatedScenario.FAILURE:
            payment = MockPayment(
                id=payment_id,
                transaction_reference=txn_ref,
                order_or_booking_id=order_or_booking_id,
                amount=amount,
                currency=currency,
                payment_method=payment_method,
                simulated_scenario=simulated_scenario,
                status=PaymentStatus.FAILED,
                idempotency_key=idempotency_key,
                error_message="Simulated Bank Decline: Insufficient mock sandbox balance.",
                gateway_metadata={
                    "error_code": "DECLINED_INSUFFICIENT_MOCK_FUNDS",
                    "disclaimer": disclaimer,
                    "processed_at": datetime.utcnow().isoformat() + "Z"
                }
            )
            self._idempotency_store[idempotency_key] = payment
            self._payments[payment_id] = payment
            return False, payment

        else: # TIMEOUT
            payment = MockPayment(
                id=payment_id,
                transaction_reference=txn_ref,
                order_or_booking_id=order_or_booking_id,
                amount=amount,
                currency=currency,
                payment_method=payment_method,
                simulated_scenario=simulated_scenario,
                status=PaymentStatus.FAILED,
                idempotency_key=idempotency_key,
                error_message="Simulated Gateway Timeout: Bank partner took too long to respond. Please retry.",
                gateway_metadata={
                    "error_code": "GATEWAY_TIMEOUT",
                    "disclaimer": disclaimer,
                    "processed_at": datetime.utcnow().isoformat() + "Z"
                }
            )
            self._idempotency_store[idempotency_key] = payment
            self._payments[payment_id] = payment
            return False, payment

    def get_payment(self, payment_id: str) -> Optional[MockPayment]:
        return self._payments.get(payment_id)

payment_simulator = PaymentSimulator()

