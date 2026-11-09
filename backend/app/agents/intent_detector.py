"""
Universal Intent Detector & Context Analyzer for Aura AI Consultant.
Extracts structured intents, entity parameters, and contextual workflow transitions.
Handles affirmative answers to pending questions and clean intent switching.
"""

import re
from typing import Dict, Any, Optional, Tuple, List
from pydantic import BaseModel, Field

class DetectedIntent(BaseModel):
    intent: str
    confidence: float = 1.0
    is_affirmative: bool = False
    is_negative: bool = False
    is_intent_switch: bool = False
    entities: Dict[str, Any] = Field(default_factory=dict)
    raw_query: str = ""

class UniversalIntentDetector:
    @staticmethod
    def detect_intent(
        user_text: str,
        active_workflow: Optional[str] = None,
        pending_question: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None
    ) -> DetectedIntent:
        text_lower = user_text.lower().strip()

        # -------------------------------------------------------------
        # 0. Check Intent Switching / Cancellation of Active Workflow
        # e.g. "I don't want to sell it anymore. Show me my purchases"
        # -------------------------------------------------------------
        intent_switch_patterns = [
            r"(?:i\s+don'?t\s+want\s+to\s+(?:sell|buy|rent|continue)|stop\s+(?:selling|buying|renting)|cancel\s+this|never\s*mind|forget\s+it)\b[,\.\s]*(.*)",
            r"(?:instead\s+of\s+(?:that|this)|rather\s+than\s+(?:that|this))\b[,\.\s]*(.*)",
            r"^(?:instead|rather)[,\.\s]+(.*)"
        ]
        remainder_text = text_lower
        is_switching = False
        for pat in intent_switch_patterns:
            m = re.search(pat, text_lower)
            if m:
                is_switching = True
                captured = m.group(1).strip()
                if captured:
                    remainder_text = captured
                break

        # -------------------------------------------------------------
        # 1. Check Contextual Affirmative / Negative Answers
        # If there is a pending question from the active workflow, e.g. IS_REGISTERED_IN_NAME
        # -------------------------------------------------------------
        # 1.4 Dynamic Detail Update Intent ("change name to ...", "change phone to ...", "change payment to ...", etc.)
        # Check this BEFORE answering pending questions so users can update details at any step!
        has_change_trigger = bool(re.search(
            r"\b(?:change|update|edit|set|modify|switch|use|make|replace|put)\b",
            text_lower
        ))
        has_field_indicator = bool(re.search(
            r"\b(?:name|phone|mobile|number|email|city|location|residence|budget|payment(?:\s+method)?|car|vehicle|category|upi(?:\s*id)?)\b",
            text_lower
        )) or bool(re.search(r"\b(?:my\s+name\s+is|my\s+phone\s+is|my\s+email\s+is|my\s+city\s+is|my\s+budget\s+is)\b", text_lower))

        if (has_change_trigger and has_field_indicator) or ("my name is" in text_lower or "my phone is" in text_lower or "my email is" in text_lower or "use card" in text_lower or "use upi" in text_lower or "switch to" in text_lower):
            update_entities = {}

            # Name
            name_m = re.search(r"\b(?:change|update|set|make)\s+(?:my\s+)?name\s+(?:to\s+|as\s+|:\s*)([A-Za-z\s]{2,30})\b", text_lower)
            if not name_m:
                name_m = re.search(r"\bmy\s+name\s+is\s+([A-Za-z\s]{2,30})\b", text_lower)
            if name_m:
                val = name_m.group(1).strip()
                val = re.split(r"\b(?:and|with|phone|email|city|budget|car)\b", val)[0].strip()
                if val:
                    update_entities["name"] = val.title()

            # Phone
            phone_m = re.search(r"\b(?:change|update|set|make)\s+(?:my\s+)?(?:phone|mobile|contact)(?:\s+number)?\s+(?:to\s+|as\s+|:\s*)([+\d\s-]{10,16})", text_lower)
            if not phone_m:
                phone_m = re.search(r"\b(?:my\s+)?(?:phone|mobile)(?:\s+number)?\s+(?:is|:)\s*([+\d\s-]{10,16})", text_lower)
            if not phone_m and ("phone" in text_lower or "mobile" in text_lower):
                phone_m = re.search(r"(?:\+?91[\s-]?)?[6-9]\d{9}", text_lower)
            if phone_m:
                update_entities["phone"] = phone_m.group(0).strip()

            # Email
            email_m = re.search(r"\b(?:change|update|set|make)\s+(?:my\s+)?email\s+(?:to\s+|as\s+|:\s*)([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", text_lower)
            if not email_m:
                email_m = re.search(r"\b(?:my\s+)?email\s+(?:is|:)\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", text_lower)
            if not email_m:
                email_m = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text_lower)
            if email_m:
                update_entities["email"] = email_m.group(0).strip()

            # City / Location
            city_m = re.search(r"\b(?:change|update|set|make)\s+(?:my\s+)?(?:city|location|delivery\s+city|address)\s+(?:to\s+|as\s+|:\s*)([A-Za-z\s]{2,20})\b", text_lower)
            if city_m:
                c_val = city_m.group(1).strip()
                c_val = re.split(r"\b(?:and|with|phone|email|budget)\b", c_val)[0].strip()
                if c_val:
                    update_entities["city"] = c_val.title()
            else:
                for c in ["delhi", "mumbai", "bangalore", "hyderabad", "pune", "chennai", "kolkata", "ahmedabad", "jaipur", "goa", "noida", "gurgaon"]:
                    if f"to {c}" in text_lower or f"in {c}" in text_lower or (f"change city" in text_lower and c in text_lower):
                        update_entities["city"] = c.title()
                        break

            # Payment Method
            pay_m = re.search(r"\b(?:change|update|set|switch)\s+(?:the\s+)?payment(?:\s+method)?\s+(?:to\s+|as\s+|:\s*)(card|credit\s*card|debit\s*card|upi|net\s*banking|netbanking)\b", text_lower)
            if not pay_m:
                pay_m = re.search(r"\buse\s+(card|credit\s*card|debit\s*card|upi|net\s*banking|netbanking)(?:\s+instead|\s+for\s+payment)?\b", text_lower)
            if not pay_m:
                pay_m = re.search(r"\bpay\s+(?:with|via|using)\s+(card|credit\s*card|debit\s*card|upi|net\s*banking|netbanking)\b", text_lower)
            if pay_m:
                pm_val = pay_m.group(1).strip().lower()
                if "card" in pm_val:
                    update_entities["payment_method"] = "card"
                elif "net" in pm_val:
                    update_entities["payment_method"] = "netbanking"
                else:
                    update_entities["payment_method"] = "upi"

            # UPI ID
            upi_m = re.search(r"\b(?:change|update|set|make)\s+(?:my\s+)?upi(?:\s*id)?\s+(?:to\s+|as\s+|:\s*)([a-zA-Z0-9.\-_]+@[a-zA-Z0-9]+)\b", text_lower)
            if upi_m:
                update_entities["upi_id"] = upi_m.group(1).strip()

            # Budget
            budget_m = re.search(r"\b(?:change|update|set|increase|decrease|make)\s+(?:my\s+)?budget\s+(?:to\s+|as\s+|:\s*)(\d+(?:\.\d+)?)\s*(?:lakh|lacs?|l\b|crore|cr\b|k\b)?", text_lower)
            if not budget_m:
                budget_m = re.search(r"\bbudget\s*(?:is|to|:)\s*(\d+(?:\.\d+)?)\s*(?:lakh|lacs?|l\b|crore|cr\b|k\b)?", text_lower)
            if budget_m:
                val = float(budget_m.group(1))
                if "crore" in text_lower or "cr" in text_lower:
                    val *= 10000000.0
                elif val < 500:
                    val *= 100000.0
                update_entities["budget_max"] = val

            # Car / Vehicle
            car_m = re.search(r"\b(?:change|update|switch|swap)\s+(?:the\s+)?(?:car|vehicle)\s+to\s+([A-Za-z0-9\s]+)\b", text_lower)
            if not car_m:
                car_m = re.search(r"\bswitch\s+to\s+([A-Za-z0-9\s]+)\b", text_lower)
            if not car_m:
                car_m = re.search(r"\bchoose\s+(?:the\s+)?([A-Za-z0-9\s]+)\s+instead\b", text_lower)
            
            matched_car = None
            if car_m:
                c_cand = car_m.group(1).strip()
                c_cand = re.split(r"\b(?:and|with|payment|budget)\b", c_cand)[0].strip()
                matched_car = c_cand

            for sm in [
                "harrier", "fortuner", "creta", "thar", "scorpio", "nexon", "seltos",
                "innova", "xuv700", "slavia", "virtus", "safari", "z4", "ioniq",
                "swift", "baleno", "verna", "amaze", "punch", "brezza"
            ]:
                if f"switch to {sm}" in text_lower or f"change car to {sm}" in text_lower or f"change to {sm}" in text_lower or f"change vehicle to {sm}" in text_lower or f"choose {sm}" in text_lower:
                    matched_car = sm
                    break

            if "honda city" in text_lower or "car to city" in text_lower:
                matched_car = "city"

            if matched_car:
                update_entities["vehicle_name"] = matched_car

            # Category
            cat_m = re.search(r"\b(?:change|update|switch)\s+(?:the\s+)?category\s+to\s+(suv|sedan|hatchback|convertible|electric|ev)\b", text_lower)
            if not cat_m:
                cat_m = re.search(r"\bswitch\s+to\s+(suv|sedan|hatchback|convertible|electric|ev)\b", text_lower)
            if cat_m:
                c_cat = cat_m.group(1).strip().lower()
                if "suv" in c_cat: update_entities["category"] = "SUV"
                elif "sedan" in c_cat: update_entities["category"] = "Sedan"
                elif "hatchback" in c_cat: update_entities["category"] = "Hatchback"
                elif "convertible" in c_cat: update_entities["category"] = "Convertible"
                elif "electric" in c_cat or "ev" in c_cat: update_entities["category"] = "Electric Vehicle"

            if update_entities:
                return DetectedIntent(
                    intent="UPDATE_DETAILS",
                    entities=update_entities,
                    raw_query=user_text
                )

        affirmative_patterns = [
            r"^(?:yes|yeah|yup|yep|sure|ok|okay|continue|okay\s*,\s*continue|go\s+ahead|proceed|confirm|confirm\s+transaction|do\s+it|complete|pay|pay\s+it|pay\s+now|pay\s+this|affirmative|correct|done|yes\s+please|it\s+is|it's\s+in\s+my\s+name|in\s+my\s+name|registered\s+to\s+me)\b",
            r"\b(okay\s+continue|yes\s+it\s+is|it\s+is\s+registered\s+in\s+my\s+name|confirm\s+and\s+pay|proceed\s+with\s+booking|proceed\s+to\s+payment|proceed\s+with\s+payment|pay\s+it|pay\s+now|pay\s+the\s+amount)\b"
        ]
        negative_patterns = [
            r"^(?:no|nope|nah|not\s+really|negative|not\s+in\s+my\s+name|someone\s+else|different\s+person)\b"
        ]

        is_affirmative = any(re.search(pat, text_lower) for pat in affirmative_patterns)
        is_negative = any(re.search(pat, text_lower) for pat in negative_patterns)

        # If user is answering a pending question without specifying a new independent command:
        if pending_question and not is_switching:
            if is_affirmative:
                return DetectedIntent(
                    intent="ANSWER_PENDING_QUESTION",
                    is_affirmative=True,
                    is_negative=False,
                    entities={"answer": True, "field": pending_question},
                    raw_query=user_text
                )
            elif is_negative:
                return DetectedIntent(
                    intent="ANSWER_PENDING_QUESTION",
                    is_affirmative=False,
                    is_negative=True,
                    entities={"answer": False, "field": pending_question},
                    raw_query=user_text
                )

        target_text = remainder_text if is_switching else text_lower

        # -------------------------------------------------------------
        # 2. Account & Digital Garage Intents
        # -------------------------------------------------------------
        # VIEW_MY_VEHICLES
        my_vehicles_patterns = [
            r"\b(?:show|list|view|display|open|see)\s+(?:me\s+)?(?:the\s+)?(?:list\s+of\s+)?my\s+(?:cars|vehicles|garage|automobiles)\b",
            r"\b(?:where\s+are\s+my\s+(?:cars|vehicles)|cars\s+i\s+own|vehicles\s+i\s+own|my\s+garage)\b",
            r"\b(?:show\s+my\s+cars|show\s+my\s+vehicles|my\s+cars|my\s+vehicles)\b"
        ]
        if any(re.search(p, target_text) for p in my_vehicles_patterns):
            return DetectedIntent(intent="VIEW_MY_VEHICLES", is_intent_switch=is_switching, raw_query=user_text)

        # VIEW_PURCHASES
        purchases_patterns = [
            r"\b(?:show|list|view|display|open|see)\s+(?:me\s+)?(?:all\s+the\s+)?(?:my\s+)?(?:purchased?\s+(?:cars|vehicles)|purchases|orders?|purchase\s+history|bought\s+cars)\b",
            r"\b(?:show|list|view|display|open|see)\s+(?:me\s+)?(?:all\s+the\s+)?(?:cars|vehicles)\s+(?:that\s+)?i(?:\x27ve|\s+have)?\s+(?:purchased|bought)\b",
            r"\b(?:cars|vehicles)\s+(?:that\s+)?i(?:\x27ve|\s+have)?\s+(?:purchased|bought)\b",
            r"\b(?:what\s+cars\s+did\s+i\s+buy|cars\s+i\s+have\s+bought|order\s+history)\b"
        ]
        if any(re.search(p, target_text) for p in purchases_patterns):
            return DetectedIntent(intent="VIEW_PURCHASES", is_intent_switch=is_switching, raw_query=user_text)

        # VIEW_RENTALS (Forwarded to VIEW_PURCHASES)
        rentals_patterns = [
            r"\b(?:show|list|view|display|open|see)\s+(?:me\s+)?(?:my\s+)?(?:rental\s+(?:history|bookings?)|rentals?|previous\s+rentals?|past\s+rentals?)\b",
            r"\b(?:show|list|view|display|open|see)\s+(?:me\s+)?(?:all\s+the\s+)?(?:cars|vehicles)\s+(?:that\s+)?i(?:\x27ve|\s+have)?\s+(?:rented|booked)\b",
            r"\b(?:cars|vehicles)\s+(?:that\s+)?i(?:\x27ve|\s+have)?\s+(?:rented|booked)\b",
            r"\b(?:my\s+rental\s+bookings|cars\s+i(?:\x27m|\s+am)?\s+renting)\b"
        ]
        if any(re.search(p, target_text) for p in rentals_patterns):
            return DetectedIntent(intent="VIEW_PURCHASES", is_intent_switch=is_switching, raw_query=user_text)

        # VIEW_SELLING_LISTINGS
        listings_patterns = [
            r"\b(?:show|list|view|display|open|see)\s+(?:me\s+)?(?:my\s+)?(?:listings?|selling\s+listings?|active\s+listings?|cars\s+(?:i(?:\x27m|\s+am)?\s+selling|for\s+sale))\b"
        ]
        if any(re.search(p, target_text) for p in listings_patterns):
            return DetectedIntent(intent="VIEW_SELLING_LISTINGS", is_intent_switch=is_switching, raw_query=user_text)

        # VIEW_PAYMENT_HISTORY
        payment_patterns = [
            r"\b(?:show|list|view|display|open|see)\s+(?:me\s+)?(?:my\s+)?(?:previous\s+payments?|payment\s+history|transactions?|receipts?|billing(?:\s+history)?)\b",
            r"\b(?:payment\s+records?|my\s+payments?)\b"
        ]
        if any(re.search(p, target_text) for p in payment_patterns):
            return DetectedIntent(intent="VIEW_PAYMENT_HISTORY", is_intent_switch=is_switching, raw_query=user_text)

        # VIEW_SAVED_VEHICLES
        saved_patterns = [
            r"\b(?:show|list|view|display|open|see)\s+(?:me\s+)?(?:my\s+)?(?:saved\s+(?:cars|vehicles)|bookmarked|wishlist|favorites)\b"
        ]
        if any(re.search(p, target_text) for p in saved_patterns):
            return DetectedIntent(intent="VIEW_SAVED_VEHICLES", is_intent_switch=is_switching, raw_query=user_text)

        # VIEW_PROFILE / UPDATE_PROFILE
        profile_patterns = [
            r"\b(?:update|edit|change)\s+(?:my\s+)?(?:phone|mobile|number|profile|residence|email|address|city)\b",
            r"\b(?:show|open|view|see)\s+(?:my\s+)?(?:profile|account\s+settings?|member\s+profile|account)\b"
        ]
        if any(re.search(p, target_text) for p in profile_patterns):
            entities = {}
            phone_m = re.search(r'(?:\+?91[\s-]?)?[6-9]\d{9}', target_text)
            if phone_m:
                entities["phone"] = phone_m.group(0)
            return DetectedIntent(intent="UPDATE_PROFILE", entities=entities, is_intent_switch=is_switching, raw_query=user_text)

        # VIEW_DASHBOARD
        dashboard_patterns = [
            r"\b(?:take\s+me\s+to|open|view|show|go\s+to)\s+(?:my\s+)?dashboard\b"
        ]
        if any(re.search(p, target_text) for p in dashboard_patterns):
            return DetectedIntent(intent="VIEW_DASHBOARD", is_intent_switch=is_switching, raw_query=user_text)

        # -------------------------------------------------------------
        # 3. Sell Workflow Intents
        # -------------------------------------------------------------
        sell_patterns = [
            r"\b(?:want\s+to\s+sell|help\s+(?:me\s+)?sell|sell\s+(?:my|a)\s+(?:car|sedan|suv|vehicle|hatchback)|list\s+(?:my\s+)?car\s+for\s+sale|put\s+up\s+for\s+sale|trade\s*in)\b",
            r"\bi\s+want\s+to\s+sell\b"
        ]
        if any(re.search(p, target_text) for p in sell_patterns):
            entities = {}
            if "sedan" in target_text:
                entities["category"] = "Sedan"
            elif "suv" in target_text:
                entities["category"] = "SUV"
            elif "hatchback" in target_text:
                entities["category"] = "Hatchback"
            return DetectedIntent(intent="SELL_VEHICLE", entities=entities, is_intent_switch=is_switching, raw_query=user_text)

        # -------------------------------------------------------------
        # 4. Compare Vehicles Intents
        # -------------------------------------------------------------
        compare_patterns = [
            r"\b(?:compare|comparison|versus|\bvs\b|difference\s+between)\b"
        ]
        if any(re.search(p, target_text) for p in compare_patterns):
            return DetectedIntent(intent="COMPARE_VEHICLES", is_intent_switch=is_switching, raw_query=user_text)

        # -------------------------------------------------------------
        # 5. Cancel Booking Intent
        # -------------------------------------------------------------
        cancel_patterns = [
            r"\bcancel\s+(?:my\s+)?(?:booking|reservation|order)\b"
        ]
        if any(re.search(p, target_text) for p in cancel_patterns):
            order_m = re.search(r'\b(bk-[a-z0-9\-]+|ord-[a-z0-9\-]+)\b', target_text)
            entities = {"order_id": order_m.group(1).upper()} if order_m else {}
            return DetectedIntent(intent="CANCEL_BOOKING", entities=entities, is_intent_switch=is_switching, raw_query=user_text)

        # -------------------------------------------------------------
        # 5.5 Auto-Click Book / Specific Vehicle Booking Intent
        # "book this car", "buy this car", "book tata harrier", "book fortuner"
        # -------------------------------------------------------------
        book_patterns = [
            r"^(?:please\s+)?(?:book|reserve)\s+(?:this\s+car|the\s+car|this\s+vehicle|this|now)\b",
            r"^(?:please\s+)?(?:buy|purchase)\s+(?:this\s+car|this\s+vehicle|this\s+one|this)\b",
            r"\b(?:book|reserve|buy|purchase)\s+(?:the\s+)?(?:tata\s+|hyundai\s+|toyota\s+|mahindra\s+|honda\s+|bmw\s+|audi\s+|mercedes\s+)?(harrier|fortuner|creta|city|thar|scorpio|nexon|seltos|innova|xuv700|slavia|virtus|safari|z4|ioniq\s*5|nexon\s*ev)\b",
            r"^(?:i\s+want\s+to\s+|ready\s+to\s+)?book\s+(?:this|now)\b",
            r"^(?:i\s+want\s+to\s+)?buy\s+this\s+car\b"
        ]
        for bp in book_patterns:
            bm = re.search(bp, target_text)
            if bm:
                entities = {}
                if bm.groups() and bm.group(1):
                    entities["vehicle_name"] = bm.group(1).strip()
                entities["intent"] = "buy"
                return DetectedIntent(intent="BOOK_VEHICLE", entities=entities, is_intent_switch=is_switching, raw_query=user_text)

        # -------------------------------------------------------------
        # 5.8 Specific Vehicle Inquiry Intent (e.g. "Tell me about Tata Harrier", "Show me Fortuner")
        # -------------------------------------------------------------
        specific_models = [
            "harrier", "fortuner", "creta", "thar", "scorpio", "nexon", "seltos",
            "innova", "xuv700", "slavia", "virtus", "safari", "z4", "ioniq",
            "swift", "city", "baleno", "verna", "amaze", "punch", "brezza",
            "hyryder", "fronx", "taigun", "kushaq", "elevate", "miata", "compass",
            "wrangler", "carnival", "carens", "glanza", "jimny", "tiago", "altroz"
        ]
        inquiry_triggers = [
            r"\b(?:tell\s+me\s+about|what\s+about|how\s+is\s+the|details\s+of|specs\s+of|info\s+on|strengths\s+and|good\s+for\s+daily\s+driving|show\s+me\s+(?:the\s+)?)\b",
            r"\b(?:about\s+the|about\s+this\s+car|about\s+this\s+vehicle)\b"
        ]
        matched_model = None
        for sm in specific_models:
            if re.search(r'\b' + sm + r'\b', target_text):
                matched_model = sm
                break

        if matched_model and (any(re.search(t, target_text) for t in inquiry_triggers) or "tell me" in target_text or "what about" in target_text or "show me" in target_text):
            entities = {"vehicle_name": matched_model, "intent": "buy"}
            return DetectedIntent(intent="VEHICLE_INQUIRY", entities=entities, is_intent_switch=is_switching, raw_query=user_text)

        # Helper for negated categories e.g. "sedan instead of suv", "not an suv"
        negated_cats = set()
        for neg_m in re.finditer(r'(?:instead\s+of|rather\s+than|not\s+an?)\s+([a-z\s]+)', target_text):
            n_phrase = neg_m.group(1)
            for c in ["sedan", "suv", "hatchback", "convertible", "electric", "ev"]:
                if c in n_phrase:
                    negated_cats.add(c)

        # -------------------------------------------------------------
        # 6. Rent Vehicle Intent
        # -------------------------------------------------------------
        rent_patterns = [
            r"\b(?:rent|rental|renting|hire|hiring|lease|leasing)\b",
            r"\b(?:per\s*day|/day|daily)\b"
        ]
        if any(re.search(p, target_text) for p in rent_patterns):
            entities = {}
            if "sedan" in target_text and "sedan" not in negated_cats: entities["category"] = "Sedan"
            elif "suv" in target_text and "suv" not in negated_cats: entities["category"] = "SUV"
            elif "hatchback" in target_text and "hatchback" not in negated_cats: entities["category"] = "Hatchback"
            elif ("electric" in target_text or "ev" in target_text) and not ("electric" in negated_cats or "ev" in negated_cats):
                entities["category"] = "Electric Vehicle"
            for loc in ["Delhi", "Mumbai", "Bangalore", "Hyderabad", "Pune", "Goa"]:
                if loc.lower() in target_text:
                    entities["location"] = loc
                    break
            return DetectedIntent(intent="RENT_VEHICLE", entities=entities, is_intent_switch=is_switching, raw_query=user_text)

        # -------------------------------------------------------------
        # 7. Search & Buy Vehicles Intent
        # -------------------------------------------------------------
        buy_patterns = [
            r"\b(?:buy|buying|purchase|purchasing|acquire|ordering|find|search|show\s+me)\b",
            r"\b(?:sedan|suv|hatchback|convertible|ev|electric)\b",
            r"\b(?:under|below|max|budget|increase\s+my\s+budget)\s+(?:to\s+)?\d+\s*(?:lakh|l)\b",
            r"\b(?:want\s+to\s+but|looking\s+to\s+but|but\s+an?\s+(?:sedan|suv|car|vehicle))\b",
            r"\b(?:seats?|seater)\b"
        ]
        if any(re.search(p, target_text) for p in buy_patterns):
            entities = {}
            if "sedan" in target_text and "sedan" not in negated_cats: entities["category"] = "Sedan"
            elif "suv" in target_text and "suv" not in negated_cats: entities["category"] = "SUV"
            elif "hatchback" in target_text and "hatchback" not in negated_cats: entities["category"] = "Hatchback"
            elif "convertible" in target_text and "convertible" not in negated_cats: entities["category"] = "Convertible"
            elif ("electric" in target_text or "ev" in target_text) and not ("electric" in negated_cats or "ev" in negated_cats):
                entities["category"] = "Electric Vehicle"

            lakh_m = re.search(r'(?:under|below|max(?:imum)?|budget\s*(?:is|of|:)?\s*)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lacs?|l\b)', target_text)
            if lakh_m:
                entities["budget_max"] = float(lakh_m.group(1)) * 100000.0

            for loc in ["Delhi", "Mumbai", "Bangalore", "Hyderabad", "Pune"]:
                if loc.lower() in target_text:
                    entities["location"] = loc
                    break

            return DetectedIntent(intent="SEARCH_VEHICLES", entities=entities, is_intent_switch=is_switching, raw_query=user_text)

        # -------------------------------------------------------------
        # 8. Navigation Fallback
        # -------------------------------------------------------------
        if "home" in target_text:
            return DetectedIntent(intent="NAVIGATE", entities={"path": "/"}, raw_query=user_text)
        elif "about" in target_text:
            return DetectedIntent(intent="NAVIGATE", entities={"path": "/about"}, raw_query=user_text)
        elif "contact" in target_text:
            return DetectedIntent(intent="NAVIGATE", entities={"path": "/contact"}, raw_query=user_text)
        elif "checkout" in target_text:
            return DetectedIntent(intent="NAVIGATE", entities={"path": "/checkout"}, raw_query=user_text)

        return DetectedIntent(intent="GENERAL_QUESTION", raw_query=user_text)

intent_detector = UniversalIntentDetector()
