from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Query
from ..repositories.user_data_repo import user_data_repo
from ..api.routes_auth import resolve_user_id

router = APIRouter(prefix="/api/purchases", tags=["Purchases"])

@router.get("")
def get_user_purchases(
    search: Optional[str] = Query(None, description="Search by brand, model, orderId, or city"),
    sort: Optional[str] = Query("date_desc", description="Sorting order: date_desc, date_asc, price_desc, price_asc"),
    status: Optional[str] = Query(None, description="Filter by status: CONFIRMED, DELIVERED, etc."),
    authorization: Optional[str] = Header(None)
):
    user_id = resolve_user_id(authorization)
    purchases = user_data_repo.get_user_purchases(
        user_id=user_id,
        search=search,
        sort_by=sort,
        status=status
    )
    return {
        "userId": user_id,
        "total": len(purchases),
        "purchases": [p.model_dump() for p in purchases]
    }

@router.get("/{purchase_id}")
def get_purchase_details(
    purchase_id: str,
    authorization: Optional[str] = Header(None)
):
    user_id = resolve_user_id(authorization)
    purchase = user_data_repo.get_purchase_by_id(purchase_id, user_id=user_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase record not found.")
    return purchase.model_dump()
