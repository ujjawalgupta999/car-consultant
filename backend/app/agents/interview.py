import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from ..models.preferences import (
    UserPreferences, IntentType, Budget, BudgetPeriod, RentalDetails, PurchaseDetails, SellDetails
)
from ..models.vehicle import VehicleCategory

CATEGORY_KEYWORD_MAP = {
    "hatchback": VehicleCategory.HATCHBACK,
    "hatchbacks": VehicleCategory.HATCHBACK,
    "sedan": VehicleCategory.SEDAN,
    "sedans": VehicleCategory.SEDAN,
    "suv": VehicleCategory.SUV,
    "suvs": VehicleCategory.SUV,
    "luxury sedan": VehicleCategory.LUXURY_SEDAN,
    "luxury sedans": VehicleCategory.LUXURY_SEDAN,
    "luxury suv": VehicleCategory.LUXURY_SUV,
    "luxury suvs": VehicleCategory.LUXURY_SUV,
    "electric": VehicleCategory.ELECTRIC_VEHICLE,
    "ev": VehicleCategory.ELECTRIC_VEHICLE,
    "evs": VehicleCategory.ELECTRIC_VEHICLE,
    "electric vehicle": VehicleCategory.ELECTRIC_VEHICLE,
    "electric vehicles": VehicleCategory.ELECTRIC_VEHICLE,
    "hybrid": VehicleCategory.HYBRID,
    "hybrids": VehicleCategory.HYBRID,
    "muv": VehicleCategory.MUV,
    "muvs": VehicleCategory.MUV,
    "mpv": VehicleCategory.MUV,
    "mpvs": VehicleCategory.MUV,
    "sports car": VehicleCategory.SPORTS_CAR,
    "sports cars": VehicleCategory.SPORTS_CAR,
    "sports": VehicleCategory.SPORTS_CAR,
    "convertible": VehicleCategory.CONVERTIBLE,
    "convertibles": VehicleCategory.CONVERTIBLE,
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

WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10
}

class AdaptiveInterviewAgent:
    @staticmethod
    def extract_preferences(user_text: str, current_prefs: UserPreferences) -> Tuple[UserPreferences, List[str]]:
        """
        Parses natural language user messages using semantic and syntactic entity extraction.
        Merges new entities into current_prefs, preserving all previously collected preferences.
        """
        text_lower = user_text.lower()
        extracted_fields = []

        # ---------------------------------------------------------
        # 1. Intent Detection
        # ---------------------------------------------------------
        purchase_hist_patterns = [
            r'\b(my\s+purchases?|purchased\s+cars?|bought\s+cars?|purchase\s+history|show\s+(?:me\s+)?(?:my\s+)?purchases?|what\s+cars?\s+(?:did\s+i|have\s+i)\s+bought)\b',
            r'\b(view\s+(?:my\s+)?purchases?|my\s+orders?|order\s+history)\b'
        ]
        rental_hist_patterns = [
            r'\b(my\s+rentals?|previous\s+rentals?|rental\s+history|show\s+(?:me\s+)?(?:my\s+)?rentals?|past\s+rentals?)\b'
        ]
        selling_hist_patterns = [
            r'\b(my\s+listings?|selling\s+listings?|cars\s+i(?:\x27m|\s+am)?\s+selling|show\s+(?:me\s+)?(?:my\s+)?listings?|my\s+cars\s+for\s+sale)\b'
        ]
        sell_patterns = [
            r'\b(sell|selling|resell|reselling|trade\s*in|list\s+(?:my\s+)?car|put\s+up\s+for\s+sale)\b',
            r'\bwant\s+to\s+sell\b',
            r'\bhelp\s+(?:me\s+)?sell\b',
            r'\bsell\s+a\s+(?:car|sedan|suv|vehicle|hatchback)\b'
        ]
        compare_patterns = [
            r'\b(compare|comparison|versus|\bvs\b|difference\s+between)\b'
        ]
        buy_patterns = [
            r'\b(buy|buying|purchase|purchasing|acquire|ordering)\b',
            r'\b(second\s*hand|pre-?owned|preowned)\b',
            r'\b(want\s+to\s+own|looking\s+to\s+own)\b',
            r'\b(want\s+to\s+but|looking\s+to\s+but)\b', # typo "but" for "buy"
            r'\b(?:but|by)\s+(?:an?\s+)?(?:car|vehicle|sedan|suv|hatchback|ev|convertible)\b',
            r'\bi\s+want\s+to\s+but\b'
        ]
        rent_patterns = [
            r'\b(rent|rental|renting|hire|hiring|lease|leasing)\b',
            r'\b(per\s*day|/day|daily)\b',
            r'\b(?:for\s+)?(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*days?\b',
            r'\bstarting\s+\d{1,2}\b'
        ]

        # Check negated intents: "instead of buying", "rather than renting", etc.
        negated_buy = bool(re.search(r'(?:instead\s+of|rather\s+than|not)\s+(?:buying|buy|purchase)', text_lower))
        negated_rent = bool(re.search(r'(?:instead\s+of|rather\s+than|not)\s+(?:renting|rent|hire|lease)', text_lower))
        negated_sell = bool(re.search(r'(?:instead\s+of|rather\s+than|not)\s+(?:selling|sell)', text_lower))

        if any(re.search(pat, text_lower) for pat in purchase_hist_patterns):
            current_prefs.intent = IntentType.PURCHASE_HISTORY
            extracted_fields.append("intent: PURCHASE_HISTORY")
        elif any(re.search(pat, text_lower) for pat in rental_hist_patterns):
            current_prefs.intent = IntentType.RENTAL_HISTORY
            extracted_fields.append("intent: RENTAL_HISTORY")
        elif any(re.search(pat, text_lower) for pat in selling_hist_patterns):
            current_prefs.intent = IntentType.SELLING_HISTORY
            extracted_fields.append("intent: SELLING_HISTORY")
        elif any(re.search(pat, text_lower) for pat in sell_patterns) and not negated_sell:
            current_prefs.intent = IntentType.SELL
            if not current_prefs.sell_details:
                current_prefs.sell_details = SellDetails()
            extracted_fields.append("intent: SELL")
        elif any(re.search(pat, text_lower) for pat in compare_patterns):
            current_prefs.intent = IntentType.COMPARE
            extracted_fields.append("intent: COMPARE")
        else:
            has_buy_signal = any(re.search(pat, text_lower) for pat in buy_patterns) and not negated_buy
            has_rent_signal = any(re.search(pat, text_lower) for pat in rent_patterns) and not negated_rent

            if has_rent_signal or has_buy_signal:
                current_prefs.intent = IntentType.BUY
                current_prefs.rental_details = None
                current_prefs.sell_details = None
                current_prefs.rental_start_date = None
                current_prefs.rental_end_date = None
                if not current_prefs.purchase_details:
                    current_prefs.purchase_details = PurchaseDetails()
                extracted_fields.append("intent: BUY")

        # ---------------------------------------------------------
        # 2. Seating Capacity Semantic Extraction
        # ---------------------------------------------------------
        # Supports:
        # - "for the seating of 2 people"
        # - "for two people" / "for 4 passengers"
        # - "five-seater" / "two-seater"
        # - "for a family of five"
        # - "me and one other person" / "couple" -> 2
        # - "only two seats are required" / "small car with two seats"
        # - "actually, change the seating to four people"
        # - "I don't need a family car" -> implies small / 2-seater if small car mentioned
        detected_seats = None

        # Check explicit changes or mentions of seating count
        num_pattern = r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)'
        seating_regexes = [
            # "change the seating to four people", "change seating to 4"
            rf'change\s+(?:the\s+)?seating\s+(?:to\s+)?{num_pattern}',
            # "for the seating of 2 people", "seating capacity of 4", "seating for 5"
            rf'(?:seating(?:\s+capacity)?\s+(?:of|for)\s+|seats?\s+(?:of|for)\s+){num_pattern}',
            # "for two people", "for 4 passengers", "for five occupants"
            rf'(?:for\s+){num_pattern}\s+(?:people|persons?|passengers?|occupants?)',
            # "two-seater", "5-seater", "two seater", "5 seater"
            rf'{num_pattern}(?:\s*|-)(?:seater|seat\b)',
            # "family of five", "family of 4"
            rf'(?:family\s+of\s+){num_pattern}',
            # "with two seats", "have 2 seats", "need 4 seats", "want 2 seats"
            rf'(?:with|have|need|require|want|need\s+a\s+car\s+for)\s+(?:only\s+|just\s+)?{num_pattern}\s+seats?',
            # "only two seats are required", "just 2 seats needed"
            rf'(?:only|just)\s+{num_pattern}\s+seats?\s+(?:are\s+)?(?:required|needed)',
        ]

        for s_reg in seating_regexes:
            match = re.search(s_reg, text_lower)
            if match:
                raw_seat = match.group(1).lower()
                detected_seats = WORD_TO_NUM.get(raw_seat, int(raw_seat) if raw_seat.isdigit() else None)
                if detected_seats:
                    break

        # Semantic natural phrases implying 2 occupants
        if detected_seats is None:
            if re.search(r'\b(me\s+and\s+one\s+(?:other\s+)?person|couple|just\s+two\s+of\s+us|only\s+two\s+of\s+us|me\s+and\s+my\s+(?:wife|husband|partner))\b', text_lower):
                detected_seats = 2
            elif re.search(r'\b(small\s+car\s+with\s+two\s+seats|two\s+seats\s+only)\b', text_lower):
                detected_seats = 2
            elif "don't need a family car" in text_lower or "do not need a family car" in text_lower:
                if "small" in text_lower or "two" in text_lower or "couple" in text_lower:
                    detected_seats = 2

        if detected_seats and detected_seats > 0:
            current_prefs.seating_capacity = detected_seats
            current_prefs.seating_match_type = "exact"
            num_words = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight"}
            word_repr = num_words.get(detected_seats, str(detected_seats))
            extracted_fields.append(f"seating_capacity: {detected_seats} ({word_repr} people)")

        # ---------------------------------------------------------
        # 3. Transmission Detection
        # ---------------------------------------------------------
        if re.search(r'\b(automatic|auto)\b', text_lower):
            current_prefs.transmission = "automatic"
            extracted_fields.append("transmission: automatic")
        elif re.search(r'\b(manual|stick\s*shift)\b', text_lower):
            current_prefs.transmission = "manual"
            extracted_fields.append("transmission: manual")

        # ---------------------------------------------------------
        # 4. Fuel Type Detection
        # ---------------------------------------------------------
        if re.search(r'\b(electric\s+car|electric\s+vehicle|electric\s+suv|electric|evs?)\b', text_lower):
            current_prefs.fuel_type = "ELECTRIC"
            extracted_fields.append("fuel_type: ELECTRIC")
        elif re.search(r'\b(hybrid|strong\s+hybrid)\b', text_lower):
            current_prefs.fuel_type = "HYBRID"
            extracted_fields.append("fuel_type: HYBRID")
        elif re.search(r'\b(petrol|gasoline)\b', text_lower):
            current_prefs.fuel_type = "PETROL"
            extracted_fields.append("fuel_type: PETROL")
        elif re.search(r'\b(diesel)\b', text_lower):
            current_prefs.fuel_type = "DIESEL"
            extracted_fields.append("fuel_type: DIESEL")
        elif re.search(r'\b(cng)\b', text_lower):
            current_prefs.fuel_type = "CNG"
            extracted_fields.append("fuel_type: CNG")

        # ---------------------------------------------------------
        # 5. Category Detection
        # ---------------------------------------------------------
        # Handle negation phrases like "instead of <category>" or "not <category>"
        negated_categories = set()
        for neg_match in re.finditer(r'(?:instead\s+of|rather\s+than|not)\s+([a-z\s]+)', text_lower):
            negated_phrase = neg_match.group(1)
            for k in CATEGORY_KEYWORD_MAP.keys():
                if k in negated_phrase:
                    negated_categories.add(k)

        # Check positive matches, sorted by length descending
        for key, cat_enum in sorted(CATEGORY_KEYWORD_MAP.items(), key=lambda x: -len(x[0])):
            if key in negated_categories:
                continue
            if key in ["electric", "ev", "evs", "electric vehicle", "electric vehicles", "hybrid", "hybrids"]:
                has_other_style = any(
                    bs in text_lower for bs in ["suv", "sedan", "hatchback", "convertible", "sports", "muv"]
                )
                if has_other_style:
                    continue
            if re.search(r'\b' + re.escape(key) + r'\b', text_lower):
                current_prefs.category = cat_enum
                current_prefs.vehicle_category = cat_enum.value
                extracted_fields.append(f"vehicle_category: {cat_enum.value}")
                break

        # ---------------------------------------------------------
        # 6. Location Detection
        # ---------------------------------------------------------
        for loc in ["Delhi", "Mumbai", "Bangalore", "Bengaluru", "Hyderabad", "Chennai", "Pune", "Goa", "Jaipur"]:
            if re.search(r'\b' + re.escape(loc.lower()) + r'\b', text_lower):
                std_loc = "Bangalore" if loc.lower() == "bengaluru" else loc
                if current_prefs.location != std_loc:
                    current_prefs.location = std_loc
                    extracted_fields.append(f"location: {std_loc}")
                break

        # ---------------------------------------------------------
        # 7. Brand Preference
        # ---------------------------------------------------------
        for b in KNOWN_BRANDS:
            if re.search(r'\b' + re.escape(b) + r'\b', text_lower):
                std_brand = b.title()
                if std_brand not in current_prefs.preferred_brands:
                    current_prefs.preferred_brands.append(std_brand)
                    current_prefs.brand_preference = std_brand
                    extracted_fields.append(f"brand_preference: {std_brand}")

        # ---------------------------------------------------------
        # 8. Budget Min & Max Detection
        # ---------------------------------------------------------
        # A) Range: "between 10 and 15 lakh", "10 to 15 lakh", "10-15 lakh"
        range_lakh = re.search(r'between\s+(\d+(?:\.\d+)?)\s*(?:and|to|-)\s*(\d+(?:\.\d+)?)\s*(?:lakh|lacs?|l\b)', text_lower)
        if not range_lakh:
            range_lakh = re.search(r'(\d+(?:\.\d+)?)\s*(?:to|-)\s*(\d+(?:\.\d+)?)\s*(?:lakh|lacs?|l\b)', text_lower)

        if range_lakh:
            b_min = float(range_lakh.group(1)) * 100000.0
            b_max = float(range_lakh.group(2)) * 100000.0
            current_prefs.budget_min = b_min
            current_prefs.budget_max = b_max
            current_prefs.budget = Budget(amount=b_max, currency="INR", period=BudgetPeriod.TOTAL)
            extracted_fields.append(f"budget: ₹{b_min/100000:.1f}L – ₹{b_max/100000:.1f}L")
        else:
            # Single upper bound in Lakhs: "under 15 lakh", "under 10 lakh", "budget is 10 lakh"
            single_lakh = re.search(r'(?:under|below|max(?:imum)?|budget\s*(?:is|of|:)?\s*)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lacs?|l\b)', text_lower)
            if single_lakh and float(single_lakh.group(1)) > 0:
                amount = float(single_lakh.group(1)) * 100000.0
                current_prefs.budget_max = amount
                current_prefs.budget = Budget(amount=amount, currency="INR", period=BudgetPeriod.TOTAL)
                if current_prefs.intent == "BUY" or current_prefs.intent == IntentType.BUY:
                    if not current_prefs.purchase_details:
                        current_prefs.purchase_details = PurchaseDetails()
                    current_prefs.purchase_details.purchase_budget = amount
                extracted_fields.append(f"budget_max: ₹{amount/100000:.1f} Lakh")
            else:
                # Daily / Numeric fallback: "under 3000/day", "₹3,000 per day"
                budget_candidates = re.findall(
                    r'(?:budget\s*(?:is|of|:)?\s*(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:,\d{3})+|\d+)|(?:₹|rs\.?|inr)\s*(\d{1,3}(?:,\d{3})+|\d+)|(\d{1,3}(?:,\d{3})+|\d+)\s*(?:per\s*day|/day|daily))',
                    text_lower
                )
                val = None
                if budget_candidates:
                    for match_tuple in budget_candidates:
                        candidate = next((g for g in match_tuple if g), None)
                        if candidate:
                            cand_val = float(candidate.replace(",", ""))
                            if cand_val != 2025 and cand_val != 2026: # guard against year
                                val = cand_val
                                break

                if val is None:
                    k_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*k\b', text_lower)
                    if k_match:
                        val = float(k_match.group(1)) * 1000.0

                if val and val > 100:
                    is_daily = "per day" in text_lower or "/day" in text_lower or "daily" in text_lower or current_prefs.intent == "RENT"
                    period = BudgetPeriod.PER_DAY if is_daily else BudgetPeriod.TOTAL
                    current_prefs.budget_max = val
                    current_prefs.budget = Budget(amount=val, currency="INR", period=period)
                    extracted_fields.append(f"budget_max: ₹{val:,.0f} {period.value}")

        # ---------------------------------------------------------
        # 9. Rental Specific: Duration and Dates
        # ---------------------------------------------------------
        is_rent_active = (current_prefs.intent == "RENT" or current_prefs.intent == IntentType.RENT)
        if is_rent_active:
            if not current_prefs.rental_details:
                current_prefs.rental_details = RentalDetails()

            # Duration: "for three days", "for 3 days", "3 days"
            dur_match = re.search(r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*days?', text_lower)
            if dur_match:
                raw_d = dur_match.group(1)
                days = WORD_TO_NUM.get(raw_d, int(raw_d) if raw_d.isdigit() else 1)
                current_prefs.rental_details.rental_duration_days = days
                extracted_fields.append(f"rental_duration: {days} days")

            # Dates: "15 december 2026", "december 15, 2026"
            date_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s*(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*(\d{4})?', text_lower)
            if date_match:
                day = int(date_match.group(1))
                month_str = date_match.group(2)[:3]
                year = int(date_match.group(3)) if date_match.group(3) else 2026
                month_num = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"].index(month_str) + 1
                try:
                    start_dt = datetime(year, month_num, day)
                    date_str = start_dt.strftime("%Y-%m-%d")
                    current_prefs.rental_start_date = date_str
                    current_prefs.rental_details.pickup_date = date_str
                    if current_prefs.rental_details.rental_duration_days:
                        end_dt = start_dt + timedelta(days=current_prefs.rental_details.rental_duration_days)
                        end_str = end_dt.strftime("%Y-%m-%d")
                        current_prefs.rental_end_date = end_str
                        current_prefs.rental_details.return_date = end_str
                    extracted_fields.append(f"rental_start_date: {date_str}")
                except ValueError:
                    pass

        # ---------------------------------------------------------
        # 10. Purchase Specific: Condition (used vs new)
        # ---------------------------------------------------------
        is_buy_active = (current_prefs.intent == "BUY" or current_prefs.intent == IntentType.BUY)
        if is_buy_active:
            if not current_prefs.purchase_details:
                current_prefs.purchase_details = PurchaseDetails()
            if any(w in text_lower for w in ["used", "pre-owned", "second hand", "preowned"]):
                current_prefs.purchase_type = "used"
                current_prefs.purchase_details.condition = "used"
                extracted_fields.append("purchase_type: used")
            elif "new" in text_lower:
                current_prefs.purchase_type = "new"
                current_prefs.purchase_details.condition = "new"
                extracted_fields.append("purchase_type: new")

        # ---------------------------------------------------------
        # 11. Sell Specific Entity Extraction
        # ---------------------------------------------------------
        is_sell_active = (current_prefs.intent == "SELL" or current_prefs.intent == IntentType.SELL)
        if is_sell_active:
            if not current_prefs.sell_details:
                current_prefs.sell_details = SellDetails()

            # Registration status in user's name
            if re.search(r'\b(yes|yeah|yep|registered\s+in\s+my\s+name|in\s+my\s+name|on\s+my\s+name|registered\s+to\s+me)\b', text_lower):
                current_prefs.sell_details.is_registered_in_user_name = True
                extracted_fields.append("registered_in_user_name: True")
            elif re.search(r'\b(no|nope|not\s+in\s+my\s+name|not\s+registered\s+in\s+my\s+name|someone\s+else)\b', text_lower):
                current_prefs.sell_details.is_registered_in_user_name = False
                extracted_fields.append("registered_in_user_name: False")

            # Year e.g. 2021, 2019, 2022
            year_match = re.search(r'\b(199\d|20[0-2]\d)\b', text_lower)
            if year_match:
                y_val = int(year_match.group(1))
                current_prefs.sell_details.year = y_val
                extracted_fields.append(f"year: {y_val}")

            # Kms driven e.g. "32,000 km", "35000 kms", "32k km", "40000"
            kms_match = re.search(r'(\d{1,3}(?:,\d{3})+|\d+)\s*(?:kms?|kilometers?|km)\b', text_lower)
            if not kms_match:
                kms_k = re.search(r'(\d+(?:\.\d+)?)\s*k\s*(?:kms?|km)\b', text_lower)
                if kms_k:
                    km_val = int(float(kms_k.group(1)) * 1000)
                    current_prefs.sell_details.kms_driven = km_val
                    extracted_fields.append(f"kms_driven: {km_val:,}")
            else:
                km_val = int(kms_match.group(1).replace(",", ""))
                current_prefs.sell_details.kms_driven = km_val
                extracted_fields.append(f"kms_driven: {km_val:,}")

            # Model recognition
            models_to_check = [
                ("city", "City"), ("creta", "Creta"), ("harrier", "Harrier"), ("fortuner", "Fortuner"),
                ("swift", "Swift"), ("baleno", "Baleno"), ("verna", "Verna"), ("i20", "i20"),
                ("nexon", "Nexon"), ("seltos", "Seltos"), ("innova", "Innova"), ("xuv700", "XUV700"),
                ("thar", "Thar"), ("scorpio", "Scorpio"), ("brezza", "Brezza"), ("tiago", "Tiago"),
                ("altroz", "Altroz"), ("punch", "Punch"), ("slavia", "Slavia"), ("virtus", "Virtus")
            ]
            for m_kw, m_label in models_to_check:
                if re.search(r'\b' + m_kw + r'\b', text_lower):
                    current_prefs.sell_details.model = m_label
                    extracted_fields.append(f"model: {m_label}")
                    break

            # Brand
            if current_prefs.preferred_brands:
                current_prefs.sell_details.brand = current_prefs.preferred_brands[0]
            elif current_prefs.brand_preference:
                current_prefs.sell_details.brand = current_prefs.brand_preference

            # Location
            if current_prefs.location:
                current_prefs.sell_details.location = current_prefs.location

            # Expected Price
            if current_prefs.budget_max and current_prefs.budget_max > 0:
                current_prefs.sell_details.expected_price = current_prefs.budget_max
            elif current_prefs.budget and current_prefs.budget.amount > 0:
                current_prefs.sell_details.expected_price = current_prefs.budget.amount

            # Technical attributes
            if current_prefs.fuel_type:
                current_prefs.sell_details.fuel_type = current_prefs.fuel_type.title()
            if current_prefs.transmission:
                current_prefs.sell_details.transmission = current_prefs.transmission.title()

        # ---------------------------------------------------------
        # 12. Completeness Check
        # ---------------------------------------------------------
        missing = AdaptiveInterviewAgent.check_missing_fields(current_prefs)
        current_prefs.interview_complete = (len(missing) == 0)

        return current_prefs, extracted_fields

    @staticmethod
    def check_missing_fields(prefs: UserPreferences) -> List[str]:
        """
        Identifies which essential requirements are genuinely missing.
        Never demands category if seating capacity is already specified.
        """
        missing = []

        # History and comparison intents require no extra interview fields
        if prefs.intent in [
            IntentType.PURCHASE_HISTORY, IntentType.RENTAL_HISTORY,
            IntentType.SELLING_HISTORY, IntentType.COMPARE,
            "PURCHASE_HISTORY", "RENTAL_HISTORY", "SELLING_HISTORY", "COMPARE"
        ]:
            return []

        # Sell intent requires ownership registration check
        if prefs.intent == IntentType.SELL or prefs.intent == "SELL":
            if not prefs.sell_details or prefs.sell_details.is_registered_in_user_name is None:
                missing.append("is_registered_in_user_name")
            return missing

        is_buy = (prefs.intent == IntentType.BUY or prefs.intent == "BUY")
        has_cat_or_seats = bool(prefs.category or prefs.seating_capacity)
        has_budget = bool(
            (prefs.budget_max and prefs.budget_max > 0) or
            (prefs.budget and prefs.budget.amount > 0)
        )

        if not prefs.location:
            missing.append("location")

        # If user specified seating capacity, category is not strictly required
        if not has_cat_or_seats:
            missing.append("category")

        if not has_budget:
            missing.append("budget")

        is_buy = (prefs.intent == IntentType.BUY or prefs.intent == "BUY")
        if not is_buy:
            has_date = bool(prefs.rental_start_date or (prefs.rental_details and prefs.rental_details.pickup_date))
            if not has_date:
                missing.append("pickup_date")
            has_dur = bool(prefs.rental_details and prefs.rental_details.rental_duration_days)
            if not has_dur:
                missing.append("rental_duration")
        else:
            if not prefs.purchase_details or not prefs.purchase_details.condition:
                # condition is desirable for buy but not strictly blocking if category/seating is given
                pass

        return missing

    @staticmethod
    def generate_followup_question(prefs: UserPreferences) -> str:
        """
        Generates contextual, conversational questions requesting ONLY information that is genuinely missing.
        Prioritizes asking one important question at a time to maintain natural conversational flow.
        """
        missing = AdaptiveInterviewAgent.check_missing_fields(prefs)
        if not missing:
            return "All set! I have gathered your key requirements. Let's find your perfect match."

        if prefs.intent == IntentType.SELL or prefs.intent == "SELL":
            if "is_registered_in_user_name" in missing:
                cat_desc = prefs.category.value.lower() if prefs.category else "car"
                return f"I can certainly help you list your {cat_desc} for sale on Aura Motors.\n\nIs the vehicle currently registered in your name?"
            return "Could you provide details about your car — such as make, model, year, kilometers driven, and expected selling price?"

        is_rent = False

        # Natural conversational acknowledgement
        ack_prefix = ""
        if prefs.seating_capacity and prefs.category:
            words = {2: "two people", 3: "three people", 4: "four people", 5: "five passengers", 7: "seven passengers"}
            cap_desc = words.get(prefs.seating_capacity, f"{prefs.seating_capacity} passengers")
            fuel_desc = f"{prefs.fuel_type.lower()} " if prefs.fuel_type and prefs.fuel_type not in ["any", None] else ""
            article = "an" if fuel_desc.startswith("e") or fuel_desc.startswith("a") else "a"
            ack_prefix = f"Great! Let's find {article} {fuel_desc}{prefs.category.value} for {cap_desc}.\n\n"
        elif prefs.seating_capacity and not prefs.location and not (prefs.budget and prefs.budget.amount > 0):
            words = {2: "two people", 3: "three people", 4: "four people", 5: "five passengers", 7: "seven passengers"}
            cap_desc = words.get(prefs.seating_capacity, f"{prefs.seating_capacity} people")
            # If both city and budget are missing and user specified seating capacity, ask both concisely
            if "location" in missing and "budget" in missing:
                budget_phrase = "what's your approximate purchase budget"
                return f"Got it! Let's find a car for {cap_desc}.\n\nWhich city will you be driving in, and {budget_phrase}?"
            ack_prefix = f"Got it! Let's find a car for {cap_desc}.\n\n"
        elif prefs.category and not prefs.location:
            ack_prefix = f"Great! Let's find a {prefs.category.value.lower()} for your purchase.\n\n"
        elif prefs.location and (prefs.category or prefs.seating_capacity):
            ack_prefix = f"Perfect, {prefs.location}. "

        # Prioritize one question at a time
        if "location" in missing:
            return (ack_prefix + "Which city will you be driving in (e.g., Delhi, Mumbai, Bangalore)?").strip()

        if "budget" in missing:
            return (ack_prefix + "What is your target purchase budget (e.g., ₹15 Lakh)?").strip()

        if "category" in missing and not prefs.seating_capacity:
            return (ack_prefix + "What style of vehicle are you looking for (e.g., SUV, Sedan, EV, Hatchback)?").strip()

        return (ack_prefix + "What other preferences do you have in mind?").strip()
