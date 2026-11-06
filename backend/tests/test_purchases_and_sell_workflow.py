import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.repositories.user_data_repo import user_data_repo
from backend.app.repositories.session import session_repo
from backend.app.orchestration.orchestrator import orchestration_engine
from backend.app.models.session import WorkflowState
from backend.app.models.preferences import IntentType

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_demo_state():
    """Ensure clean baseline state before tests."""
    user_data_repo._purchases.clear()
    user_data_repo._purchases_by_order.clear()
    user_data_repo._listings.clear()
    user_data_repo._owned_vehicles.clear()
    user_data_repo._seed_initial_demo_data()

@pytest.mark.asyncio
async def test_complete_purchases_sell_and_context_isolation_journey():
    session_id = "sess_journey_test_01"
    user_id = "usr_demo_01"
    session_repo.get_or_create_session(session_id)

    # =========================================================================
    # STEP 1: Purchase an SUV through Platform & Verify Persistence & Idempotency
    # =========================================================================
    # 1.1 Calculate & create an order
    order_payload = {
        "session_id": session_id,
        "vehicle_id": "CAR-004", # Tata Harrier or Land Rover SUV
        "customer_name": "Alex Vance",
        "customer_email": "demo@auramotors.com",
        "customer_phone": "+91 98765 43210",
        "pan_or_id": "ABCDE1234F",
        "delivery_city": "Delhi",
        "deposit_amount": 25000.0,
        "idempotency_key": "idemp_order_suv_01"
    }
    ord_res = client.post("/api/orders", json=order_payload)
    assert ord_res.status_code == 201, ord_res.text
    order_id = ord_res.json()["order_id"]

    # 1.2 Execute mock payment for purchase order
    pay_payload = {
        "order_or_booking_id": order_id,
        "amount": 25000.0,
        "payment_method": "upi",
        "simulated_scenario": "success",
        "idempotency_key": "idemp_pay_suv_01"
    }
    pay_res = client.post("/api/payments/mock", json=pay_payload)
    assert pay_res.status_code == 200
    assert pay_res.json()["status"] == "SUCCESS"
    assert pay_res.json()["workflow_state"] == "CONFIRMED"

    # 1.3 Strict Payment Idempotency Check: Calling payment again returns cached success
    pay_res_dup = client.post("/api/payments/mock", json=pay_payload)
    assert pay_res_dup.status_code == 200
    assert pay_res_dup.json()["status"] == "SUCCESS"

    # 1.4 Verify purchases endpoint GET /api/purchases
    p_res = client.get("/api/purchases")
    assert p_res.status_code == 200
    p_data = p_res.json()
    assert p_data["total"] >= 1
    purchase = next(p for p in p_data["purchases"] if p["orderId"] == order_id)
    assert purchase["orderId"] == order_id
    assert purchase["purchaseStatus"] == "CONFIRMED"
    assert purchase["paymentStatus"] == "SUCCESS"
    assert purchase["vehicleSnapshot"]["brand"] != ""
    assert purchase["transactionReference"].startswith("TXN-")

    # 1.5 Verify purchased SUV automatically added to user's owned vehicles
    veh_res = client.get("/api/dashboard/vehicles")
    assert veh_res.status_code == 200
    veh_data = veh_res.json()
    platform_purchased = [v for v in veh_data["vehicles"] if v["source"] == "PURCHASED_PLATFORM"]
    assert len(platform_purchased) == 1
    assert platform_purchased[0]["vehicleId"] == "CAR-004"

    # 1.6 Verify dashboard summary computed metrics
    summ_res = client.get("/api/dashboard/summary")
    assert summ_res.status_code == 200
    metrics = summ_res.json()["summary"]
    assert metrics["total_purchases"] >= 1
    assert metrics["total_spent_inr"] > 0
    assert metrics["vehicles_owned"] >= 3 # initial 2 seed + 1 purchased

    # =========================================================================
    # STEP 2: User says "I want to sell a sedan" -> AI isolates context & asks registration
    # =========================================================================
    # Current session is in CONFIRMED state.
    session = session_repo.get_session(session_id)
    assert session.workflow_state == WorkflowState.CONFIRMED

    # User initiates new intent: "I want to sell a sedan"
    turn_1 = await orchestration_engine.process_user_turn(session_id, "I want to sell a sedan")
    
    # Verify no purchase confirmation text repeated
    assert "🎉" not in turn_1["message"]["content"]
    assert "Booking Confirmed" not in turn_1["message"]["content"]
    assert "Reference" not in turn_1["message"]["content"]

    # Verify intent classified as SELL
    assert turn_1["preferences"]["intent"] == "SELL"
    assert turn_1["preferences"]["vehicle_category"] == "Sedan" or turn_1["preferences"]["category"] == "Sedan"

    # Verify AI asked registration question as per requirement
    assert "registered in your name" in turn_1["message"]["content"].lower()

    # =========================================================================
    # STEP 3: User provides vehicle details -> AI pre-fills Sell Form & navigates
    # =========================================================================
    turn_2 = await orchestration_engine.process_user_turn(
        session_id,
        "Yes, it is a 2021 Honda City, petrol, automatic, 32,000 km, asking 11.8 Lakh in Delhi"
    )

    # Verify AI responses
    content_2 = turn_2["message"]["content"]
    assert "Honda City" in content_2 or "honda" in content_2.lower()
    assert "Sell a Car" in content_2 or "listing" in content_2.lower()

    # Verify structured website actions
    actions_2 = turn_2["website_actions"]
    prefill_action = next((a for a in actions_2 if a["type"] == "PREFILL_SELL_FORM"), None)
    nav_action = next((a for a in actions_2 if a["type"] == "NAVIGATE_TO_PAGE"), None)

    assert prefill_action is not None
    assert nav_action is not None
    assert nav_action["payload"]["path"] == "/sell-car"

    payload_pf = prefill_action["payload"]
    assert payload_pf["brand"].lower() == "honda"
    assert payload_pf["model"].lower() == "city"
    assert payload_pf["year"] == 2021
    assert payload_pf["is_registered_in_user_name"] is True
    assert payload_pf["kms_driven"] == 32000
    assert payload_pf["expected_price"] == 1180000.0

    # =========================================================================
    # STEP 4: Submit listing via POST /api/listings
    # =========================================================================
    listing_res = client.post("/api/listings", json={
        "brand": "Honda",
        "model": "City",
        "variant": "ZX 1.5 i-VTEC",
        "year": 2021,
        "registration_year": 2021,
        "fuel_type": "Petrol",
        "transmission": "Automatic",
        "kms_driven": 32000,
        "condition": "Excellent",
        "ownership_count": 1,
        "location": "Delhi NCR",
        "expected_price": 1180000.0,
        "images": ["https://images.unsplash.com/photo-1590362891988-f77804702088?auto=format&fit=crop&w=800&q=80"],
        "is_registered_in_user_name": True,
        "contact_name": "Alex Vance",
        "contact_phone": "+91 98765 43210",
        "contact_email": "demo@auramotors.com"
    })
    assert listing_res.status_code == 201, listing_res.text
    listing_id = listing_res.json()["listing_id"]

    # Verify listing appears in GET /api/listings
    list_check = client.get("/api/listings")
    assert list_check.status_code == 200
    my_listings = list_check.json()["listings"]
    assert any(l["id"] == listing_id for l in my_listings)

    # Verify SUV purchase from Step 1 is still safely in My Purchases
    p_check = client.get("/api/purchases")
    assert p_check.status_code == 200
    assert p_check.json()["total"] >= 1
    assert any(p["orderId"] == order_id for p in p_check.json()["purchases"])

    # =========================================================================
    # STEP 5: User says "Show my purchased cars" -> AI summarizes & navigates
    # =========================================================================
    turn_3 = await orchestration_engine.process_user_turn(session_id, "Show my purchased cars")
    assert turn_3["preferences"]["intent"] == "PURCHASE_HISTORY"
    assert "My Purchases" in turn_3["message"]["content"]
    assert order_id in turn_3["message"]["content"] or "purchases" in turn_3["message"]["content"].lower()

    actions_3 = turn_3["website_actions"]
    nav_to_purchases = next((a for a in actions_3 if a["type"] == "NAVIGATE_TO_PAGE"), None)
    assert nav_to_purchases is not None
    assert nav_to_purchases["payload"]["path"] == "/dashboard/purchases"
