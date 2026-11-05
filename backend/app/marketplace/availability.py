from datetime import datetime
from typing import List, Tuple, Optional
from ..models.vehicle import Vehicle, RentalAvailabilityInterval

def parse_date(d_str: str) -> datetime:
    try:
        return datetime.strptime(d_str, "%Y-%m-%d")
    except ValueError:
        # Fallback for ISO format with time
        return datetime.fromisoformat(d_str.replace("Z", "+00:00")).replace(tzinfo=None)

def is_vehicle_available_for_dates(
    vehicle: Vehicle,
    start_date_str: str,
    end_date_str: str
) -> Tuple[bool, List[RentalAvailabilityInterval]]:
    """
    Checks if vehicle has any overlapping booked intervals with the requested dates.
    Returns (is_available, list_of_conflicts).
    """
    if not vehicle.available_for_rent:
        return False, []

    req_start = parse_date(start_date_str)
    req_end = parse_date(end_date_str)

    if req_end < req_start:
        return False, []

    conflicts: List[RentalAvailabilityInterval] = []
    for interval in vehicle.rental_availability:
        booked_start = parse_date(interval.start_date)
        booked_end = parse_date(interval.end_date)

        # Intervals overlap if start <= booked_end and end >= booked_start
        if req_start <= booked_end and req_end >= booked_start:
            conflicts.append(interval)

    return len(conflicts) == 0, conflicts

