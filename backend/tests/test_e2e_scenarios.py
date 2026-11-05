import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_scenario_a_rental_journey():
    """
    Scenario A: Rental
    User: 'I need an automatic SUV in Delhi for five days starting 15 December 2026. My budget is ₹3,000 per day.'
    """
    # 1. Create session
    sess_res = client.post("/api/sessions")
    session_id = sess_res.json()["session_id"]

    # 2. User sends rental query
    user_msg = "I need an automatic SUV in Delhi for five days starting 15 December 2026. My budget is ₹3,000 per day."
    turn_res = client.post(f"/api/sessions/{session_id}/messages", json={"content": user_msg})
    assert turn_res.status_code == 200
    turn_data = turn_res.json()

    assert turn_data["workflow_state"] == "RECOMMENDATIONS_READY"
    assert len(turn_data["recommendations"]) > 0

    top_rec = turn_data["recommendations"][0]
    assert top_rec["vehicle"]["category"] == "SUV"
    assert top_rec["vehicle"]["transmission"] == "automatic"
    assert top_rec["vehicle"]["rental_price_per_day"] <= 3000.0
    assert top_rec["match_score"] >= 75.0
    assert len(top_rec["positive_matches"]) > 0

    selected_vehicle_id = top_rec["vehicle"]["id"]

    # 3. User selects vehicle via A2UI
    select_res = client.post("/api/a2ui/action", json={
        "session_id": session_id,
        "surface_id": turn_data["a2ui_surfaces"][0],
        "action_id": "select_vehicle",
        "data": {"vehicle_id": selected_vehicle_id}
    })
    assert select_res.status_code == 200
    assert select_res.json()["workflow_state"] == "VEHICLE_SELECTED"

    # 4. Booking MCP App calculates authoritative total
    calc_res = client.post("/api/bookings/calculate", json={
        "vehicle_id": selected_vehicle_id,
        "duration_days": 5,
        "addon_ids": ["addon_insurance_zero_dep"]
    })
    assert calc_res.status_code == 200
    calc_data = calc_res.json()
    assert calc_data["total_amount"] > 0
    total_amount = calc_data["total_amount"]

    # 5. Booking MCP App submits verified booking
    booking_res = client.post("/api/bookings", json={
        "session_id": session_id,
        "vehicle_id": selected_vehicle_id,
        "customer_name": "Rohan Sharma",
        "customer_email": "rohan.sharma@example.com",
        "customer_phone": "+91 98765 43210",
        "driver_license_number": "DL-1420110012345",
        "pickup_date": "2026-12-15",
        "return_date": "2026-12-20",
        "duration_days": 5,
        "pickup_location": "Delhi Airport T3",
        "return_location": "Delhi Airport T3",
        "addon_ids": ["addon_insurance_zero_dep"],
        "idempotency_key": "idemp_scen_a_booking"
    })
    assert booking_res.status_code == 201
    booking_id = booking_res.json()["booking_id"]
    assert booking_res.json()["booking"]["status"] == "PENDING_PAYMENT"

    # 6. Checkout MCP App simulates successful payment
    pay_res = client.post("/api/payments/mock", json={
        "order_or_booking_id": booking_id,
        "amount": total_amount,
        "payment_method": "upi",
        "simulated_scenario": "success",
        "idempotency_key": "idemp_scen_a_pay"
    })
    assert pay_res.status_code == 200
    pay_data = pay_res.json()
    assert pay_data["status"] == "SUCCESS"
    assert pay_data["workflow_state"] == "CONFIRMED"

    # 7. Final status verification
    conf_res = client.get(f"/api/bookings/{booking_id}")
    assert conf_res.status_code == 200
    assert conf_res.json()["status"] == "CONFIRMED"
    assert conf_res.json()["payment_reference"] is not None

def test_scenario_b_purchase_journey():
    """
    Scenario B: Purchase
    User: 'I want to buy a used automatic SUV in Delhi with a maximum budget of ₹15 lakh.'
    """
    sess_res = client.post("/api/sessions")
    session_id = sess_res.json()["session_id"]

    user_msg = "I want to buy a used automatic SUV in Delhi with a maximum budget of ₹15 lakh."
    turn_res = client.post(f"/api/sessions/{session_id}/messages", json={"content": user_msg})
    assert turn_res.status_code == 200
    turn_data = turn_res.json()

    assert turn_data["workflow_state"] == "RECOMMENDATIONS_READY"
    assert len(turn_data["recommendations"]) > 0

    top_rec = turn_data["recommendations"][0]
    assert top_rec["vehicle"]["available_for_purchase"] is True
    assert top_rec["vehicle"]["purchase_price"] <= 1500000.0

    selected_vehicle_id = top_rec["vehicle"]["id"]

    # Select vehicle
    client.post("/api/a2ui/action", json={
        "session_id": session_id,
        "surface_id": turn_data["a2ui_surfaces"][0],
        "action_id": "select_vehicle",
        "data": {"vehicle_id": selected_vehicle_id}
    })

    # Purchase reservation order
    order_res = client.post("/api/orders", json={
        "session_id": session_id,
        "vehicle_id": selected_vehicle_id,
        "customer_name": "Priya Patel",
        "customer_email": "priya.patel@example.com",
        "customer_phone": "+91 98111 22334",
        "pan_or_id": "ABCDE1234F",
        "delivery_city": "Delhi",
        "deposit_amount": 25000.0,
        "financing_selected": True,
        "idempotency_key": "idemp_scen_b_order"
    })
    assert order_res.status_code == 201
    order_id = order_res.json()["order_id"]
    assert order_res.json()["order"]["status"] == "PENDING_PAYMENT"

    # Mock payment for token deposit
    pay_res = client.post("/api/payments/mock", json={
        "order_or_booking_id": order_id,
        "amount": 25000.0,
        "payment_method": "card",
        "simulated_scenario": "success",
        "idempotency_key": "idemp_scen_b_pay"
    })
    assert pay_res.status_code == 200
    assert pay_res.json()["status"] == "SUCCESS"

    # Verify order is CONFIRMED
    get_order = client.get(f"/api/orders/{order_id}")
    assert get_order.json()["status"] == "CONFIRMED"

def test_scenario_c_zero_results_and_relaxation():
    """
    Scenario C: No matching vehicles
    User: 'I need an automatic convertible in Delhi for 5 days starting 15 December 2026 with a daily budget of ₹500.'
    """
    sess_res = client.post("/api/sessions")
    session_id = sess_res.json()["session_id"]

    user_msg = "I need an automatic convertible in Delhi for 5 days starting 15 December 2026 with a daily budget of ₹500."
    turn_res = client.post(f"/api/sessions/{session_id}/messages", json={"content": user_msg})
    assert turn_res.status_code == 200
    turn_data = turn_res.json()

    assert len(turn_data["recommendations"]) == 0
    assert "diagnostics" in turn_data
    diag = turn_data["diagnostics"]
    assert len(diag["binding_constraints"]) > 0
    assert "500" in diag["binding_constraints"][0] or "Convertible" in diag["binding_constraints"][0]
    assert len(diag["recommended_relaxations"]) > 0

def test_scenario_d_payment_failure_recovery_and_idempotency():
    """
    Scenario D: Failed payment recovery
    """
    sess_res = client.post("/api/sessions")
    session_id = sess_res.json()["session_id"]

    # Create initial booking
    bk_res = client.post("/api/bookings", json={
        "session_id": session_id,
        "vehicle_id": "CAR-001",
        "customer_name": "Test Driver",
        "customer_email": "driver@example.com",
        "customer_phone": "+91 99999 00000",
        "driver_license_number": "DL-00001",
        "pickup_date": "2026-12-15",
        "return_date": "2026-12-18",
        "duration_days": 3,
        "pickup_location": "Delhi",
        "return_location": "Delhi",
        "idempotency_key": "idemp_scen_d_bk"
    })
    booking_id = bk_res.json()["booking_id"]

    # 1. Attempt simulated failure
    pay_fail = client.post("/api/payments/mock", json={
        "order_or_booking_id": booking_id,
        "amount": 9000.0,
        "payment_method": "card",
        "simulated_scenario": "failure",
        "idempotency_key": "idemp_scen_d_fail_attempt"
    })
    assert pay_fail.json()["status"] == "FAILED"
    assert pay_fail.json()["workflow_state"] == "PAYMENT_FAILED"

    # Booking must NOT be confirmed
    chk_bk = client.get(f"/api/bookings/{booking_id}")
    assert chk_bk.json()["status"] == "PENDING_PAYMENT"

    # 2. Safe retry with success
    pay_success = client.post("/api/payments/mock", json={
        "order_or_booking_id": booking_id,
        "amount": 9000.0,
        "payment_method": "upi",
        "simulated_scenario": "success",
        "idempotency_key": "idemp_scen_d_success_attempt"
    })
    assert pay_success.json()["status"] == "SUCCESS"
    assert pay_success.json()["workflow_state"] == "CONFIRMED"

    # Booking must now be confirmed
    chk_bk2 = client.get(f"/api/bookings/{booking_id}")
    assert chk_bk2.json()["status"] == "CONFIRMED"

    # 3. Idempotency test: Repeating payment with the exact same key returns same receipt
    pay_duplicate = client.post("/api/payments/mock", json={
        "order_or_booking_id": booking_id,
        "amount": 9000.0,
        "payment_method": "upi",
        "simulated_scenario": "success",
        "idempotency_key": "idemp_scen_d_success_attempt"
    })
    assert pay_duplicate.json()["status"] == "SUCCESS"
    assert pay_duplicate.json()["payment"]["id"] == pay_success.json()["payment"]["id"]
    assert pay_duplicate.json()["payment"]["transaction_reference"] == pay_success.json()["payment"]["transaction_reference"]
