from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..models.vehicle import Vehicle

class MarketplaceRepositoryBase(ABC):
    @abstractmethod
    def get_all_vehicles(self) -> List[Vehicle]:
        pass

    @abstractmethod
    def get_vehicle_by_id(self, vehicle_id: str) -> Optional[Vehicle]:
        pass

    @abstractmethod
    def search_vehicles(
        self,
        intent: str, # "rent" or "buy"
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
        pass

