from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator
from .vehicle import VehicleCategory, FuelType, Transmission, VehicleCondition

class IntentType(str, Enum):
    RENT = "RENT"
    BUY = "BUY"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value.upper() == other.upper()
        if isinstance(other, IntentType):
            return self.value.upper() == other.value.upper()
        return super().__eq__(other)

    def __hash__(self):
        return hash(self.value.upper())

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
    
    # Canonical Preference Schema fields (all default to None as per specification)
    intent: Optional[str] = None # "BUY" or "RENT" or None
    location: Optional[str] = None
    vehicle_category: Optional[str] = None # e.g. "SUV", "Sedan", "Sports Car"
    seating_capacity: Optional[int] = None # e.g. 2, 4, 5, 7
    seating_match_type: Optional[str] = "exact" # "exact", "min", "max"
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    fuel_type: Optional[str] = None # "PETROL", "DIESEL", "ELECTRIC", "HYBRID", "CNG"
    transmission: Optional[str] = None # "AUTOMATIC", "MANUAL"
    purchase_type: Optional[str] = None # "new", "used", "any"
    brand_preference: Optional[str] = None
    rental_start_date: Optional[str] = None
    rental_end_date: Optional[str] = None

    # Backwards-compatible nested structures
    category: Optional[VehicleCategory] = None
    budget: Optional[Budget] = None
    preferred_brands: List[str] = Field(default_factory=list)
    additional_preferences: List[str] = Field(default_factory=list)
    rental_details: Optional[RentalDetails] = None
    purchase_details: Optional[PurchaseDetails] = None
    interview_complete: bool = False

    @model_validator(mode="after")
    def sync_canonical_and_nested(self):
        # 1. Sync category & vehicle_category
        if self.vehicle_category and not self.category:
            for cat in VehicleCategory:
                if cat.value.lower() == self.vehicle_category.lower():
                    self.category = cat
                    break
        elif self.category and not self.vehicle_category:
            self.vehicle_category = self.category.value

        # 2. Sync budget & budget_max
        if self.budget_max and not self.budget:
            is_daily = (self.intent == "RENT" or self.intent == IntentType.RENT)
            period = BudgetPeriod.PER_DAY if is_daily else BudgetPeriod.TOTAL
            self.budget = Budget(amount=self.budget_max, currency="INR", period=period)
        elif self.budget and not self.budget_max:
            self.budget_max = self.budget.amount

        # 3. Sync rental dates
        if self.rental_details:
            if self.rental_details.pickup_date and not self.rental_start_date:
                self.rental_start_date = self.rental_details.pickup_date
            if self.rental_details.return_date and not self.rental_end_date:
                self.rental_end_date = self.rental_details.return_date
        elif self.rental_start_date or self.rental_end_date:
            self.rental_details = RentalDetails(
                pickup_date=self.rental_start_date,
                return_date=self.rental_end_date
            )

        # 4. Sync brand preference
        if self.brand_preference and not self.preferred_brands:
            self.preferred_brands = [self.brand_preference]
        elif self.preferred_brands and not self.brand_preference:
            self.brand_preference = self.preferred_brands[0]

        # 5. Sync purchase details condition
        if self.purchase_type and not (self.purchase_details and self.purchase_details.condition):
            if not self.purchase_details:
                self.purchase_details = PurchaseDetails()
            self.purchase_details.condition = self.purchase_type
        elif self.purchase_details and self.purchase_details.condition and not self.purchase_type:
            self.purchase_type = self.purchase_details.condition

        return self

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Returns the canonical user preference schema required by specifications."""
        intent_str = None
        if self.intent:
            intent_str = self.intent.upper() if isinstance(self.intent, str) else self.intent.value.upper()

        return {
            "intent": intent_str,
            "location": self.location,
            "vehicle_category": self.vehicle_category or (self.category.value if self.category else None),
            "seating_capacity": self.seating_capacity,
            "budget_min": self.budget_min,
            "budget_max": self.budget_max or (self.budget.amount if self.budget else None),
            "fuel_type": self.fuel_type.upper() if (self.fuel_type and self.fuel_type.lower() != "any") else None,
            "transmission": self.transmission.upper() if (self.transmission and self.transmission.lower() != "any") else None,
            "purchase_type": self.purchase_type if (self.purchase_type and self.purchase_type.lower() != "any") else None,
            "brand_preference": self.brand_preference or (self.preferred_brands[0] if self.preferred_brands else None),
            "rental_start_date": self.rental_start_date or (self.rental_details.pickup_date if self.rental_details else None),
            "rental_end_date": self.rental_end_date or (self.rental_details.return_date if self.rental_details else None)
        }
