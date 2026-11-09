import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from .base import MarketplaceRepositoryBase
from ..models.vehicle import Vehicle
from ..config import settings
from ..db.mongodb import mongodb_manager

logger = logging.getLogger(__name__)

class MarketplaceRepository(MarketplaceRepositoryBase):
    def __init__(self, data_path: Optional[str] = None):
        self.data_path = Path(data_path) if data_path else (Path(__file__).parent.parent.parent / "data" / "vehicles.json")
        self._vehicles: Dict[str, Vehicle] = {}
        # 1. Initialize MongoDB connection & seeding if available
        self.load_from_mongodb()
        # 2. If MongoDB wasn't connected, load from json as fallback
        if len(self._vehicles) == 0:
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
        logger.info(f"Loaded {len(self._vehicles)} vehicles into marketplace repository from local fallback.")

    def load_from_mongodb(self):
        """Loads and synchronizes all vehicle listings directly from MongoDB Atlas."""
        try:
            if not mongodb_manager.is_connected():
                mongodb_manager.connect()

            if mongodb_manager.is_connected():
                coll = mongodb_manager.get_collection("vehicles")
                if coll is not None:
                    count = coll.count_documents({})
                    # If empty, automatically seed from vehicles.json into Atlas
                    if count == 0 and self.data_path.exists():
                        with open(self.data_path, "r", encoding="utf-8") as f:
                            seed_data = json.load(f)
                        for item in seed_data:
                            coll.update_one({"id": item["id"]}, {"$set": item}, upsert=True)
                        count = coll.count_documents({})
                        logger.info(f"Seeded {count} vehicles into empty MongoDB Atlas 'vehicles' collection.")

                    if count > 0:
                        loaded = {}
                        for doc in coll.find({}, {"_id": 0}):
                            vehicle = Vehicle(**doc)
                            loaded[vehicle.id] = vehicle
                        self._vehicles = loaded
                        logger.info(f"Directly loaded and synchronized {len(self._vehicles)} vehicles from MongoDB Atlas.")
        except Exception as e:
            logger.warning(f"Could not load vehicles from MongoDB: {e}")

    def get_all_vehicles(self) -> List[Vehicle]:
        return list(self._vehicles.values())

    def get_vehicle_by_id(self, vehicle_id: str) -> Optional[Vehicle]:
        if mongodb_manager.is_connected():
            coll = mongodb_manager.get_collection("vehicles")
            if coll is not None:
                try:
                    doc = coll.find_one({"id": vehicle_id}, {"_id": 0})
                    if doc:
                        return Vehicle(**doc)
                except Exception:
                    pass
        return self._vehicles.get(vehicle_id)

    def search_vehicles(
        self,
        intent: str = "buy",
        location: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        transmission: Optional[str] = None,
        fuel_type: Optional[str] = None,
        seats: Optional[int] = None,
        seats_min: Optional[int] = None,
        seats_max: Optional[int] = None,
        seats_match_type: Optional[str] = "exact",
        brands: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Vehicle]:
        results: List[Vehicle] = []

        vehicles_source = list(self._vehicles.values())
        if mongodb_manager.is_connected():
            coll = mongodb_manager.get_collection("vehicles")
            if coll is not None:
                try:
                    docs = list(coll.find({}, {"_id": 0}))
                    if docs:
                        vehicles_source = [Vehicle(**d) for d in docs]
                except Exception:
                    pass

        for v in vehicles_source:
            # 1. Marketplace is strictly purchase / buy
            if not v.available_for_purchase:
                continue

            # 2. Location check
            if location and location.lower() not in ["any", "all", ""]:
                if location.lower() not in v.location.lower():
                    continue

            # 3. Category check
            if category and category.lower() not in ["any", "all", ""]:
                cat_match = (v.category.value.lower() == category.lower())
                if not cat_match and category.lower() in ["suv", "luxury suv"]:
                    is_elec = (fuel_type and fuel_type.lower() == "electric") or (v.fuel_type.value.lower() == "electric")
                    if is_elec and v.category.value == "Electric Vehicle":
                        if any(k in v.model.lower() for k in ["nexon", "ioniq", "ev6", "zs", "xuv", "xc40", "model y"]):
                            cat_match = True
                if not cat_match:
                    continue

            # 4. Budget check (strictly purchase price)
            price = v.purchase_price
            if min_price and min_price > 0 and price < min_price:
                continue
            if max_price and max_price > 0 and price > max_price:
                continue

            # 5. Transmission check
            if transmission and transmission.lower() not in ["any", "all", ""]:
                if v.transmission.value.lower() != transmission.lower():
                    continue

            # 6. Fuel Type check
            if fuel_type and fuel_type.lower() not in ["any", "all", ""]:
                if v.fuel_type.value.lower() != fuel_type.lower():
                    continue

            # 7. Brand check
            if brands and len(brands) > 0:
                if not any(v.brand.lower() == b.lower() for b in brands):
                    continue

            # 8. Seating capacity check
            if seats_match_type == "exact" and seats and seats > 0:
                if v.seats != seats:
                    continue
            elif seats_match_type == "min" or (seats_min and seats_min > 0):
                target_min = seats_min or seats
                if target_min and v.seats < target_min:
                    continue
            elif seats_match_type == "max" or (seats_max and seats_max > 0):
                target_max = seats_max or seats
                if target_max and v.seats > target_max:
                    continue
            elif seats and seats > 0:
                if v.seats != seats:
                    continue

            results.append(v)

        return results

# Singleton instance
marketplace_repo = MarketplaceRepository()
