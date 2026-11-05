"""
Seed data generator for Amulate Summer Hackathon 2026.
Generates at least 100 listings across 10 categories, ensuring that
AT LEAST 10 DISTINCT BRANDS are represented in EVERY category.
"""

import json
from pathlib import Path

# Category-to-Brand matrix: 10 distinct brands per category
CATEGORY_BRANDS = {
    "Hatchback": [
        ("Maruti Suzuki", "Swift ZXi", 2024, "petrol", "automatic", 5, 2200, 850000, 14000, 4.6),
        ("Hyundai", "i20 Asta (O)", 2025, "petrol", "automatic", 5, 2500, 1100000, 8000, 4.7),
        ("Tata", "Altroz XZ Plus", 2023, "diesel", "manual", 5, 2100, 920000, 22000, 4.5),
        ("Volkswagen", "Polo GT TSI", 2022, "petrol", "automatic", 5, 2700, 980000, 29000, 4.8),
        ("Toyota", "Glanza V", 2024, "petrol", "automatic", 5, 2300, 990000, 11000, 4.6),
        ("Honda", "Jazz ZX", 2022, "petrol", "automatic", 5, 2200, 880000, 31000, 4.4),
        ("Renault", "Kwid Climber", 2024, "petrol", "automatic", 5, 1600, 620000, 12000, 4.2),
        ("Mini", "Cooper 3-Door S", 2023, "petrol", "automatic", 4, 8500, 4200000, 16000, 4.9),
        ("Fiat", "Abarth Punto", 2021, "petrol", "manual", 5, 2900, 750000, 38000, 4.6),
        ("Ford", "Figo Titanium", 2021, "diesel", "manual", 5, 1800, 580000, 42000, 4.3),
    ],
    "Sedan": [
        ("Honda", "City ZX", 2025, "petrol", "automatic", 5, 2900, 1550000, 6000, 4.8),
        ("Hyundai", "Verna SX (O) Turbo", 2024, "petrol", "automatic", 5, 3100, 1680000, 13000, 4.7),
        ("Skoda", "Slavia Style 1.5 TSI", 2024, "petrol", "automatic", 5, 3300, 1750000, 15000, 4.8),
        ("Volkswagen", "Virtus GT Plus", 2025, "petrol", "automatic", 5, 3400, 1820000, 9000, 4.9),
        ("Maruti Suzuki", "Ciaz Alpha", 2023, "petrol", "automatic", 5, 2400, 1120000, 24000, 4.4),
        ("Toyota", "Camry Hybrid", 2023, "hybrid", "automatic", 5, 7500, 4500000, 19000, 4.9),
        ("Nissan", "Sunny XV", 2021, "diesel", "manual", 5, 1900, 650000, 45000, 4.2),
        ("Mazda", "Mazda 3 SkyActiv", 2023, "petrol", "automatic", 5, 3800, 2200000, 18000, 4.7),
        ("Subaru", "Legacy Premium", 2023, "petrol", "automatic", 5, 4100, 2600000, 21000, 4.5),
        ("Kia", "K5 GT-Line", 2024, "petrol", "automatic", 5, 4200, 2800000, 14000, 4.7),
    ],
    "SUV": [
        ("Hyundai", "Creta SX (O)", 2025, "petrol", "automatic", 5, 2800, 1450000, 12400, 4.7),
        ("Tata", "Harrier Fearless Plus", 2024, "diesel", "automatic", 5, 3600, 2400000, 14000, 4.7),
        ("Mahindra", "XUV700 AX7 Luxury", 2024, "diesel", "automatic", 7, 3800, 2550000, 17000, 4.8),
        ("Kia", "Seltos GTX Plus", 2025, "petrol", "automatic", 5, 2900, 1950000, 8000, 4.7),
        ("Toyota", "Fortuner Legender", 2024, "diesel", "automatic", 7, 6500, 4400000, 19000, 4.9),
        ("MG", "Hector Sharp Pro", 2023, "petrol", "automatic", 5, 2700, 1850000, 21000, 4.4),
        ("Jeep", "Compass Model S", 2023, "diesel", "automatic", 5, 4200, 2700000, 18000, 4.6),
        ("Volkswagen", "Taigun Topline", 2024, "petrol", "automatic", 5, 3000, 1750000, 11000, 4.7),
        ("Skoda", "Kushaq Monte Carlo", 2024, "petrol", "automatic", 5, 3100, 1800000, 13000, 4.6),
        ("Nissan", "Magnite XV Premium", 2023, "petrol", "automatic", 5, 2000, 950000, 26000, 4.3),
    ],
    "Luxury Sedan": [
        ("Mercedes-Benz", "E-Class E 220d", 2024, "diesel", "automatic", 5, 11000, 7800000, 12000, 4.9),
        ("BMW", "5 Series 530i M Sport", 2024, "petrol", "automatic", 5, 11500, 7500000, 10000, 4.9),
        ("Audi", "A6 45 TFSI", 2024, "petrol", "automatic", 5, 9500, 6800000, 14000, 4.8),
        ("Lexus", "ES 300h Luxury", 2023, "hybrid", "automatic", 5, 10500, 6900000, 16000, 4.9),
        ("Jaguar", "XF R-Dynamic", 2023, "petrol", "automatic", 5, 9800, 7100000, 18000, 4.7),
        ("Genesis", "G80 2.5T", 2024, "petrol", "automatic", 5, 10000, 7200000, 9000, 4.8),
        ("Volvo", "S90 B5 Inscription", 2023, "hybrid", "automatic", 5, 9200, 6700000, 15000, 4.8),
        ("Porsche", "Panamera 4", 2023, "petrol", "automatic", 4, 22000, 16500000, 11000, 5.0),
        ("Maserati", "Ghibli Modena", 2022, "petrol", "automatic", 5, 19500, 12500000, 14000, 4.7),
        ("Alfa Romeo", "Giulia Veloce", 2023, "petrol", "automatic", 5, 12000, 7900000, 12000, 4.8),
    ],
    "Luxury SUV": [
        ("Land Rover", "Range Rover Sport Dynamic", 2024, "diesel", "automatic", 5, 18000, 17000000, 11000, 4.9),
        ("Porsche", "Cayenne Base", 2024, "petrol", "automatic", 5, 21000, 14500000, 9000, 5.0),
        ("Mercedes-Benz", "GLE 450 4MATIC", 2024, "petrol", "automatic", 5, 14000, 11000000, 13000, 4.9),
        ("BMW", "X5 xDrive40i", 2024, "petrol", "automatic", 5, 13500, 10500000, 15000, 4.8),
        ("Audi", "Q7 55 TFSI Quattro", 2023, "petrol", "automatic", 7, 12500, 9200000, 19000, 4.7),
        ("Volvo", "XC90 Recharge Ultimate", 2024, "hybrid", "automatic", 7, 13000, 10200000, 8000, 4.9),
        ("Lexus", "RX 500h F-Sport", 2024, "hybrid", "automatic", 5, 15000, 11800000, 10000, 4.9),
        ("Maserati", "Levante GT", 2023, "petrol", "automatic", 5, 19000, 14900000, 14000, 4.6),
        ("Aston Martin", "DBX 707", 2023, "petrol", "automatic", 5, 38000, 39000000, 6000, 5.0),
        ("Bentley", "Bentayga V8", 2023, "petrol", "automatic", 5, 45000, 42000000, 7000, 5.0),
    ],
    "Electric Vehicle": [
        ("Tesla", "Model 3 Long Range", 2024, "electric", "automatic", 5, 7500, 5200000, 9000, 4.9),
        ("Tata", "Nexon EV Empowered", 2025, "electric", "automatic", 5, 2600, 1950000, 7000, 4.7),
        ("Hyundai", "Ioniq 5 AWD", 2024, "electric", "automatic", 5, 6500, 4600000, 12000, 4.9),
        ("Kia", "EV6 GT-Line AWD", 2024, "electric", "automatic", 5, 8200, 6100000, 11000, 4.9),
        ("BYD", "Seal Performance", 2024, "electric", "automatic", 5, 7000, 5300000, 8000, 4.8),
        ("MG", "ZS EV Exclusive Plus", 2024, "electric", "automatic", 5, 3100, 2450000, 14000, 4.5),
        ("Mahindra", "XUV400 Pro", 2024, "electric", "automatic", 5, 2500, 1750000, 13000, 4.4),
        ("Polestar", "Polestar 2 Dual Motor", 2023, "electric", "automatic", 5, 8000, 5800000, 15000, 4.8),
        ("BMW", "i4 eDrive40", 2024, "electric", "automatic", 5, 11000, 7400000, 9000, 4.9),
        ("Audi", "e-tron GT Quattro", 2023, "electric", "automatic", 4, 25000, 17000000, 8000, 5.0),
    ],
    "Hybrid": [
        ("Toyota", "Urban Cruiser Hyryder Strong Hybrid", 2024, "hybrid", "automatic", 5, 2900, 1950000, 11000, 4.8),
        ("Honda", "City e:HEV ZX", 2024, "hybrid", "automatic", 5, 3200, 2050000, 12000, 4.8),
        ("Maruti Suzuki", "Grand Vitara Alpha+ Hybrid", 2024, "hybrid", "automatic", 5, 2800, 1980000, 13000, 4.7),
        ("Lexus", "NX 350h Overtrail", 2024, "hybrid", "automatic", 5, 11500, 7200000, 7000, 4.9),
        ("Hyundai", "Tucson Hybrid AWD", 2024, "hybrid", "automatic", 5, 4800, 3600000, 10000, 4.7),
        ("Kia", "Niro Hybrid EX", 2023, "hybrid", "automatic", 5, 3600, 2700000, 16000, 4.6),
        ("Ford", "Escape Hybrid Titanium", 2023, "hybrid", "automatic", 5, 4100, 3100000, 20000, 4.5),
        ("Subaru", "Crosstrek Hybrid", 2023, "hybrid", "automatic", 5, 3900, 2900000, 18000, 4.6),
        ("Nissan", "X-Trail e-POWER", 2024, "hybrid", "automatic", 7, 5200, 4900000, 8000, 4.6),
        ("Volvo", "XC60 Recharge T8", 2024, "hybrid", "automatic", 5, 12000, 6900000, 11000, 4.9),
    ],
    "MUV": [
        ("Toyota", "Innova Hycross ZX(O)", 2024, "hybrid", "automatic", 7, 4500, 3100000, 14000, 4.9),
        ("Maruti Suzuki", "Ertiga ZXi Plus", 2024, "petrol", "automatic", 7, 2400, 1150000, 19000, 4.5),
        ("Kia", "Carens Luxury Plus", 2024, "diesel", "automatic", 7, 2800, 1800000, 15000, 4.7),
        ("Mahindra", "Marazzo M6 Plus", 2023, "diesel", "manual", 8, 2300, 1400000, 28000, 4.3),
        ("Renault", "Triber RXZ", 2024, "petrol", "manual", 7, 1700, 850000, 16000, 4.2),
        ("Hyundai", "Staria Lounge", 2023, "diesel", "automatic", 7, 6800, 4800000, 15000, 4.8),
        ("Honda", "Freed Hybrid", 2023, "hybrid", "automatic", 6, 3200, 2100000, 22000, 4.6),
        ("Nissan", "Serena e-POWER", 2023, "hybrid", "automatic", 7, 4100, 3200000, 20000, 4.6),
        ("Mitsubishi", "Xpander Cross", 2023, "petrol", "automatic", 7, 2600, 1700000, 24000, 4.4),
        ("Mercedes-Benz", "V-Class Exclusive", 2023, "diesel", "automatic", 6, 22000, 14000000, 12000, 4.9),
    ],
    "Sports Car": [
        ("Porsche", "911 Carrera S", 2024, "petrol", "automatic", 4, 32000, 21000000, 8000, 5.0),
        ("Ford", "Mustang GT 5.0", 2023, "petrol", "automatic", 4, 16000, 7800000, 17000, 4.8),
        ("Chevrolet", "Corvette Stingray 3LT", 2023, "petrol", "automatic", 2, 21000, 13500000, 11000, 4.9),
        ("Nissan", "GT-R Nismo", 2022, "petrol", "automatic", 4, 28000, 22500000, 14000, 4.9),
        ("Toyota", "GR Supra 3.0", 2024, "petrol", "automatic", 2, 14000, 8500000, 9000, 4.8),
        ("BMW", "M4 Competition", 2024, "petrol", "automatic", 4, 24000, 15500000, 10000, 4.9),
        ("Jaguar", "F-Type R Dynamic P450", 2023, "petrol", "automatic", 2, 19000, 14500000, 13000, 4.8),
        ("Aston Martin", "Vantage V8", 2023, "petrol", "automatic", 2, 35000, 31000000, 7000, 5.0),
        ("Audi", "R8 V10 Performance", 2022, "petrol", "automatic", 2, 39000, 28000000, 12000, 5.0),
        ("Lotus", "Emira First Edition", 2024, "petrol", "manual", 2, 20000, 16000000, 5000, 4.9),
    ],
    "Convertible": [
        ("Mazda", "MX-5 Miata Club", 2024, "petrol", "manual", 2, 5800, 3900000, 9000, 4.9),
        ("BMW", "Z4 M40i Roadster", 2024, "petrol", "automatic", 2, 13500, 9200000, 10000, 4.9),
        ("Mercedes-Benz", "CLE 300 Cabriolet", 2024, "petrol", "automatic", 4, 15000, 10800000, 7000, 4.8),
        ("Audi", "A5 Cabriolet 45 TFSI", 2023, "petrol", "automatic", 4, 12000, 8200000, 14000, 4.7),
        ("Mini", "Cooper S Convertible", 2024, "petrol", "automatic", 4, 9200, 4700000, 8000, 4.8),
        ("Porsche", "718 Boxster GTS 4.0", 2024, "petrol", "automatic", 2, 26000, 15800000, 6000, 5.0),
        ("Ford", "Mustang Convertible EcoBoost", 2023, "petrol", "automatic", 4, 14000, 7400000, 16000, 4.7),
        ("Chevrolet", "Corvette Convertible 2LT", 2023, "petrol", "automatic", 2, 23000, 14800000, 9000, 4.9),
        ("Jaguar", "F-Type Convertible R-Dynamic", 2023, "petrol", "automatic", 2, 21000, 15800000, 12000, 4.8),
        ("Lexus", "LC 500 Convertible", 2023, "petrol", "automatic", 4, 34000, 24000000, 8000, 5.0),
    ]
}

# Image fallbacks for categories
CATEGORY_IMAGES = {
    "Hatchback": "https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?auto=format&fit=crop&w=800&q=80",
    "Sedan": "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=800&q=80",
    "SUV": "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=800&q=80",
    "Luxury Sedan": "https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=800&q=80",
    "Luxury SUV": "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=800&q=80",
    "Electric Vehicle": "https://images.unsplash.com/photo-1560958089-b8a1929cea89?auto=format&fit=crop&w=800&q=80",
    "Hybrid": "https://images.unsplash.com/photo-1590362891991-f776e747a588?auto=format&fit=crop&w=800&q=80",
    "MUV": "https://images.unsplash.com/photo-1502877338535-766e1452684a?auto=format&fit=crop&w=800&q=80",
    "Sports Car": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=800&q=80",
    "Convertible": "https://images.unsplash.com/photo-1508974239320-0a029497e820?auto=format&fit=crop&w=800&q=80",
}

def generate_listings():
    listings = []
    idx = 1
    
    # 1. Base 100 listings (10 categories x 10 distinct brands)
    for category, cars in CATEGORY_BRANDS.items():
        for brand, model, year, fuel, trans, seats, rent_p, buy_p, odo, rating in cars:
            car_id = f"CAR-{idx:03d}"
            idx += 1
            
            # Realistic condition: 2025 is new/nearly new, others used
            condition = "new" if year >= 2025 and odo < 10000 else "used"
            
            # Distribution of locations: primary Delhi, some Mumbai, Bangalore
            loc = "Delhi" if idx % 4 != 0 else ("Mumbai" if idx % 4 == 1 else "Bangalore")
            
            # Features depending on category
            feats = ["Touchscreen Infotainment", "Keyless Entry", "Rear Parking Sensors", "Dual Airbags"]
            if "Luxury" in category or "Sports" in category:
                feats.extend(["Panoramic Sunroof", "Ventilated Seats", "360-Degree Camera", "Harman Kardon Audio", "Adaptive Cruise Control"])
            elif category in ["SUV", "Hybrid", "Electric Vehicle"]:
                feats.extend(["Sunroof", "Wireless Phone Charging", "Apple CarPlay & Android Auto", "Hill Hold Assist"])
            else:
                feats.extend(["Bluetooth Connectivity", "Steering Mounted Controls", "Power Windows"])
            
            # Reserved dates for demo scenario availability testing:
            # For CAR-001 (Hyundai Creta in Delhi), ensure Dec 15-20, 2026 is fully open!
            # We add a previous booked range in November to prove date checking works.
            rent_avail = [
                {"start_date": "2026-11-01", "end_date": "2026-11-06", "booking_id": "BK-PAST-01"}
            ]
            if idx % 5 == 0:
                # Some cars are booked in mid-December to verify conflict detection
                rent_avail.append({"start_date": "2026-12-14", "end_date": "2026-12-18", "booking_id": "BK-CONFLICT-1"})

            listings.append({
                "id": car_id,
                "brand": brand,
                "model": model,
                "year": year,
                "category": category,
                "condition": condition,
                "fuel_type": fuel,
                "transmission": trans,
                "seats": seats,
                "location": loc,
                "rental_price_per_day": rent_p,
                "purchase_price": buy_p,
                "available_for_rent": True,
                "available_for_purchase": True,
                "rental_availability": rent_avail,
                "rating": rating,
                "review_count": 25 + (idx * 3) % 95,
                "image_url": CATEGORY_IMAGES[category],
                "features": feats,
                "mileage_kmpl": 16.5 if fuel != "electric" else None,
                "range_km": 450 if fuel == "electric" else None,
                "odometer_km": odo,
                "source": "Mock Marketplace",
                "listing_type": "mock"
            })
            
    # 2. Add 20 extra listings to enrich Delhi marketplace for budget & test scenarios
    extra_cars = [
        ("Hyundai", "Venue SX", 2024, "SUV", "petrol", "automatic", 5, "Delhi", 2400, 1150000, 11000, 4.6),
        ("Tata", "Punch Creative", 2024, "SUV", "petrol", "automatic", 5, "Delhi", 1900, 920000, 14000, 4.5),
        ("Kia", "Sonet HTX", 2025, "SUV", "diesel", "automatic", 5, "Delhi", 2600, 1280000, 6000, 4.7),
        ("Maruti Suzuki", "Brezza ZXi", 2024, "SUV", "petrol", "automatic", 5, "Delhi", 2500, 1220000, 13000, 4.5),
        ("Mahindra", "Scorpio-N Z8L", 2024, "SUV", "diesel", "automatic", 7, "Delhi", 3900, 2450000, 15000, 4.8),
        ("Toyota", "Innova Crysta VX", 2023, "MUV", "diesel", "automatic", 7, "Delhi", 4200, 2350000, 29000, 4.8),
        ("Skoda", "Octavia L&K", 2023, "Sedan", "petrol", "automatic", 5, "Delhi", 5200, 2950000, 21000, 4.8),
        ("Honda", "Elevate ZX", 2024, "SUV", "petrol", "automatic", 5, "Delhi", 2800, 1520000, 9500, 4.6),
        ("MG", "Astor Savvy", 2023, "SUV", "petrol", "automatic", 5, "Delhi", 2700, 1490000, 17000, 4.5),
        ("Volkswagen", "Tiguan Elegance", 2023, "SUV", "petrol", "automatic", 5, "Delhi", 5800, 3600000, 19000, 4.8),
        ("BMW", "3 Series Gran Limousine", 2024, "Luxury Sedan", "petrol", "automatic", 5, "Delhi", 10200, 6400000, 11000, 4.9),
        ("Mercedes-Benz", "GLA 220d 4MATIC", 2024, "Luxury SUV", "diesel", "automatic", 5, "Delhi", 9200, 5400000, 12000, 4.8),
        ("Audi", "Q3 40 TFSI", 2024, "Luxury SUV", "petrol", "automatic", 5, "Delhi", 8900, 5100000, 14000, 4.7),
        ("Volvo", "XC40 Recharge", 2024, "Electric Vehicle", "electric", "automatic", 5, "Delhi", 7900, 5600000, 10000, 4.8),
        ("Tata", "Tiago EV Tech LUX", 2024, "Electric Vehicle", "electric", "automatic", 5, "Delhi", 1800, 1150000, 12000, 4.5),
        ("Maruti Suzuki", "Baleno Alpha AMT", 2024, "Hatchback", "petrol", "automatic", 5, "Delhi", 2100, 940000, 13000, 4.5),
        ("Hyundai", "Grand i10 Nios Asta", 2023, "Hatchback", "petrol", "automatic", 5, "Delhi", 1800, 810000, 20000, 4.4),
        ("Toyota", "Vellfire VIP", 2024, "MUV", "hybrid", "automatic", 7, "Delhi", 25000, 13500000, 8000, 5.0),
        ("Porsche", "Macan GTS", 2024, "Luxury SUV", "petrol", "automatic", 5, "Delhi", 17500, 11200000, 9000, 4.9),
        ("Ford", "Mustang Mach 1", 2022, "Sports Car", "petrol", "automatic", 4, "Delhi", 19500, 8900000, 15000, 4.9)
    ]
    
    for brand, model, year, category, fuel, trans, seats, loc, rent_p, buy_p, odo, rating in extra_cars:
        car_id = f"CAR-{idx:03d}"
        idx += 1
        condition = "new" if year >= 2025 and odo < 10000 else "used"
        listings.append({
            "id": car_id,
            "brand": brand,
            "model": model,
            "year": year,
            "category": category,
            "condition": condition,
            "fuel_type": fuel,
            "transmission": trans,
            "seats": seats,
            "location": loc,
            "rental_price_per_day": rent_p,
            "purchase_price": buy_p,
            "available_for_rent": True,
            "available_for_purchase": True,
            "rental_availability": [
                {"start_date": "2026-11-01", "end_date": "2026-11-06", "booking_id": "BK-PAST-02"}
            ],
            "rating": rating,
            "review_count": 30 + (idx * 2) % 110,
            "image_url": CATEGORY_IMAGES[category],
            "features": ["Sunroof", "Touchscreen Infotainment", "Keyless Entry", "Apple CarPlay", "Rear Camera"],
            "mileage_kmpl": 17.2 if fuel != "electric" else None,
            "range_km": 420 if fuel == "electric" else None,
            "odometer_km": odo,
            "source": "Mock Marketplace",
            "listing_type": "mock"
        })
        
    return listings

def main():
    listings = generate_listings()
    out_path = Path(__file__).parent / "vehicles.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(listings, f, indent=2)
    print(f"Generated {len(listings)} listings in {out_path}")

if __name__ == "__main__":
    main()

