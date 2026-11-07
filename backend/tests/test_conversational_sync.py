import pytest
from backend.app.repositories.session import session_repo
from backend.app.orchestration.orchestrator import orchestration_engine
from backend.app.agents.intent_detector import intent_detector

@pytest.mark.asyncio
async def test_vehicle_inquiry_syncs_background_page_and_applies_filter():
    session = session_repo.get_or_create_session("test_inquiry_session")
    
    # 1. User inquires about Tata Harrier
    query = "Tell me about the Tata Harrier. What are its main strengths and is it good for daily driving?"
    detected = intent_detector.detect_intent(query)
    assert detected.intent == "VEHICLE_INQUIRY"
    assert detected.entities.get("vehicle_name") == "harrier"

    res = await orchestration_engine.process_user_turn(session.session_id, query)
    assert res is not None
    assert len(res.get("website_actions", [])) > 0

    actions = res["website_actions"]
    nav_action = next((a for a in actions if a["type"] == "NAVIGATE_TO_PAGE"), None)
    filter_action = next((a for a in actions if a["type"] == "APPLY_FILTERS"), None)

    assert nav_action is not None
    assert nav_action["payload"]["path"] in ["/buy", "/rent"]
    assert filter_action is not None
    assert filter_action["payload"]["brand"].lower() == "tata"
    assert "harrier" in filter_action["payload"]["search"].lower()

@pytest.mark.asyncio
async def test_two_step_conversational_booking_proceed_and_pay():
    session = session_repo.get_or_create_session("test_booking_flow_session")

    # Step 1: User says "book tata harrier"
    r1 = await orchestration_engine.process_user_turn(session.session_id, "book tata harrier")
    assert r1 is not None
    
    # Background page navigated to booking form & pre-filled
    actions1 = r1["website_actions"]
    nav1 = next((a for a in actions1 if a["type"] == "NAVIGATE_TO_PAGE"), None)
    prefill1 = next((a for a in actions1 if a["type"] == "PREFILL_CHECKOUT_FORM"), None)
    assert nav1 is not None
    assert "/booking/" in nav1["payload"]["path"] or "/checkout/" in nav1["payload"]["path"]
    assert prefill1 is not None

    # AI asks user in chat to proceed
    content1 = r1["message"]["content"]
    assert "proceed to payment" in content1.lower() or "proceed" in content1.lower()
    
    # Step 2: User says "proceed"
    r2 = await orchestration_engine.process_user_turn(session.session_id, "proceed")
    assert r2 is not None

    # Background moves to checkout/payment page
    actions2 = r2["website_actions"]
    nav2 = next((a for a in actions2 if a["type"] == "NAVIGATE_TO_PAGE"), None)
    assert nav2 is not None
    assert "/checkout/" in nav2["payload"]["path"]

    # AI asks user to pay
    content2 = r2["message"]["content"]
    assert "pay it" in content2.lower() or "pay and confirm" in content2.lower()

    # Step 3: User says "pay it"
    r3 = await orchestration_engine.process_user_turn(session.session_id, "pay it")
    assert r3 is not None
    assert r3["workflow_state"] == "CONFIRMED"

    # Background navigates to payment result receipt
    actions3 = r3["website_actions"]
    nav3 = next((a for a in actions3 if a["type"] == "NAVIGATE_TO_PAGE"), None)
    assert nav3 is not None
    assert "/payment/result/" in nav3["payload"]["path"]

    # Returns showcase card with OWNED / RENTED status
    assert len(r3.get("cards", [])) > 0
    showcase = r3["cards"][0]
    assert showcase["status"] in ["OWNED", "RENTAL CONFIRMED"]

