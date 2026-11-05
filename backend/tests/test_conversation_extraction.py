import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.preferences import UserPreferences
from backend.app.agents.interview import AdaptiveInterviewAgent
from backend.app.repositories.marketplace import marketplace_repo

client = TestClient(app)

def test_canonical_preference_schema():
    """Verify default UserPreferences matches canonical schema with None for all fields."""
    prefs = UserPreferences()
    canonical = prefs.to_canonical_dict()
    expected_keys = [
        "intent", "location", "vehicle_category", "seating_capacity",
        "budget_min", "budget_max", "fuel_type", "transmission",
        "purchase_type", "brand_preference", "rental_start_date", "rental_end_date"
    ]
    for key in expected_keys:
        assert key in canonical
        assert canonical[key] is None

def test_scenario_1_buy_for_two_people():
    """
    Scenario 1: 'I want to buy a car for two people.'
    Extracts: intent=BUY, seating_capacity=2.
    Follow-up question acknowledges 2 people and asks only for genuinely missing fields (city & budget).
    """
    prefs = UserPreferences()
    updated_prefs, extracted = AdaptiveInterviewAgent.extract_preferences(
        "I want to buy a car for two people.", prefs
    )
    canonical = updated_prefs.to_canonical_dict()
    assert canonical["intent"] == "BUY"
    assert canonical["seating_capacity"] == 2

    # Follow-up question verification
    followup = AdaptiveInterviewAgent.generate_followup_question(updated_prefs)
    assert "two people" in followup.lower()
    assert "city" in followup.lower()
    assert "budget" in followup.lower()
    # Does NOT ask for category because 2 seats was provided
    assert "style of vehicle" not in followup.lower()

    # Via API endpoint
    sess_res = client.post("/api/sessions")
    session_id = sess_res.json()["session_id"]
    msg_res = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "I want to buy a car for two people."}
    )
    assert msg_res.status_code == 200
    data = msg_res.json()
    assert data["preferences"]["intent"] == "BUY"
    assert data["preferences"]["seating_capacity"] == 2
    bot_content = data["message"]["content"]
    assert "two people" in bot_content.lower()
    assert "city" in bot_content.lower()
    assert "budget" in bot_content.lower()

def test_scenario_2_two_seater_under_10_lakh():
    """
    Scenario 2: 'Show me a two-seater car under 10 lakh.'
    Extracts: seating_capacity=2, budget_max=1000000.0.
    Inventory diagnosis: in the database, two-seaters start at 39 Lakh,
    so it diagnoses zero results instead of recommending 5-seaters.
    """
    prefs = UserPreferences()
    updated_prefs, extracted = AdaptiveInterviewAgent.extract_preferences(
        "Show me a two-seater car under 10 lakh.", prefs
    )
    canonical = updated_prefs.to_canonical_dict()
    assert canonical["seating_capacity"] == 2
    assert canonical["budget_max"] == 1000000.0

    # Search verification: exact 2-seaters under 10 lakh
    matches = marketplace_repo.search_vehicles(
        intent="buy",
        max_price=1000000.0,
        seats=2,
        seats_match_type="exact"
    )
    assert len(matches) == 0  # 0 two-seaters under 10 lakh exist

    # But without budget constraint, exactly 11 two-seaters exist
    all_two_seaters = marketplace_repo.search_vehicles(
        intent="buy",
        seats=2,
        seats_match_type="exact"
    )
    assert len(all_two_seaters) == 11
    for v in all_two_seaters:
        assert v.seats == 2  # NEVER returns 5-seaters

def test_scenario_3_automatic_for_four_people():
    """
    Scenario 3: 'I need an automatic car for four people.'
    Extracts: transmission=AUTOMATIC, seating_capacity=4.
    """
    prefs = UserPreferences()
    updated_prefs, extracted = AdaptiveInterviewAgent.extract_preferences(
        "I need an automatic car for four people.", prefs
    )
    canonical = updated_prefs.to_canonical_dict()
    assert canonical["transmission"] == "AUTOMATIC"
    assert canonical["seating_capacity"] == 4

def test_scenario_4_electric_suv_five_passengers():
    """
    Scenario 4: 'Find an electric SUV for five passengers.'
    Extracts: fuel_type=ELECTRIC, vehicle_category=SUV, seating_capacity=5.
    """
    prefs = UserPreferences()
    updated_prefs, extracted = AdaptiveInterviewAgent.extract_preferences(
        "Find an electric SUV for five passengers.", prefs
    )
    canonical = updated_prefs.to_canonical_dict()
    assert canonical["fuel_type"] == "ELECTRIC"
    assert canonical["vehicle_category"] == "SUV"
    assert canonical["seating_capacity"] == 5

    # Search marketplace for electric 5-seater SUVs
    matches = marketplace_repo.search_vehicles(
        intent="buy",
        category="SUV",
        fuel_type="ELECTRIC",
        seats=5,
        seats_match_type="exact"
    )
    assert len(matches) > 0
    for v in matches:
        assert v.seats == 5
        assert v.fuel_type.value.lower() == "electric"

def test_scenario_5_rent_for_two_people_three_days():
    """
    Scenario 5: 'I want to rent a car for two people for three days.'
    Extracts: intent=RENT, seating_capacity=2, rental_duration=3.
    """
    prefs = UserPreferences()
    updated_prefs, extracted = AdaptiveInterviewAgent.extract_preferences(
        "I want to rent a car for two people for three days.", prefs
    )
    canonical = updated_prefs.to_canonical_dict()
    assert canonical["intent"] == "RENT"
    assert canonical["seating_capacity"] == 2
    assert updated_prefs.rental_details is not None
    assert updated_prefs.rental_details.rental_duration_days == 3

def test_scenario_6_state_preservation_and_update():
    """
    Scenario 6 & Multi-Turn Preservation:
    Turn 1: 'I want to buy a car for two people.'
    Turn 2: 'Budget is 10 lakh.'
    Turn 3: 'Actually, change the seating to four people.'
    Verifies that intent and budget are strictly preserved when seating is modified.
    """
    sess_res = client.post("/api/sessions")
    session_id = sess_res.json()["session_id"]

    # Turn 1
    t1 = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "I want to buy a car for two people."}
    )
    assert t1.status_code == 200
    p1 = t1.json()["preferences"]
    assert p1["intent"] == "BUY"
    assert p1["seating_capacity"] == 2

    # Turn 2
    t2 = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "Budget is 10 lakh."}
    )
    assert t2.status_code == 200
    p2 = t2.json()["preferences"]
    assert p2["intent"] == "BUY"
    assert p2["seating_capacity"] == 2
    assert p2["budget_max"] == 1000000.0
    # Turn 2 follow-up asks ONLY for missing location
    t2_content = t2.json()["message"]["content"]
    assert "city" in t2_content.lower()
    assert "budget" not in t2_content.lower()  # budget is already known!

    # Turn 3: Modify seating to 4
    t3 = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "Actually, change the seating to four people."}
    )
    assert t3.status_code == 200
    p3 = t3.json()["preferences"]
    assert p3["intent"] == "BUY"  # PRESERVED
    assert p3["seating_capacity"] == 4  # UPDATED
    assert p3["budget_max"] == 1000000.0  # PRESERVED

def test_semantic_variations_for_two_seater():
    """Verifies that varied natural expressions extract seating_capacity = 2."""
    test_phrases = [
        "I need a car for two people.",
        "I want a two-seater car.",
        "Only two seats are required.",
        "A car for me and one other person.",
        "I don't need a family car, just a small car with two seats.",
        "for the seating of 2 people",
        "couple car for me and my wife"
    ]
    for phrase in test_phrases:
        p = UserPreferences()
        updated, _ = AdaptiveInterviewAgent.extract_preferences(phrase, p)
        assert updated.seating_capacity == 2, f"Failed to extract seating_capacity=2 for phrase: '{phrase}'"

def test_semantic_variations_for_budget_range():
    """Verifies range extraction: 'between 10 and 15 lakh' -> min: 10L, max: 15L."""
    p = UserPreferences()
    updated, _ = AdaptiveInterviewAgent.extract_preferences(
        "I want a car between 10 and 15 lakh", p
    )
    assert updated.budget_min == 1000000.0
    assert updated.budget_max == 1500000.0
