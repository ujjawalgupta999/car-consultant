from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Query
from ..repositories.user_data_repo import user_data_repo
from ..api.routes_auth import resolve_user_id

router = APIRouter(prefix="/api/rentals", tags=["Rentals"])

@router.get("")
def get_user_rentals(
    search: Optional[str] = Query(None, description="Search by brand, model, orderId, or pickup city"),
    status: Optional[str] = Query(None, description="Filter by status: CONFIRMED, ACTIVE, COMPLETED"),
    authorization: Optional[str] = Header(None)
):
    user_id = resolve_user_id(authorization)
    rentals = user_data_repo.get_user_rentals(
        user_id=user_id,
        search=search,
        status=status
    )
    return {
        "userId": user_id,
        "total": len(rentals),
        "rentals": [r.model_dump() for r in rentals]
    }

@router.get("/{rental_id}")
def get_rental_details(
    rental_id: str,
    authorization: Optional[str] = Header(None)
):
    user_id = resolve_user_id(authorization)
    rental = user_data_repo.get_rental_by_id(rental_id, user_id=user_id)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental record not found.")
    return rental.model_dump()

