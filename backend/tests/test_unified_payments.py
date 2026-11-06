import pytest
from backend.app.repositories.user_data_repo import user_data_repo
from backend.app.repositories.session import session_repo
from backend.app.repositories.marketplace import marketplace_repo
from backend.app.services.transaction_service import transaction_service
from backend.app.models.payment import PaymentStatus
from backend.app.models.session import WorkflowState
from backend.app.models.preferences import IntentType, UserPreferences
from backend.app.agents.interview import AdaptiveInterviewAgent

@pytest.fixture(autouse=True)
def reset_test_state():
    """Reset repository in-memory state before each test."""
    user_data_repo._payments.clear()
    user_data_repo._payments_by_order.clear()
    user_data_repo._payments_by_idemp.clear()
    user_data_repo._purchases.clear()
    user_data_repo._purchases_by_order.clear()
    user_data_repo._rentals.clear()
    user_data_repo._rentals_by_order.clear()
    user_data_repo._listings.clear()
    user_data_repo._owned_vehicles.clear()
    user_data_repo._seed_initial_demo_data()

def test_buy_transaction_flow_and_idempotency():
    user_id = "usr_demo_01"
    order_id = "ORD-TEST-001"
    vehicle_id = "CAR-001"
    amount = 1450000.0

    # 1. Confirm mock payment for BUY order
    ok, payment, linked_entity, _, _, _ = transaction_service.process_payment_records(
        order_or_booking_id=order_id,
        amount=amount,
        payment_method="UPI",
        user_id=user_id,
        idempotency_key="idemp_buy_001",
        simulated_scenario="SUCCESS"
    )

    assert ok is True
    assert payment.paymentStatus == PaymentStatus.SUCCESS
    assert payment.orderId == order_id
    assert payment.transactionType == "BUY"
    assert payment.vehicleId == vehicle_id
    assert payment.amount == amount

    # 2. Verify Purchase record created in UserDataRepository
    purchase = user_data_repo.get_purchase_by_order(order_id)
    assert purchase is not None
    assert purchase.purchaseStatus == "CONFIRMED"
    assert purchase.paymentStatus == "SUCCESS"
    assert purchase.paymentId == payment.id
    assert purchase.vehicleSnapshot.brand != ""

    # 3. Verify vehicle added to owned vehicles
    owned = user_data_repo.get_user_owned_vehicles(user_id)
    platform_vehicles = [v for v in owned if v.source == "PURCHASED_PLATFORM"]
    assert any(v.vehicleId == vehicle_id for v in platform_vehicles)

    # 4. Strict idempotency check: repeat call with same idempotency key returns cached payment
    ok2, dup_payment, _, _, _, _ = transaction_service.process_payment_records(
        order_or_booking_id=order_id,
        amount=amount,
        payment_method="UPI",
        user_id=user_id,
        idempotency_key="idemp_buy_001",
        simulated_scenario="SUCCESS"
    )
    assert ok2 is True
    assert dup_payment.id == payment.id

    # Ensure no duplicate purchases were created
    all_purchases = user_data_repo.get_user_purchases(user_id)
    assert len([p for p in all_purchases if p.orderId == order_id]) == 1

def test_rent_transaction_flow():
    from backend.app.models.booking import RentalBooking, BookingStatus
    user_id = "usr_demo_01"
    order_id = "BK-TEST-RENT-002"
    vehicle_id = "CAR-002"
    amount = 18500.0

    booking = RentalBooking(
        id=order_id,
        session_id="sess_test_rent",
        vehicle_id=vehicle_id,
        customer_name="Demo User",
        customer_email="demo@auramotors.com",
        customer_phone="+91 98765 43210",
        driver_license_number="DL-12345",
        pickup_date="2026-05-01",
        return_date="2026-05-05",
        duration_days=4,
        pickup_location="Delhi NCR",
        return_location="Delhi NCR",
        base_rate=3500.0,
        subtotal=14000.0,
        taxes=2520.0,
        total_amount=amount,
        currency="INR",
        status=BookingStatus.PENDING_PAYMENT,
        idempotency_key="idemp_bk_rent_002"
    )
    session_repo.create_booking(booking)

    # 1. Confirm mock payment for RENT booking
    ok, payment, linked_entity, _, _, _ = transaction_service.process_payment_records(
        order_or_booking_id=order_id,
        amount=amount,
        payment_method="CARD",
        user_id=user_id,
        idempotency_key="idemp_rent_002",
        simulated_scenario="SUCCESS"
    )

    assert ok is True
    assert payment.paymentStatus == PaymentStatus.SUCCESS
    assert payment.orderId == order_id
    assert payment.transactionType == "RENT"
    assert payment.vehicleId == vehicle_id

    # 2. Verify dedicated Rental record created in UserDataRepository
    rental = user_data_repo.get_rental_by_order(order_id)
    assert rental is not None
    assert rental.rentalStatus == "CONFIRMED"
    assert rental.paymentStatus == "SUCCESS"
    assert rental.paymentId == payment.id
    assert rental.rentalAmount == amount

def test_failed_and_declined_payment_flow():
    user_id = "usr_demo_01"
    order_id = "ORD-FAIL-003"
    vehicle_id = "CAR-003"
    amount = 500000.0

    # 1. Simulate declined payment
    ok, payment, _, _, error_msg, _ = transaction_service.process_payment_records(
        order_or_booking_id=order_id,
        amount=amount,
        payment_method="NET_BANKING",
        user_id=user_id,
        idempotency_key="idemp_fail_003",
        simulated_scenario="FAILURE"
    )

    assert ok is False
    assert payment.paymentStatus == PaymentStatus.FAILED
    assert "Decline" in (payment.errorMessage or "")

    # 2. Verify no purchase was created
    purchase = user_data_repo.get_purchase_by_order(order_id)
    assert purchase is None

def test_payment_queries_and_filters():
    user_id = "usr_demo_01"

    # Seed 1 buy, 1 rent, 1 failed
    transaction_service.process_payment_records(
        order_or_booking_id="ORD-Q1", amount=1200000.0, payment_method="UPI",
        user_id=user_id, idempotency_key="idemp_q1", simulated_scenario="SUCCESS"
    )
    transaction_service.process_payment_records(
        order_or_booking_id="BK-Q2", amount=15000.0, payment_method="CARD",
        user_id=user_id, idempotency_key="idemp_q2", simulated_scenario="SUCCESS"
    )
    transaction_service.process_payment_records(
        order_or_booking_id="ORD-Q3", amount=900000.0, payment_method="UPI",
        user_id=user_id, idempotency_key="idemp_q3", simulated_scenario="FAILURE"
    )

    # Query all
    all_p = user_data_repo.get_user_payments(user_id)
    assert len(all_p) >= 3

    # Filter by status = SUCCESS
    success_p = user_data_repo.get_user_payments(user_id, status="SUCCESS")
    assert all(p.paymentStatus == PaymentStatus.SUCCESS for p in success_p)

    # Filter by transaction_type = RENT
    rent_p = user_data_repo.get_user_payments(user_id, transaction_type="RENT")
    assert all(p.transactionType == "RENT" for p in rent_p)

    # Dashboard summary
    summary = user_data_repo.get_dashboard_summary(user_id)
    assert summary["total_payments"] >= 3
    assert summary["total_settled_payments_inr"] > 0

def test_professional_ai_response_formatting():
    session_id = "sess_ai_format_01"

    # Test 1: "I want to rent a sedan" -> asks only ONE question (city) without robotic prefix
    prefs = UserPreferences(session_id=session_id)
    updated_prefs, _ = AdaptiveInterviewAgent.extract_preferences("I want to rent a sedan", prefs)
    question = AdaptiveInterviewAgent.generate_followup_question(updated_prefs)

    # Verify no robotic "Got it: intent: RENT..." prefix
    assert not question.startswith("Got it: intent:")
    assert "Which city will you be driving in" in question
    # Verify it asks ONE question, not all 3 at once
    assert "What is your approximate daily" not in question

    # Test 2: User provides city: "Delhi" -> next question asks daily rental budget
    updated_prefs, _ = AdaptiveInterviewAgent.extract_preferences("Delhi", updated_prefs)
    question_2 = AdaptiveInterviewAgent.generate_followup_question(updated_prefs)
    assert "daily rental budget" in question_2.lower()
    assert "city will you be driving in" not in question_2

    # Test 3: "I want to buy an SUV under 20 lakh" -> extracts budget and style
    buy_prefs = UserPreferences(session_id="sess_buy_01")
    updated_buy_prefs, _ = AdaptiveInterviewAgent.extract_preferences("I want to buy an SUV under 20 lakh", buy_prefs)
    assert updated_buy_prefs.intent == IntentType.BUY
    assert updated_buy_prefs.category.value == "SUV"
    assert updated_buy_prefs.budget_max == 2000000.0
    # Next question asks only for city
    question_buy = AdaptiveInterviewAgent.generate_followup_question(updated_buy_prefs)
    assert "city" in question_buy.lower()
    assert "budget" not in question_buy.lower()
