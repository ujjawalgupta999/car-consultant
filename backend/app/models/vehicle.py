from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

class VehicleCategory(str, Enum):
    HATCHBACK = "Hatchback"
    SEDAN = "Sedan"
    SUV = "SUV"
    LUXURY_SEDAN = "Luxury Sedan"
    LUXURY_SUV = "Luxury SUV"
    ELECTRIC_VEHICLE = "Electric Vehicle"
    HYBRID = "Hybrid"
    MUV = "MUV"
    SPORTS_CAR = "Sports Car"
    CONVERTIBLE = "Convertible"

class VehicleCondition(str, Enum):
    NEW = "new"
    USED = "used"

class FuelType(str, Enum):
    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    CNG = "cng"

class Transmission(str, Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"

class RentalAvailabilityInterval(BaseModel):
    start_date: str
    end_date: str
    booking_id: Optional[str] = None

class Vehicle(BaseModel):
    id: str = Field(..., description="Unique vehicle identifier e.g. CAR-001")
    brand: str
    model: str
    year: int
    category: VehicleCategory
    condition: VehicleCondition
    fuel_type: FuelType
    transmission: Transmission
    seats: int
    location: str
    rental_price_per_day: float
    purchase_price: float
    available_for_rent: bool = True
    available_for_purchase: bool = True
    rental_availability: List[RentalAvailabilityInterval] = Field(default_factory=list)
    rating: float = Field(..., ge=1.0, le=5.0)
    review_count: int = 0
    image_url: Optional[str] = None
    features: List[str] = Field(default_factory=list)
    mileage_kmpl: Optional[float] = None
    range_km: Optional[int] = None
    odometer_km: int = 0
    source: str = "Mock Marketplace"
    listing_type: str = "mock"

