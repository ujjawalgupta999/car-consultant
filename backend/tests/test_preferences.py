from backend.app.models.preferences import UserPreferences, IntentType
from backend.app.models.vehicle import VehicleCategory
from backend.app.agents.interview import AdaptiveInterviewAgent

def test_extract_scenario_a_rental():
    input_text = "I need an automatic SUV in Delhi for five days starting 15 December 2026. My budget is ₹3,000 per day."
    prefs = UserPreferences()
    updated, extracted = AdaptiveInterviewAgent.extract_preferences(input_text, prefs)
    
    assert updated.intent == IntentType.RENT
    assert updated.location == "Delhi"
    assert updated.category == VehicleCategory.SUV
    assert updated.transmission == "automatic"
    assert updated.budget is not None
    assert updated.budget.amount == 3000.0
    assert updated.rental_details is not None
    assert updated.rental_details.rental_duration_days == 5
    assert updated.rental_details.pickup_date == "2026-12-15"
    assert updated.rental_details.return_date == "2026-12-20"
    assert updated.interview_complete is True

def test_extract_scenario_b_purchase():
    input_text = "I want to buy a used automatic SUV in Delhi with a maximum budget of ₹15 lakh."
    prefs = UserPreferences()
    updated, extracted = AdaptiveInterviewAgent.extract_preferences(input_text, prefs)
    
    assert updated.intent == IntentType.BUY
    assert updated.location == "Delhi"
    assert updated.category == VehicleCategory.SUV
    assert updated.transmission == "automatic"
    assert updated.budget is not None
    assert updated.budget.amount == 1500000.0
    assert updated.purchase_details is not None
    assert updated.purchase_details.condition == "used"
    assert updated.purchase_details.purchase_budget == 1500000.0
    assert updated.interview_complete is True

def test_adaptive_missing_fields():
    # Incomplete input: only specifies SUV in Delhi
    input_text = "I am looking for an SUV in Delhi."
    prefs = UserPreferences()
    updated, extracted = AdaptiveInterviewAgent.extract_preferences(input_text, prefs)
    
    assert updated.interview_complete is False
    missing = AdaptiveInterviewAgent.check_missing_fields(updated)
    assert "budget" in missing
    assert "pickup_date" in missing or "rental_duration" in missing
    
    question = AdaptiveInterviewAgent.generate_followup_question(updated)
    assert "budget" in question.lower()
    # Does NOT ask for location or category because they were already provided!
    assert "which city" not in question.lower()
    assert "what style" not in question.lower()

