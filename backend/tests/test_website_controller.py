import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_user_input_buy_car_sedan_navigates_and_filters():
    # 1. Create session
    sess_res = client.post("/api/sessions")
    assert sess_res.status_code == 201
    session_id = sess_res.json()["session_id"]

    # 2. User sends "i want to buy an car sedan"
    msg_res = client.post(f"/api/sessions/{session_id}/messages", json={"content": "i want to buy an car sedan"})
    assert msg_res.status_code == 200
    data = msg_res.json()

    # Verify website actions
    actions = data.get("website_actions", [])
    assert len(actions) >= 2

    nav_action = next((a for a in actions if a["type"] == "NAVIGATE_TO_PAGE"), None)
    assert nav_action is not None
    assert nav_action["payload"]["path"] == "/buy"

    filter_action = next((a for a in actions if a["type"] == "APPLY_FILTERS"), None)
    assert filter_action is not None
    assert filter_action["payload"]["category"] == "Sedan"
    assert filter_action["payload"]["intent"] == "buy"

    # Verify message mentions navigating to Buy Cars and filtering for Sedans
    msg_content = data["message"]["content"]
    assert "Buy Cars" in msg_content
    assert "Sedan" in msg_content

    # Recommendations preview should be present
    assert len(data.get("recommendations", [])) > 0

def test_typo_and_negation_input():
    sess_res = client.post("/api/sessions")
    session_id = sess_res.json()["session_id"]

    # Typo "but" for "buy" and negation "instead of suv"
    msg_res = client.post(f"/api/sessions/{session_id}/messages", json={"content": "i want to but an sedan instead of suv"})
    assert msg_res.status_code == 200
    data = msg_res.json()

    actions = data.get("website_actions", [])
    nav_action = next((a for a in actions if a["type"] == "NAVIGATE_TO_PAGE"), None)
    assert nav_action is not None
    assert nav_action["payload"]["path"] == "/buy"

    filter_action = next((a for a in actions if a["type"] == "APPLY_FILTERS"), None)
    assert filter_action is not None
    assert filter_action["payload"]["category"] == "Sedan"

def test_comparison_prompt_navigates_to_compare():
    sess_res = client.post("/api/sessions")
    session_id = sess_res.json()["session_id"]

    prompt = (
        "Please provide an objective, expert comparison between: Tata Harrier Fearless Plus (2024) vs Toyota Fortuner Legender (2024). "
        "Highlight their driving dynamics, fuel efficiency, ownership costs, and give me a clear verdict on which is the superior choice for daily urban driving vs long highway tours."
    )
    msg_res = client.post(f"/api/sessions/{session_id}/messages", json={"content": prompt})
    assert msg_res.status_code == 200
    data = msg_res.json()

    actions = data.get("website_actions", [])
    nav_action = next((a for a in actions if a["type"] == "NAVIGATE_TO_PAGE"), None)
    assert nav_action is not None
    assert nav_action["payload"]["path"] == "/compare"

    comp_action = next((a for a in actions if a["type"] == "ADD_TO_COMPARISON"), None)
    assert comp_action is not None
    assert "CAR-022" in comp_action["payload"]["vehicleIds"]
    assert "CAR-025" in comp_action["payload"]["vehicleIds"]

    assert "Tata Harrier Fearless Plus" in data["message"]["content"]
    assert "Toyota Fortuner Legender" in data["message"]["content"]

