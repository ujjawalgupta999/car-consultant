import pytest
from backend.app.models.vehicle import Vehicle, VehicleCategory, VehicleCondition, FuelType, Transmission
from backend.app.models.payment import PaymentMethod, SimulatedScenario, PaymentStatus
from backend.app.services.pricing import calculate_rental_total, calculate_purchase_summary, ADDON_CATALOG
from backend.app.services.payment_simulator import payment_simulator

@pytest.fixture
def sample_vehicle():
    return Vehicle(
        id="CAR-TEST-01",
        brand="Hyundai",
        model="Creta",
        year=2025,
        category=VehicleCategory.SUV,
        condition=VehicleCondition.USED,
        fuel_type=FuelType.PETROL,
        transmission=Transmission.AUTOMATIC,
        seats=5,
        location="Delhi",
        rental_price_per_day=2800.0,
        purchase_price=1450000.0,
        available_for_rent=True,
        available_for_purchase=True,
        rating=4.7
    )

def test_calculate_rental_pricing(sample_vehicle):
    # 5 days, with Zero Dep (₹300/day)
    breakdown = calculate_rental_total(
        sample_vehicle,
        duration_days=5,
        addon_ids=["addon_insurance_zero_dep"]
    )
    
    expected_subtotal = 2800.0 * 5 # 14,000
    expected_addons = 300.0 * 5 # 1,500
    expected_taxable = 15500.0
    expected_tax = round(expected_taxable * 0.18, 2) # 2,790
    expected_total = expected_taxable + expected_tax # 18,290
    
    assert breakdown.subtotal == expected_subtotal
    assert breakdown.addons_total == expected_addons
    assert breakdown.taxes == expected_tax
    assert breakdown.total_amount == expected_total

def test_purchase_pricing_summary(sample_vehicle):
    summary = calculate_purchase_summary(sample_vehicle, deposit_amount=25000.0)
    assert summary["ex_showroom_price"] == 1450000.0
    assert summary["token_deposit"] == 25000.0
    assert summary["on_road_estimated"] > 1450000.0

def test_payment_idempotency():
    idemp_key = "test_key_unique_12345"
    success, payment1 = payment_simulator.process_mock_payment(
        order_or_booking_id="BK-99999",
        amount=18290.0,
        payment_method=PaymentMethod.UPI_SIMULATOR,
        simulated_scenario=SimulatedScenario.SUCCESS,
        idempotency_key=idemp_key
    )
    assert success is True
    assert payment1.status == PaymentStatus.SUCCESS
    
    # Second submission with the exact same idempotency key
    success2, payment2 = payment_simulator.process_mock_payment(
        order_or_booking_id="BK-99999",
        amount=18290.0,
        payment_method=PaymentMethod.UPI_SIMULATOR,
        simulated_scenario=SimulatedScenario.SUCCESS,
        idempotency_key=idemp_key
    )
    assert success2 is True
    assert payment1.id == payment2.id
    assert payment1.transaction_reference == payment2.transaction_reference

def test_payment_failure_scenario():
    idemp_key = "test_key_decline_777"
    success, payment = payment_simulator.process_mock_payment(
        order_or_booking_id="BK-88888",
        amount=18290.0,
        payment_method=PaymentMethod.CARD_SIMULATOR,
        simulated_scenario=SimulatedScenario.FAILURE,
        idempotency_key=idemp_key
    )
    assert success is False
    assert payment.status == PaymentStatus.FAILED
    assert "Decline" in payment.error_message

