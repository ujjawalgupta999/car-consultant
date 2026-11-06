from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from ..repositories.user_data_repo import user_data_repo
from ..api.routes_auth import resolve_user_id

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/summary")
def get_dashboard_summary(authorization: Optional[str] = Header(None)):
    user_id = resolve_user_id(authorization)
    summary = user_data_repo.get_dashboard_summary(user_id)
    return {
        "userId": user_id,
        "summary": summary
    }

@router.get("/vehicles")
def get_dashboard_vehicles(authorization: Optional[str] = Header(None)):
    user_id = resolve_user_id(authorization)
    vehicles = user_data_repo.get_user_owned_vehicles(user_id)
    
    # Categorize vehicles
    purchased = [v.model_dump() for v in vehicles if v.source.value == "PURCHASED_PLATFORM"]
    manually_added = [v.model_dump() for v in vehicles if v.source.value == "MANUALLY_ADDED"]
    listed_for_sale = [v.model_dump() for v in vehicles if v.source.value == "LISTED_FOR_SALE"]
    sold = [v.model_dump() for v in vehicles if v.source.value == "SOLD"]

    return {
        "userId": user_id,
        "total": len(vehicles),
        "vehicles": [v.model_dump() for v in vehicles],
        "grouped": {
            "purchased_platform": purchased,
            "manually_added": manually_added,
            "listed_for_sale": listed_for_sale,
            "sold": sold
        }
    }

@router.get("/rentals")
def get_dashboard_rentals(authorization: Optional[str] = Header(None)):
    user_id = resolve_user_id(authorization)
    rentals = user_data_repo.get_user_rentals(user_id)
    return {
        "userId": user_id,
        "total": len(rentals),
        "rentals": [r.model_dump() for r in rentals]
    }

