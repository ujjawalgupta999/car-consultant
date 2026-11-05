import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel, Field
from datetime import datetime
from ..models.listing import VehicleListing, ListingStatus, ApprovalStatus
from ..repositories.user_data_repo import user_data_repo
from ..api.routes_auth import resolve_user_id

router = APIRouter(prefix="/api/listings", tags=["Vehicle Listings (Sell a Car)"])

class CreateListingRequest(BaseModel):
    brand: str
    model: str
    variant: Optional[str] = "Standard"
    year: int = 2022
    registration_year: Optional[int] = None
    fuel_type: str = "Petrol"
    transmission: str = "Automatic"
    kms_driven: int = 25000
    condition: str = "Excellent"
    ownership_count: int = 1
    location: str = "Delhi NCR"
    expected_price: float = 1200000.0
    images: Optional[List[str]] = Field(default_factory=list)
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    is_registered_in_user_name: bool = True

class UpdateListingRequest(BaseModel):
    expected_price: Optional[float] = None
    kms_driven: Optional[int] = None
    condition: Optional[str] = None
    status: Optional[str] = None
    contact_phone: Optional[str] = None

@router.get("")
def get_user_listings(
    status: Optional[str] = Query(None, description="Filter by listing status"),
    authorization: Optional[str] = Header(None)
):
    user_id = resolve_user_id(authorization)
    listings = user_data_repo.get_user_listings(user_id, status=status)
    return {
        "userId": user_id,
        "total": len(listings),
        "listings": [l.model_dump() for l in listings]
    }

@router.post("", status_code=201)
def create_listing(
    req: CreateListingRequest,
    authorization: Optional[str] = Header(None)
):
    user_id = resolve_user_id(authorization)

    # Use default high-res vehicle image if none uploaded
    images = req.images or [
        "https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?auto=format&fit=crop&w=800&q=80"
    ]

    listing_id = f"LIST-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"
    listing = VehicleListing(
        id=listing_id,
        sellerId=user_id,
        brand=req.brand.strip(),
        model=req.model.strip(),
        variant=req.variant.strip() if req.variant else "Standard",
        year=req.year,
        registration_year=req.registration_year or req.year,
        fuel_type=req.fuel_type,
        transmission=req.transmission,
        kms_driven=req.kms_driven,
        condition=req.condition,
        ownership_count=req.ownership_count,
        location=req.location,
        expected_price=req.expected_price,
        images=images,
        contact_name=req.contact_name or "Aura Verified Seller",
        contact_phone=req.contact_phone or "+91 98765 43210",
        contact_email=req.contact_email or "seller@auramotors.com",
        is_registered_in_user_name=req.is_registered_in_user_name,
        approval_status=ApprovalStatus.APPROVED, # Pre-verified for verified demo users
        status=ListingStatus.ACTIVE,
        demo_mode=True
    )

    created = user_data_repo.create_listing(listing)
    return {
        "message": "Vehicle listing published successfully.",
        "listing_id": created.id,
        "listing": created.model_dump()
    }

@router.get("/{listing_id}")
def get_listing(
    listing_id: str,
    authorization: Optional[str] = Header(None)
):
    user_id = resolve_user_id(authorization)
    listing = user_data_repo.get_listing_by_id(listing_id, user_id=user_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found.")
    return listing.model_dump()

@router.put("/{listing_id}")
def update_listing(
    listing_id: str,
    req: UpdateListingRequest,
    authorization: Optional[str] = Header(None)
):
    user_id = resolve_user_id(authorization)
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    updated = user_data_repo.update_listing(listing_id, user_id=user_id, updates=updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Listing not found or unauthorized.")
    return {
        "message": "Listing updated successfully.",
        "listing": updated.model_dump()
    }

@router.delete("/{listing_id}")
def delete_listing(
    listing_id: str,
    authorization: Optional[str] = Header(None)
):
    user_id = resolve_user_id(authorization)
    success = user_data_repo.delete_listing(listing_id, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Listing not found or unauthorized.")
    return {
        "message": "Listing removed successfully.",
        "listing_id": listing_id
    }
