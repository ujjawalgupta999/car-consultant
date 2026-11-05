import json
from pathlib import Path

REQUIRED_CATEGORIES = [
    "Hatchback",
    "Sedan",
    "SUV",
    "Luxury Sedan",
    "Luxury SUV",
    "Electric Vehicle",
    "Hybrid",
    "MUV",
    "Sports Car",
    "Convertible"
]

def load_seed_data():
    data_path = Path(__file__).parent.parent / "data" / "vehicles.json"
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_listing_count():
    vehicles = load_seed_data()
    assert len(vehicles) >= 100, f"Expected >= 100 listings, found {len(vehicles)}"

def test_all_required_categories_present():
    vehicles = load_seed_data()
    categories_found = set(v["category"] for v in vehicles)
    for cat in REQUIRED_CATEGORIES:
        assert cat in categories_found, f"Required category '{cat}' missing from dataset"

def test_at_least_ten_brands_per_category():
    vehicles = load_seed_data()
    for cat in REQUIRED_CATEGORIES:
        brands_in_cat = set(v["brand"] for v in vehicles if v["category"] == cat)
        assert len(brands_in_cat) >= 10, (
            f"Category '{cat}' has only {len(brands_in_cat)} distinct brands: {brands_in_cat}. "
            f"Requirement is at least 10 distinct brands per category."
        )

def test_rental_and_purchase_fields_distinct():
    vehicles = load_seed_data()
    for v in vehicles:
        assert "rental_price_per_day" in v and v["rental_price_per_day"] > 0
        assert "purchase_price" in v and v["purchase_price"] > 0
        assert "available_for_rent" in v and isinstance(v["available_for_rent"], bool)
        assert "available_for_purchase" in v and isinstance(v["available_for_purchase"], bool)
        assert "rental_availability" in v and isinstance(v["rental_availability"], list)
        assert "rating" in v and 1.0 <= v["rating"] <= 5.0

