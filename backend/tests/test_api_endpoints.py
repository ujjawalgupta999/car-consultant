import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["total_listings"] >= 100
    assert data["categories_supported"] == 10

def test_session_lifecycle_and_scenario_a():
    # 1. Create session
    sess_res = client.post("/api/sessions")
    assert sess_res.status_code == 201
    session_id = sess_res.json()["session_id"]
    assert session_id.startswith("sess_")

    # 2. Send Scenario A message:
    # "I need an automatic SUV in Delhi for five days starting 15 December 2026. My budget is ₹3,000 per day."
    msg_payload = {
        "content": "I need an automatic SUV in Delhi for five days starting 15 December 2026. My budget is ₹3,000 per day."
    }
    msg_res = client.post(f"/api/sessions/{session_id}/messages", json=msg_payload)
    assert msg_res.status_code == 200
    data = msg_res.json()
    assert data["workflow_state"] == "RECOMMENDATIONS_READY"
    assert len(data["recommendations"]) > 0

    top_vehicle = data["recommendations"][0]["vehicle"]
    vehicle_id = top_vehicle["id"]

    # 3. Select vehicle via A2UI action
    action_payload = {
        "session_id": session_id,
        "surface_id": "test_surf",
        "action_id": "select_vehicle",
        "data": {"vehicle_id": vehicle_id}
    }
    action_res = client.post("/api/a2ui/action", json=action_payload)
    assert action_res.status_code == 200
    action_data = action_res.json()
    assert action_data["workflow_state"] == "VEHICLE_SELECTED"

    # 4. Calculate booking total
    calc_res = client.post("/api/bookings/calculate", json={
        "vehicle_id": vehicle_id,
        "duration_days": 5,
        "addon_ids": ["addon_insurance_zero_dep"]
    })
    assert calc_res.status_code == 200
    calc_data = calc_res.json()
    assert calc_data["total_amount"] > 0
    total_amount = calc_data["total_amount"]

    # 5. Create booking
    booking_payload = {
        "session_id": session_id,
        "vehicle_id": vehicle_id,
        "customer_name": "Rohan Sharma",
        "customer_email": "rohan@example.com",
        "customer_phone": "+91 98765 43210",
        "driver_license_number": "DL-1420110012345",
        "pickup_date": "2026-12-15",
        "return_date": "2026-12-20",
        "duration_days": 5,
        "pickup_location": "Delhi Airport T3",
        "return_location": "Delhi Airport T3",
        "addon_ids": ["addon_insurance_zero_dep"],
        "idempotency_key": "idemp_api_test_bk_01"
    }
    bk_res = client.post("/api/bookings", json=booking_payload)
    assert bk_res.status_code == 201
    bk_data = bk_res.json()
    booking_id = bk_data["booking_id"]
    assert bk_data["workflow_state"] == "CHECKOUT_READY"

    # 6. Simulate mock payment (Scenario Success)
    pay_payload = {
        "order_or_booking_id": booking_id,
        "amount": total_amount,
        "payment_method": "upi",
        "simulated_scenario": "success",
        "idempotency_key": "idemp_api_test_pay_01"
    }
    pay_res = client.post("/api/payments/mock", json=pay_payload)
    assert pay_res.status_code == 200
    pay_data = pay_res.json()
    assert pay_data["status"] == "SUCCESS"
    assert pay_data["workflow_state"] == "CONFIRMED"

    # 7. Check booking status is now CONFIRMED
    get_bk = client.get(f"/api/bookings/{booking_id}")
    assert get_bk.status_code == 200
    assert get_bk.json()["status"] == "CONFIRMED"
    assert get_bk.json()["payment_reference"] is not None

def test_scenario_d_payment_failure_and_retry():
    # Create booking
    sess_res = client.post("/api/sessions")
    session_id = sess_res.json()["session_id"]
    
    bk_res = client.post("/api/bookings", json={
        "session_id": session_id,
        "vehicle_id": "CAR-002",
        "customer_name": "Test User",
        "customer_email": "user@example.com",
        "customer_phone": "+91 98000 00000",
        "driver_license_number": "DL-000000",
        "pickup_date": "2026-12-01",
        "return_date": "2026-12-03",
        "duration_days": 2,
        "pickup_location": "Delhi",
        "return_location": "Delhi",
        "idempotency_key": "idemp_test_fail_bk"
    })
    booking_id = bk_res.json()["booking_id"]

    # 1. Simulate Payment Failure
    pay_fail_res = client.post("/api/payments/mock", json={
        "order_or_booking_id": booking_id,
        "amount": 5000.0,
        "payment_method": "card",
        "simulated_scenario": "failure",
        "idempotency_key": "idemp_test_fail_pay_1"
    })
    assert pay_fail_res.status_code == 200
    assert pay_fail_res.json()["status"] == "FAILED"
    assert pay_fail_res.json()["workflow_state"] == "PAYMENT_FAILED"

    # Verify booking is STILL unconfirmed (PENDING_PAYMENT)
    get_bk = client.get(f"/api/bookings/{booking_id}")
    assert get_bk.json()["status"] == "PENDING_PAYMENT"

    # 2. Retry with Success
    pay_retry_res = client.post("/api/payments/mock", json={
        "order_or_booking_id": booking_id,
        "amount": 5000.0,
        "payment_method": "upi",
        "simulated_scenario": "success",
        "idempotency_key": "idemp_test_retry_pay_2"
    })
    assert pay_retry_res.status_code == 200
    assert pay_retry_res.json()["status"] == "SUCCESS"
    assert pay_retry_res.json()["workflow_state"] == "CONFIRMED"

    # Verify booking is now CONFIRMED
    get_bk_after = client.get(f"/api/bookings/{booking_id}")
    assert get_bk_after.json()["status"] == "CONFIRMED"

