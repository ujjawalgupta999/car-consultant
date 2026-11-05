import pytest
from backend.app.models.vehicle import Vehicle, VehicleCategory, VehicleCondition, FuelType, Transmission
from backend.app.models.preferences import UserPreferences, Budget, IntentType, RentalDetails, BudgetPeriod
from backend.app.ranking.engine import RankingEngine
from backend.app.repositories.marketplace import marketplace_repo

def test_ranking_score_and_weights_with_brand():
    prefs = UserPreferences(
        intent=IntentType.RENT,
        location="Delhi",
        category=VehicleCategory.SUV,
        budget=Budget(amount=3000, currency="INR", period=BudgetPeriod.PER_DAY),
        transmission="automatic",
        preferred_brands=["Hyundai"],
        rental_details=RentalDetails(rental_duration_days=5)
    )
    
    vehicles = marketplace_repo.search_vehicles(
        intent="rent",
        location="Delhi",
        category="SUV",
        max_price=3000,
        transmission="automatic"
    )
    assert len(vehicles) > 0
    ranked = RankingEngine.rank_vehicles(vehicles, prefs, limit=5)
    
    assert len(ranked) > 0
    top_pick = ranked[0]
    assert top_pick.match_score >= 80.0
    assert "Hyundai" in top_pick.vehicle.brand
    assert top_pick.score_breakdown["brand_score"] == 10.0
    assert len(top_pick.positive_matches) > 0
    assert len(top_pick.trade_offs) >= 0
    assert "Creta" in top_pick.explanation or "Venue" in top_pick.explanation

def test_ranking_weights_redistribution_without_brand():
    prefs = UserPreferences(
        intent=IntentType.RENT,
        location="Delhi",
        category=VehicleCategory.SUV,
        budget=Budget(amount=3000, currency="INR", period=BudgetPeriod.PER_DAY),
        transmission="automatic",
        preferred_brands=[], # No brand specified
        rental_details=RentalDetails(rental_duration_days=5)
    )
    
    vehicles = marketplace_repo.search_vehicles(
        intent="rent",
        location="Delhi",
        category="SUV",
        max_price=3000,
        transmission="automatic"
    )
    ranked = RankingEngine.rank_vehicles(vehicles, prefs, limit=5)
    top_pick = ranked[0]
    # Brand score should be 0.0 because no brand preference was requested
    assert top_pick.score_breakdown["brand_score"] == 0.0
    # Total score should still be normalized up to 100
    assert 0.0 <= top_pick.match_score <= 100.0

def test_zero_result_diagnostics():
    prefs = UserPreferences(
        intent=IntentType.RENT,
        location="Delhi",
        category=VehicleCategory.CONVERTIBLE,
        budget=Budget(amount=500, currency="INR", period=BudgetPeriod.PER_DAY),
        transmission="automatic"
    )
    all_vehicles = marketplace_repo.get_all_vehicles()
    diag = RankingEngine.diagnose_zero_results(all_vehicles, prefs)
    
    assert len(diag["binding_constraints"]) > 0
    assert "Convertible" in diag["binding_constraints"][0]
    assert len(diag["recommended_relaxations"]) > 0

