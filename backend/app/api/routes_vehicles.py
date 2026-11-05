from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..repositories.marketplace import marketplace_repo
from ..marketplace.availability import is_vehicle_available_for_dates
from ..ranking.engine import RankingEngine
from ..models.preferences import UserPreferences, IntentType, Budget, BudgetPeriod

router = APIRouter(tags=["Vehicles & Marketplace"])

class SearchRequest(BaseModel):
    intent: str = "rent" # "rent" or "buy"
    location: Optional[str] = None
    category: Optional[str] = None
    max_price: Optional[float] = None
    transmission: Optional[str] = None
    fuel_type: Optional[str] = None
    seats: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = 5

class CompareRequest(BaseModel):
    vehicle_ids: List[str]

class AvailabilityCheckRequest(BaseModel):
    vehicle_id: str
    start_date: str
    end_date: str

@router.post("/api/search")
def search_marketplace(req: SearchRequest):
    vehicles = marketplace_repo.search_vehicles(
        intent=req.intent,
        location=req.location,
        category=req.category,
        max_price=req.max_price,
        transmission=req.transmission,
        fuel_type=req.fuel_type,
        seats=req.seats,
        start_date=req.start_date,
        end_date=req.end_date
    )

    # Rank results
    prefs = UserPreferences(
        intent=IntentType.RENT if req.intent.lower() == "rent" else IntentType.BUY,
        location=req.location,
        category=None,
        budget=Budget(amount=req.max_price, currency="INR", period=BudgetPeriod.PER_DAY) if req.max_price else None,
        transmission=req.transmission,
        fuel_type=req.fuel_type,
        seating_capacity=req.seats
    )
    if req.category:
        try:
            from ..models.vehicle import VehicleCategory
            prefs.category = VehicleCategory(req.category)
        except ValueError:
            pass

    ranked = RankingEngine.rank_vehicles(vehicles, prefs, limit=req.limit)

    return {
        "total_matching": len(vehicles),
        "recommendations": [r.to_dict() for r in ranked]
    }

@router.get("/api/vehicles")
def list_vehicles(
    category: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 50
):
    all_v = marketplace_repo.get_all_vehicles()
    if category:
        all_v = [v for v in all_v if v.category.value.lower() == category.lower()]
    if location:
        all_v = [v for v in all_v if location.lower() in v.location.lower()]
    return {
        "count": len(all_v[:limit]),
        "vehicles": [v.model_dump() for v in all_v[:limit]]
    }

@router.get("/api/vehicles/{vehicle_id}")
def get_vehicle_details(vehicle_id: str):
    v = marketplace_repo.get_vehicle_by_id(vehicle_id)
    if not v:
        raise HTTPException(status_code=404, detail=f"Vehicle '{vehicle_id}' not found.")
    return v.model_dump()

@router.post("/api/vehicles/compare")
def compare_vehicles(req: CompareRequest):
    compared = []
    for vid in req.vehicle_ids[:4]:
        v = marketplace_repo.get_vehicle_by_id(vid)
        if v:
            compared.append(v.model_dump())
    return {
        "count": len(compared),
        "vehicles": compared
    }

@router.post("/api/availability/check")
def check_availability(req: AvailabilityCheckRequest):
    v = marketplace_repo.get_vehicle_by_id(req.vehicle_id)
    if not v:
        raise HTTPException(status_code=404, detail=f"Vehicle '{req.vehicle_id}' not found.")
    is_avail, conflicts = is_vehicle_available_for_dates(v, req.start_date, req.end_date)
    return {
        "vehicle_id": req.vehicle_id,
        "is_available": is_avail,
        "conflicts": [c.model_dump() for c in conflicts]
    }

