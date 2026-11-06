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
        affirmative_patterns = [
            r"^(?:yes|yeah|yup|yep|sure|ok|okay|continue|okay\s*,\s*continue|go\s+ahead|proceed|affirmative|correct|done|yes\s+please|it\s+is|it's\s+in\s+my\s+name|in\s+my\s+name|registered\s+to\s+me)\b",
            r"\b(okay\s+continue|yes\s+it\s+is|it\s+is\s+registered\s+in\s+my\s+name)\b"
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

        # VIEW_RENTALS
        rentals_patterns = [
            r"\b(?:show|list|view|display|open|see)\s+(?:me\s+)?(?:my\s+)?(?:rental\s+(?:history|bookings?)|rentals?|previous\s+rentals?|past\s+rentals?)\b",
            r"\b(?:show|list|view|display|open|see)\s+(?:me\s+)?(?:all\s+the\s+)?(?:cars|vehicles)\s+(?:that\s+)?i(?:\x27ve|\s+have)?\s+(?:rented|booked)\b",
            r"\b(?:cars|vehicles)\s+(?:that\s+)?i(?:\x27ve|\s+have)?\s+(?:rented|booked)\b",
            r"\b(?:my\s+rental\s+bookings|cars\s+i(?:\x27m|\s+am)?\s+renting)\b"
        ]
        if any(re.search(p, target_text) for p in rentals_patterns):
            return DetectedIntent(intent="VIEW_RENTALS", is_intent_switch=is_switching, raw_query=user_text)

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
