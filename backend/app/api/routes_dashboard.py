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
def get_dashboard_vehicles_deprecated(authorization: Optional[str] = Header(None)):
    """Deprecated: Maps to confirmed purchases."""
    user_id = resolve_user_id(authorization)
    purchases = user_data_repo.get_user_purchases(user_id)
    return {
        "userId": user_id,
        "total": len(purchases),
        "vehicles": [p.model_dump() for p in purchases],
        "message": "My Garage has been consolidated into My Purchases."
    }
