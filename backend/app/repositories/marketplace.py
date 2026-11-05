import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from .base import MarketplaceRepositoryBase
from ..models.vehicle import Vehicle, RentalAvailabilityInterval
from ..marketplace.availability import is_vehicle_available_for_dates
from ..config import settings

logger = logging.getLogger(__name__)

class MarketplaceRepository(MarketplaceRepositoryBase):
    def __init__(self, data_path: Optional[str] = None):
        self.data_path = Path(data_path) if data_path else (Path(__file__).parent.parent.parent / "data" / "vehicles.json")
        self._vehicles: Dict[str, Vehicle] = {}
        self.load_from_json()

    def load_from_json(self):
        if not self.data_path.exists():
            logger.error(f"Data file not found at {self.data_path}")
            return
        with open(self.data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            for item in raw_data:
                vehicle = Vehicle(**item)
                self._vehicles[vehicle.id] = vehicle
        logger.info(f"Loaded {len(self._vehicles)} vehicles into marketplace repository.")

    def get_all_vehicles(self) -> List[Vehicle]:
        return list(self._vehicles.values())

    def get_vehicle_by_id(self, vehicle_id: str) -> Optional[Vehicle]:
        return self._vehicles.get(vehicle_id)

    def add_booking_interval(self, vehicle_id: str, start_date: str, end_date: str, booking_id: str) -> bool:
        vehicle = self.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            return False
        vehicle.rental_availability.append(
            RentalAvailabilityInterval(start_date=start_date, end_date=end_date, booking_id=booking_id)
        )
        return True

    def search_vehicles(
        self,
        intent: str = "rent", # "rent" or "buy"
        location: Optional[str] = None,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        transmission: Optional[str] = None,
        fuel_type: Optional[str] = None,
        seats: Optional[int] = None,
        brands: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Vehicle]:
        results: List[Vehicle] = []
        is_rent = (intent.lower() == "rent")

        for v in self._vehicles.values():
            # 1. Intent check
            if is_rent and not v.available_for_rent:
                continue
            if not is_rent and not v.available_for_purchase:
                continue

            # 2. Location check (case-insensitive substring or match)
            if location and location.lower() not in ["any", "all", ""]:
                if location.lower() not in v.location.lower():
                    continue

            # 3. Category check
            if category and category.lower() not in ["any", "all", ""]:
                if v.category.value.lower() != category.lower():
                    continue

            # 4. Budget check (daily for rent, total for purchase)
            if max_price and max_price > 0:
                if is_rent:
                    if v.rental_price_per_day > max_price:
                        continue
                else:
                    if v.purchase_price > max_price:
                        continue

            # 5. Transmission check
            if transmission and transmission.lower() not in ["any", "all", ""]:
                if v.transmission.value.lower() != transmission.lower():
                    continue

            # 6. Fuel Type check
            if fuel_type and fuel_type.lower() not in ["any", "all", ""]:
                if v.fuel_type.value.lower() != fuel_type.lower():
                    continue

            # 7. Seating capacity check
            if seats and seats > 0:
                if v.seats < seats:
                    continue

            # 8. Date Availability (for rent)
            if is_rent and start_date and end_date:
                available, _ = is_vehicle_available_for_dates(v, start_date, end_date)
                if not available:
                    continue

            results.append(v)

        return results

# Singleton instance
marketplace_repo = MarketplaceRepository()

