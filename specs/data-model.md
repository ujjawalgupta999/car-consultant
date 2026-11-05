# AMULATE SUMMER HACKATHON 2026: DATA MODEL SPECIFICATION
## AI-Powered Car Rental and Purchase Consultant

---

## 1. Overview
The data models are specified using Pydantic (v2) conventions for the Python backend and mirrored in TypeScript interfaces for the React frontend.

---

## 2. Core Entities

### 2.1 Vehicle Listing (`Vehicle`)
```json
{
  "id": "CAR-001",
  "brand": "Hyundai",
  "model": "Creta",
  "year": 2025,
  "category": "SUV",
  "condition": "used",
  "fuel_type": "petrol",
  "transmission": "automatic",
  "seats": 5,
  "location": "Delhi",
  "rental_price_per_day": 2800,
  "purchase_price": 1450000,
  "available_for_rent": true,
  "available_for_purchase": true,
  "rental_availability": [
    {
      "start_date": "2026-11-10",
      "end_date": "2026-11-14",
      "booking_id": "BK-EXISTING-1"
    }
  ],
  "rating": 4.7,
  "review_count": 86,
  "image_url": "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=800&q=80",
  "features": ["Sunroof", "Apple CarPlay", "Ventilated Seats", "360 Camera", "ADAS Level 2"],
  "mileage_kmpl": 17.0,
  "odometer_km": 12400,
  "source": "Mock Marketplace",
  "listing_type": "mock"
}
```

### 2.2 Category Enumeration (10 Required Categories)
```python
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
```

### 2.3 User Preferences (`UserPreferences`)
```json
{
  "session_id": "sess_89a3f2b1",
  "intent": "rent",
  "location": "Delhi",
  "category": "SUV",
  "budget": {
    "amount": 3000,
    "currency": "INR",
    "period": "per_day"
  },
  "fuel_type": "any",
  "transmission": "automatic",
  "seating_capacity": 5,
  "preferred_brands": ["Hyundai", "Tata", "Kia"],
  "additional_preferences": ["Sunroof", "GPS"],
  "interview_complete": true,
  
  "rental_details": {
    "pickup_date": "2026-12-15",
    "return_date": "2026-12-20",
    "rental_duration_days": 5,
    "pickup_location": "Delhi Airport T3",
    "return_location": "Delhi Airport T3"
  },
  
  "purchase_details": null
}
```

### 2.4 Purchase Details (`PurchasePreferences`)
```json
{
  "purchase_budget": 1500000,
  "expected_purchase_date": "2026-12-31",
  "condition": "used",
  "financing_preference": "loan",
  "intended_ownership_use": "family_daily_commute"
}
```

### 2.5 Workflow State Machine (`WorkflowState`)
```python
class WorkflowState(str, Enum):
    NEW = "NEW"
    INTERVIEWING = "INTERVIEWING"
    READY_TO_SEARCH = "READY_TO_SEARCH"
    SEARCHING = "SEARCHING"
    RANKING = "RANKING"
    RECOMMENDATIONS_READY = "RECOMMENDATIONS_READY"
    VEHICLE_SELECTED = "VEHICLE_SELECTED"
    BOOKING_IN_PROGRESS = "BOOKING_IN_PROGRESS"
    CHECKOUT_READY = "CHECKOUT_READY"
    PAYMENT_PROCESSING = "PAYMENT_PROCESSING"
    CONFIRMED = "CONFIRMED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    CANCELLED = "CANCELLED"
```

### 2.6 Recommendation Item (`RecommendationItem`)
```json
{
  "vehicle": { ... },
  "match_score": 94.5,
  "score_breakdown": {
    "budget_score": 30.0,
    "category_score": 25.0,
    "preference_score": 18.0,
    "rating_score": 14.1,
    "brand_score": 7.4
  },
  "estimated_total_cost": 15000,
  "currency": "INR",
  "positive_matches": [
    "Automatic transmission requested and present",
    "Under daily budget of ₹3,000 (₹2,800/day)",
    "Preferred brand Hyundai",
    "Available for full 5-day duration in Delhi"
  ],
  "trade_offs": [
    "Used vehicle condition (12,400 km)",
    "Fuel type is Petrol (Hybrid not available at this budget)"
  ],
  "explanation": "This Hyundai Creta is an outstanding match for your Delhi trip. It satisfies your SUV and automatic transmission needs while coming in ₹200/day under budget. All dates from Dec 15 to Dec 20 are verified open.",
  "availability_status": "AVAILABLE"
}
```

### 2.7 Booking Entity (`RentalBooking`)
```json
{
  "id": "BK-2026-90412",
  "session_id": "sess_89a3f2b1",
  "vehicle_id": "CAR-001",
  "customer_name": "Rohan Sharma",
  "customer_email": "rohan.sharma@example.com",
  "customer_phone": "+91 98765 43210",
  "driver_license_number": "DL-1420110012345",
  "pickup_date": "2026-12-15",
  "return_date": "2026-12-20",
  "duration_days": 5,
  "pickup_location": "Delhi Airport T3",
  "return_location": "Delhi Airport T3",
  "base_rate_per_day": 2800,
  "subtotal": 14000,
  "add_ons": [
    {"id": "addon_insurance_full", "title": "Zero Depreciation Cover", "amount": 1500}
  ],
  "taxes_and_fees": 1860,
  "total_amount": 17360,
  "currency": "INR",
  "status": "CONFIRMED",
  "idempotency_key": "idemp_bk_89a3f2b1_1",
  "payment_reference": "TXN-MOCK-782910",
  "created_at": "2026-11-04T16:15:00Z"
}
```

### 2.8 Purchase Order Entity (`PurchaseOrder`)
```json
{
  "id": "ORD-2026-30214",
  "session_id": "sess_91b4c3d2",
  "vehicle_id": "CAR-001",
  "customer_name": "Priya Patel",
  "customer_email": "priya.patel@example.com",
  "customer_phone": "+91 98111 22334",
  "pan_or_id": "ABCDE1234F",
  "purchase_price": 1450000,
  "booking_token_amount": 25000,
  "financing_selected": true,
  "status": "CONFIRMED",
  "idempotency_key": "idemp_ord_91b4c3d2_1",
  "payment_reference": "TXN-MOCK-991204",
  "created_at": "2026-11-04T16:20:00Z"
}
```

### 2.9 Mock Payment Record (`MockPayment`)
```json
{
  "id": "PAY-2026-55192",
  "transaction_reference": "TXN-MOCK-782910",
  "order_or_booking_id": "BK-2026-90412",
  "amount": 17360,
  "currency": "INR",
  "payment_method": "upi_simulator",
  "simulated_scenario": "success",
  "status": "SUCCESS",
  "idempotency_key": "idemp_pay_89a3f2b1_1",
  "gateway_response": {
    "simulated_auth_code": "AUTH_9921_OK",
    "timestamp": "2026-11-04T16:15:30Z",
    "disclaimer": "Simulated payment transaction - No actual financial charge."
  },
  "created_at": "2026-11-04T16:15:30Z"
}
```

