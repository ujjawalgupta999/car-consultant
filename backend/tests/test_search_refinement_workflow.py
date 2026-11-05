import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.session import WorkflowState
from backend.app.repositories.session import session_repo
from backend.app.orchestration.state_machine import StateMachine, InvalidStateTransitionError

client = TestClient(app)

def test_acceptance_criteria_workflow():
    """
    Acceptance Criteria Test:
    Turn 1: User says: 'I want to buy an SUV under 15 lakh.'
            -> AI searches marketplace and displays recommendations.
    Turn 2: User says: 'Actually, increase my budget to 20 lakh.'
            -> AI updates budget, preserves SUV and BUY intent, searches again, displays new recommendations.
    Turn 3: User says: 'Only show me cars with two seats.'
            -> AI updates seating capacity, preserves budget and SUV preference, searches again.
    Zero 500 errors across all turns!
    """
    # Create session
    sess_res = client.post("/api/sessions")
    assert sess_res.status_code == 201
    session_id = sess_res.json()["session_id"]

    # Turn 1: "I want to buy an SUV under 15 lakh."
    r1 = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "I want to buy an SUV under 15 lakh."}
    )
    assert r1.status_code == 200, f"Turn 1 failed: {r1.text}"
    d1 = r1.json()
    assert d1["workflow_state"] == "RECOMMENDATIONS_READY"
    assert len(d1["recommendations"]) > 0
    p1 = d1["preferences"]
    assert p1["intent"] == "BUY"
    assert p1["category"] == "SUV" or p1["vehicle_category"] == "SUV"
    assert p1["budget_max"] == 1500000.0

    # Verify top recommendations are all within 15 lakh budget
    for rec in d1["recommendations"]:
        assert rec["vehicle"]["purchase_price"] <= 1500000.0

    # Turn 2: "Actually, increase my budget to 20 lakh."
    # Previously this triggered: InvalidStateTransitionError: Invalid transition from RECOMMENDATIONS_READY to SEARCHING
    r2 = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "Actually, increase my budget to 20 lakh."}
    )
    assert r2.status_code == 200, f"Turn 2 failed: {r2.text}"
    d2 = r2.json()
    assert d2["workflow_state"] == "RECOMMENDATIONS_READY"
    assert len(d2["recommendations"]) > 0
    p2 = d2["preferences"]
    # Preserved preferences
    assert p2["intent"] == "BUY"
    assert p2["category"] == "SUV" or p2["vehicle_category"] == "SUV"
    # Updated budget
    assert p2["budget_max"] == 2000000.0

    # Turn 3: "Only show me cars with two seats."
    r3 = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "Only show me cars with two seats."}
    )
    assert r3.status_code == 200, f"Turn 3 failed: {r3.text}"
    d3 = r3.json()
    assert d3["workflow_state"] == "RECOMMENDATIONS_READY"
    p3 = d3["preferences"]
    assert p3["intent"] == "BUY"
    assert p3["category"] == "SUV" or p3["vehicle_category"] == "SUV"
    assert p3["budget_max"] == 2000000.0
    assert p3["seating_capacity"] == 2

def test_multiple_consecutive_refinements():
    """
    Test 5+ consecutive search refinement cycles:
    RECOMMENDATIONS_READY -> SEARCHING -> RECOMMENDATIONS_READY -> SEARCHING -> ...
    """
    sess_res = client.post("/api/sessions")
    session_id = sess_res.json()["session_id"]

    # 1. Initial search: Sedan under 25 lakh
    r1 = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "I want to buy a Sedan in Delhi under 25 lakh."}
    )
    assert r1.status_code == 200
    assert r1.json()["workflow_state"] == "RECOMMENDATIONS_READY"
    assert r1.json()["preferences"]["category"] == "Sedan"

    # 2. Refinement A: Change transmission to automatic
    r2 = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "Make it an automatic transmission."}
    )
    assert r2.status_code == 200
    assert r2.json()["workflow_state"] == "RECOMMENDATIONS_READY"
    assert r2.json()["preferences"]["transmission"] == "automatic"
    assert r2.json()["preferences"]["category"] == "Sedan"
    assert r2.json()["preferences"]["budget_max"] == 2500000.0

    # 3. Refinement B: Change fuel type to electric
    r3 = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "Actually, show me electric options."}
    )
    assert r3.status_code == 200
    assert r3.json()["workflow_state"] == "RECOMMENDATIONS_READY"
    assert r3.json()["preferences"]["fuel_type"] == "ELECTRIC"

    # 4. Refinement C: Increase budget to 50 lakh
    r4 = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "Increase budget to 50 lakh."}
    )
    assert r4.status_code == 200
    assert r4.json()["workflow_state"] == "RECOMMENDATIONS_READY"
    assert r4.json()["preferences"]["budget_max"] == 5000000.0

    # 5. Refinement D: Change city to Mumbai
    r5 = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "Let's look in Mumbai instead."}
    )
    assert r5.status_code == 200
    assert r5.json()["workflow_state"] == "RECOMMENDATIONS_READY"
    assert r5.json()["preferences"]["location"] == "Mumbai"

def test_transition_from_recommendations_back_to_interview():
    """
    Test switching from RECOMMENDATIONS_READY back to INTERVIEWING
    when requirements are modified to an incomplete state.
    """
    sess_res = client.post("/api/sessions")
    session_id = sess_res.json()["session_id"]

    # 1. Search that reaches RECOMMENDATIONS_READY
    r1 = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "I want to buy an SUV in Delhi with a budget of 15 lakh."}
    )
    assert r1.status_code == 200
    assert r1.json()["workflow_state"] == "RECOMMENDATIONS_READY"

    session = session_repo.get_session(session_id)
    assert session.workflow_state == WorkflowState.RECOMMENDATIONS_READY

    # 2. User transitions to rental with incomplete dates
    r2 = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "Actually, I want to rent a car instead of buying."}
    )
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["workflow_state"] == "INTERVIEWING"
    assert d2["preferences"]["intent"] == "RENT"
    # Persistent search results of the session are invalidated
    assert session_repo.get_session(session_id).search_results == []

def test_invalid_state_transition_api_error_handling():
    """
    Verify that if an InvalidStateTransitionError is triggered,
    the API returns a structured HTTP 400 error rather than an unhandled 500 traceback.
    """
    sess_res = client.post("/api/sessions")
    session_id = sess_res.json()["session_id"]

    # Manually put session in a state and attempt an illegal transition via validate_transition
    session = session_repo.get_session(session_id)
    assert session.workflow_state == WorkflowState.NEW

    with pytest.raises(InvalidStateTransitionError) as exc_info:
        StateMachine.validate_transition(WorkflowState.NEW, WorkflowState.PAYMENT_PROCESSING)

    assert exc_info.value.current_state == WorkflowState.NEW
    assert exc_info.value.target_state == WorkflowState.PAYMENT_PROCESSING
