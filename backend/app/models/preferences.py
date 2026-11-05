from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from .vehicle import VehicleCategory, FuelType, Transmission, VehicleCondition

class IntentType(str, Enum):
    RENT = "rent"
    BUY = "buy"

class BudgetPeriod(str, Enum):
    PER_DAY = "per_day"
    TOTAL = "total"

class Budget(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = "INR"
    period: BudgetPeriod = BudgetPeriod.PER_DAY

class RentalDetails(BaseModel):
    pickup_date: Optional[str] = None
    return_date: Optional[str] = None
    rental_duration_days: Optional[int] = Field(default=None, ge=1)
    pickup_location: Optional[str] = None
    return_location: Optional[str] = None

class PurchaseDetails(BaseModel):
    purchase_budget: Optional[float] = None
    expected_purchase_date: Optional[str] = None
    condition: Optional[str] = "any" # "new", "used", "any"
    financing_preference: Optional[str] = "loan" # "cash", "loan", "lease"
    intended_ownership_use: Optional[str] = None

class UserPreferences(BaseModel):
    session_id: Optional[str] = None
    intent: IntentType = IntentType.RENT
    location: Optional[str] = None
    category: Optional[VehicleCategory] = None
    budget: Optional[Budget] = None
    fuel_type: Optional[str] = "any"
    transmission: Optional[str] = "any"
    seating_capacity: Optional[int] = None
    preferred_brands: List[str] = Field(default_factory=list)
    additional_preferences: List[str] = Field(default_factory=list)
    rental_details: Optional[RentalDetails] = None
    purchase_details: Optional[PurchaseDetails] = None
    interview_complete: bool = False

