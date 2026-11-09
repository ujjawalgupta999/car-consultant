import uuid
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.mongodb import mongodb_manager
from backend.app.repositories.user_data_repo import user_data_repo

client = TestClient(app)

def test_full_user_registration_save_and_purchase_flow():
    # 1. Register a new user
    rand_suffix = uuid.uuid4().hex[:6]
    test_email = f"user_{rand_suffix}@auratest.com"
    test_password = "SecretPassword123!"
    test_name = f"Test Driver {rand_suffix}"

    reg_res = client.post("/api/auth/signup", json={
        "name": test_name,
        "email": test_email,
        "password": test_password,
        "phone": "+91 99999 11111"
    })
    assert reg_res.status_code == 201, f"Signup failed: {reg_res.text}"
    reg_data = reg_res.json()
    token = reg_data["token"]
    user_id = reg_data["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Login as the newly created user
    login_res = client.post("/api/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    login_data = login_res.json()
    assert login_data["user"]["email"] == test_email
    assert login_data["user"]["name"] == test_name

    # 3. Verify user profile retrieval
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["authenticated"] is True
    assert me_data["user"]["id"] == user_id

    # 4. Save a vehicle to user shortlist
    target_vehicle_id = "CAR-002"
    save_res = client.post("/api/auth/saved-vehicles/toggle", json={
        "vehicle_id": target_vehicle_id
    }, headers=headers)
    assert save_res.status_code == 200
    save_data = save_res.json()
    assert save_data["is_saved"] is True
    assert target_vehicle_id in save_data["saved_vehicles"]

    # Verify saved endpoint
    saved_list_res = client.get("/api/auth/saved", headers=headers)
    assert saved_list_res.status_code == 200
    assert target_vehicle_id in saved_list_res.json()["saved_vehicles"]

    # 5. Place a purchase order (refundable token deposit)
    checkout_res = client.post("/api/checkout", json={
        "vehicle_id": target_vehicle_id,
        "intent": "buy",
        "customer_name": test_name,
        "customer_email": test_email,
        "customer_phone": "+91 99999 11111",
        "delivery_city": "Mumbai"
    }, headers=headers)
    assert checkout_res.status_code == 200, f"Checkout initiation failed: {checkout_res.text}"
    checkout_data = checkout_res.json()
    order_id = checkout_data["orderId"]
    assert order_id.startswith("ORD-")
    assert checkout_data["transactionType"] == "BUY"
    assert checkout_data["pricing"]["depositAmount"] == 25000.0

    # 6. Simulate payment confirmation
    pay_res = client.post("/api/payments/mock/confirm", json={
        "orderId": order_id,
        "amount": 25000.0,
        "paymentMethod": "UPI",
        "simScenario": "success"
    }, headers=headers)
    assert pay_res.status_code == 200, f"Payment failed: {pay_res.text}"
    pay_data = pay_res.json()
    assert pay_data["status"] == "SUCCESS"
    assert pay_data["payment"]["paymentStatus"] == "SUCCESS"
    assert pay_data["payment"]["orderId"] == order_id

    # 7. View purchase in "MY PURCHASES"
    purchases_res = client.get("/api/purchases", headers=headers)
    assert purchases_res.status_code == 200
    purchases_data = purchases_res.json()
    assert purchases_data["total"] >= 1
    my_order = next((p for p in purchases_data["purchases"] if p["orderId"] == order_id), None)
    assert my_order is not None, f"Order {order_id} not found in user purchases"
    assert my_order["purchaseStatus"] == "CONFIRMED"
    assert my_order["paymentStatus"] == "SUCCESS"

    # 8. Check Payment Ledger
    payments_res = client.get("/api/payments", headers=headers)
    assert payments_res.status_code == 200
    payments_data = payments_res.json()
    assert any(p["orderId"] == order_id for p in payments_data["payments"])

    # 9. Verify Dashboard Summary metrics (exclusively purchases/payments/saved/listings)
    summary_res = client.get("/api/dashboard/summary", headers=headers)
    assert summary_res.status_code == 200
    sum_data = summary_res.json()["summary"]
    assert "total_rentals" not in sum_data
    assert "active_rentals" not in sum_data
    assert "vehicles_owned" not in sum_data
    assert sum_data["total_purchases"] >= 1
    assert sum_data["total_spent_inr"] > 0
    assert sum_data["total_saved"] >= 1

    # 10. Verify Rental endpoints return 404 (strictly eliminated)
    rental_res = client.get("/api/rentals")
    assert rental_res.status_code == 404, f"Rental endpoint should be removed, got {rental_res.status_code}"

    booking_calc_res = client.post("/api/bookings/calculate", json={})
    assert booking_calc_res.status_code == 404, f"Booking calc endpoint should be removed, got {booking_calc_res.status_code}"

    print("ALL ATLAS PERSISTENCE & RENTAL/GARAGE CLEANUP TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_full_user_registration_save_and_purchase_flow()

