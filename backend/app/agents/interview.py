import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from ..models.preferences import (
    UserPreferences, IntentType, Budget, BudgetPeriod, RentalDetails, PurchaseDetails
)
from ..models.vehicle import VehicleCategory

CATEGORY_KEYWORD_MAP = {
    "hatchback": VehicleCategory.HATCHBACK,
    "sedan": VehicleCategory.SEDAN,
    "suv": VehicleCategory.SUV,
    "luxury sedan": VehicleCategory.LUXURY_SEDAN,
    "luxury suv": VehicleCategory.LUXURY_SUV,
    "electric": VehicleCategory.ELECTRIC_VEHICLE,
    "ev": VehicleCategory.ELECTRIC_VEHICLE,
    "electric vehicle": VehicleCategory.ELECTRIC_VEHICLE,
    "hybrid": VehicleCategory.HYBRID,
    "muv": VehicleCategory.MUV,
    "mpv": VehicleCategory.MUV,
    "sports car": VehicleCategory.SPORTS_CAR,
    "sports": VehicleCategory.SPORTS_CAR,
    "convertible": VehicleCategory.CONVERTIBLE,
    "cabriolet": VehicleCategory.CONVERTIBLE,
    "roadster": VehicleCategory.CONVERTIBLE,
}

KNOWN_BRANDS = [
    "maruti", "maruti suzuki", "hyundai", "tata", "toyota", "kia", "mahindra",
    "honda", "volkswagen", "skoda", "mg", "bmw", "mercedes", "mercedes-benz",
    "audi", "porsche", "volvo", "lexus", "jaguar", "land rover", "ford",
    "byd", "tesla", "nissan", "renault", "mini", "aston martin", "bentley",
    "lotus", "maserati", "genesis", "chevrolet", "mazda", "subaru"
]

class AdaptiveInterviewAgent:
    @staticmethod
    def extract_preferences(user_text: str, current_prefs: UserPreferences) -> Tuple[UserPreferences, List[str]]:
        """
        Parses user's natural language input, updates preference model incrementally,
        and returns updated preferences alongside a list of newly extracted fields.
        """
        text_lower = user_text.lower()
        extracted_fields = []

        # 1. Intent Detection
        if any(w in text_lower for w in ["buy", "purchase", "own", "buying", "second hand"]):
            if current_prefs.intent != IntentType.BUY:
                current_prefs.intent = IntentType.BUY
                current_prefs.rental_details = None
                if not current_prefs.purchase_details:
                    current_prefs.purchase_details = PurchaseDetails()
                extracted_fields.append("intent: BUY")
        elif any(w in text_lower for w in ["rent", "hire", "rental", "renting"]):
            if current_prefs.intent != IntentType.RENT:
                current_prefs.intent = IntentType.RENT
                current_prefs.purchase_details = None
                if not current_prefs.rental_details:
                    current_prefs.rental_details = RentalDetails()
                extracted_fields.append("intent: RENT")

        # 2. Category Detection
        # Check longer phrases first
        for key, cat_enum in sorted(CATEGORY_KEYWORD_MAP.items(), key=lambda x: -len(x[0])):
            if re.search(r'\b' + re.escape(key) + r'\b', text_lower):
                current_prefs.category = cat_enum
                extracted_fields.append(f"category: {cat_enum.value}")
                break

        # 3. Location Detection
        for loc in ["Delhi", "Mumbai", "Bangalore", "Bengaluru", "Hyderabad", "Chennai", "Pune", "Goa", "Jaipur"]:
            if re.search(r'\b' + re.escape(loc.lower()) + r'\b', text_lower):
                std_loc = "Bangalore" if loc.lower() == "bengaluru" else loc
                current_prefs.location = std_loc
                extracted_fields.append(f"location: {std_loc}")
                break

        # 4. Transmission
        if "automatic" in text_lower or "auto" in text_lower:
            current_prefs.transmission = "automatic"
            extracted_fields.append("transmission: automatic")
        elif "manual" in text_lower:
            current_prefs.transmission = "manual"
            extracted_fields.append("transmission: manual")

        # 5. Fuel Type
        for fuel in ["petrol", "diesel", "electric", "hybrid", "cng"]:
            if re.search(r'\b' + fuel + r'\b', text_lower):
                current_prefs.fuel_type = fuel
                extracted_fields.append(f"fuel_type: {fuel}")
                break

        # 6. Brands
        for b in KNOWN_BRANDS:
            if re.search(r'\b' + re.escape(b) + r'\b', text_lower):
                std_brand = b.title()
                if std_brand not in current_prefs.preferred_brands:
                    current_prefs.preferred_brands.append(std_brand)
                    extracted_fields.append(f"brand: {std_brand}")

        # 7. Budget Detection
        # Match explicit budget mentions first: e.g. "budget is ₹3000", "₹3,000 per day", "under 3000", "3000/day"
        # Match Lakhs: e.g. "15 lakh", "15 lakhs", "15l"
        lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakh|lacs?|l\b)', text_lower)
        if lakh_match:
            amount = float(lakh_match.group(1)) * 100000.0
            current_prefs.budget = Budget(amount=amount, currency="INR", period=BudgetPeriod.TOTAL)
            if current_prefs.intent == IntentType.BUY:
                if not current_prefs.purchase_details:
                    current_prefs.purchase_details = PurchaseDetails()
                current_prefs.purchase_details.purchase_budget = amount
            extracted_fields.append(f"budget: ₹{amount:,.0f} total")
        else:
            # Check for explicitly labeled budget or currency: "budget of ...", "budget is ...", "₹...", "rs ...", "... /day"
            explicit_budget_match = re.search(
                r'(?:budget\s*(?:is|of|:)?\s*|under\s+|max(?:imum)?\s+)?(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:,\d{3})+|\d+)\s*(?:k\b|k\s+)?(?:\s*(?:per\s*day|/day|daily))?',
                text_lower
            )
            # Find all numbers specifically associated with budget or currency symbols
            budget_candidates = re.findall(
                r'(?:budget\s*(?:is|of|:)?\s*(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:,\d{3})+|\d+)|(?:₹|rs\.?|inr)\s*(\d{1,3}(?:,\d{3})+|\d+)|(\d{1,3}(?:,\d{3})+|\d+)\s*(?:per\s*day|/day|daily))',
                text_lower
            )
            
            val = None
            if budget_candidates:
                # Find the non-empty captured group
                for match_tuple in budget_candidates:
                    candidate = next((g for g in match_tuple if g), None)
                    if candidate:
                        cand_val = float(candidate.replace(",", ""))
                        if cand_val != 2025 and cand_val != 2026: # guard against accidental year
                            val = cand_val
                            break

            if val is None:
                # Fallback to k notation: "3k"
                k_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*k\b', text_lower)
                if k_match:
                    val = float(k_match.group(1)) * 1000.0

            if val and val > 100:
                is_daily = "per day" in text_lower or "/day" in text_lower or "daily" in text_lower or current_prefs.intent == IntentType.RENT
                period = BudgetPeriod.PER_DAY if is_daily else BudgetPeriod.TOTAL
                current_prefs.budget = Budget(amount=val, currency="INR", period=period)
                if current_prefs.intent == IntentType.BUY and not is_daily:
                    if not current_prefs.purchase_details:
                        current_prefs.purchase_details = PurchaseDetails()
                    current_prefs.purchase_details.purchase_budget = val
                extracted_fields.append(f"budget: ₹{val:,.0f} {period.value}")

        # 8. Rental Specific: Duration and Dates
        if current_prefs.intent == IntentType.RENT:
            if not current_prefs.rental_details:
                current_prefs.rental_details = RentalDetails()

            # Duration: "five days", "5 days", "for 5 days"
            word_to_num = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
            dur_match = re.search(r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*days?', text_lower)
            if dur_match:
                raw_d = dur_match.group(1)
                days = word_to_num.get(raw_d, int(raw_d) if raw_d.isdigit() else 1)
                current_prefs.rental_details.rental_duration_days = days
                extracted_fields.append(f"duration: {days} days")

            # Dates: "15 december 2026", "december 15, 2026", "15th dec 2026"
            date_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s*(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*(\d{4})?', text_lower)
            if date_match:
                day = int(date_match.group(1))
                month_str = date_match.group(2)[:3]
                year = int(date_match.group(3)) if date_match.group(3) else 2026
                month_num = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"].index(month_str) + 1
                try:
                    start_dt = datetime(year, month_num, day)
                    current_prefs.rental_details.pickup_date = start_dt.strftime("%Y-%m-%d")
                    # If duration is already known, compute return date
                    if current_prefs.rental_details.rental_duration_days:
                        end_dt = start_dt + timedelta(days=current_prefs.rental_details.rental_duration_days)
                        current_prefs.rental_details.return_date = end_dt.strftime("%Y-%m-%d")
                    extracted_fields.append(f"pickup_date: {current_prefs.rental_details.pickup_date}")
                except ValueError:
                    pass

        # 9. Purchase Specific: Condition (used vs new)
        if current_prefs.intent == IntentType.BUY:
            if not current_prefs.purchase_details:
                current_prefs.purchase_details = PurchaseDetails()
            if any(w in text_lower for w in ["used", "pre-owned", "second hand", "preowned"]):
                current_prefs.purchase_details.condition = "used"
                extracted_fields.append("condition: used")
            elif "new" in text_lower:
                current_prefs.purchase_details.condition = "new"
                extracted_fields.append("condition: new")

        # 10. Check Missing Fields & Completeness
        missing = AdaptiveInterviewAgent.check_missing_fields(current_prefs)
        current_prefs.interview_complete = (len(missing) == 0)

        return current_prefs, extracted_fields

    @staticmethod
    def check_missing_fields(prefs: UserPreferences) -> List[str]:
        missing = []
        if not prefs.location:
            missing.append("location")
        if not prefs.category:
            missing.append("category")
        if not prefs.budget or prefs.budget.amount <= 0:
            missing.append("budget")

        if prefs.intent == IntentType.RENT:
            if not prefs.rental_details or not prefs.rental_details.pickup_date:
                missing.append("pickup_date")
            if not prefs.rental_details or not prefs.rental_details.rental_duration_days:
                missing.append("rental_duration")
        else: # BUY
            if not prefs.purchase_details or not prefs.purchase_details.condition:
                missing.append("condition")

        return missing

    @staticmethod
    def generate_followup_question(prefs: UserPreferences) -> str:
        missing = AdaptiveInterviewAgent.check_missing_fields(prefs)
        if not missing:
            return "All set! I have gathered your key requirements. Let's find your perfect match."

        questions = []
        if "location" in missing:
            questions.append("Which city will you be driving in (e.g., Delhi, Mumbai, Bangalore)?")
        if "category" in missing:
            questions.append("What style of vehicle are you looking for (e.g., SUV, Sedan, EV, Hatchback)?")
        if "budget" in missing:
            if prefs.intent == IntentType.RENT:
                questions.append("What is your approximate daily budget in ₹?")
            else:
                questions.append("What is your target purchase budget (e.g., ₹15 Lakh)?")
        if "pickup_date" in missing and prefs.intent == IntentType.RENT:
            questions.append("What is your intended pickup date (e.g., 15 December 2026)?")
        if "rental_duration" in missing and prefs.intent == IntentType.RENT:
            questions.append("How many days will you need the vehicle for?")
        if "condition" in missing and prefs.intent == IntentType.BUY:
            questions.append("Are you interested in a brand-new vehicle or a quality pre-owned car?")

        return " ".join(questions)
