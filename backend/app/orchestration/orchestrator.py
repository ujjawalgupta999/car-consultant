import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
from ..models.session import Session, WorkflowState, ChatMessage, ChatRole
from ..models.preferences import UserPreferences, IntentType
from ..models.a2ui import CreateSurfaceMessage, UpdateComponentsMessage, A2UIComponent
from ..orchestration.state_machine import StateMachine
from ..agents.interview import AdaptiveInterviewAgent
from ..agents.intent_detector import intent_detector, DetectedIntent
from ..actions.registry import action_registry
from ..repositories.marketplace import marketplace_repo
from ..repositories.session import session_repo
from ..repositories.user_data_repo import user_data_repo
from ..ranking.engine import RankingEngine
from ..config import settings

class OrchestrationEngine:
    def __init__(self):
        # Event queues for active SSE streams: session_id -> List of asyncio.Queue
        self._event_subscribers: Dict[str, List[asyncio.Queue]] = {}

    def subscribe_events(self, session_id: str) -> asyncio.Queue:
        q = asyncio.Queue()
        if session_id not in self._event_subscribers:
            self._event_subscribers[session_id] = []
        self._event_subscribers[session_id].append(q)
        return q

    def unsubscribe_events(self, session_id: str, q: asyncio.Queue):
        if session_id in self._event_subscribers:
            if q in self._event_subscribers[session_id]:
                self._event_subscribers[session_id].remove(q)

    async def emit_event(self, session_id: str, event_type: str, data: Dict[str, Any]):
        if session_id in self._event_subscribers:
            payload = {
                "event": event_type,
                "data": json.dumps(data)
            }
            for q in self._event_subscribers[session_id]:
                await q.put(payload)

    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        payload = {
            "event": event_type,
            "data": json.dumps(data)
        }
        for session_id, queues in list(self._event_subscribers.items()):
            for q in queues:
                try:
                    await q.put(payload)
                except Exception:
                    pass

    async def process_user_turn(self, session_id: str, user_content: str) -> Dict[str, Any]:
        session = session_repo.get_or_create_session(session_id)

        # 1. Store user message
        user_msg = ChatMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            role=ChatRole.USER,
            content=user_content
        )
        session_repo.add_message(session_id, user_msg)

        # 2. Emit Progress: Understanding preferences
        await self.emit_event(session_id, "progress", {
            "stage": "INTERVIEW",
            "step": 1,
            "total_steps": 6,
            "message": "Analyzing natural language automotive preferences..."
        })

        # Context Isolation: If previous session had reached CONFIRMED or PAYMENT_FAILED,
        # isolate context so that the bot does not repeat previous purchase/booking confirmation!
        if session.workflow_state in [WorkflowState.CONFIRMED, WorkflowState.PAYMENT_FAILED]:
            session.workflow_state = WorkflowState.INTERVIEWING
            session.selected_vehicle_id = None
            session.search_results = []
            session.active_order_id = None
            session.active_booking_id = None
            session.active_workflow = None
            session.pending_question = None
            session.workflow_data = {}
            session.preferences = UserPreferences(session_id=session_id)

        # 3. Universal Intent Detection & Context Analysis
        user_id = session.user_id or "usr_demo_01"
        detected = intent_detector.detect_intent(
            user_content,
            active_workflow=session.active_workflow,
            pending_question=session.pending_question,
            session_data=session.workflow_data
        )

        # Handle Intent Switching: e.g. "I don't want to sell it anymore. Show me my purchases"
        if detected.is_intent_switch:
            session.active_workflow = None
            session.pending_question = None
            session.workflow_data = {}

        # -----------------------------------------------------------------
        # SCENARIO: Answering Pending Workflow Question (e.g. Sell Registration)
        # -----------------------------------------------------------------
        if detected.intent == "ANSWER_PENDING_QUESTION":
            if session.pending_question == "IS_REGISTERED_IN_NAME":
                if not session.preferences.sell_details:
                    from ..models.preferences import SellDetails
                    session.preferences.sell_details = SellDetails()

                if detected.is_affirmative:
                    session.preferences.sell_details.is_registered_in_user_name = True
                    session.pending_question = None
                    session.active_workflow = "SELL_WORKFLOW"

                    # Check if user has an owned car matching or in garage
                    owned_vehicles = user_data_repo.get_user_owned_vehicles(user_id)
                    match_id = session.workflow_data.get("matching_owned_vehicle_id")
                    target_owned = None
                    if match_id:
                        target_owned = next((v for v in owned_vehicles if v.id == match_id), None)
                    if not target_owned:
                        content_lower = user_content.lower()
                        # Match by brand or model word in user response
                        for v in owned_vehicles:
                            if v.brand.lower() in content_lower or v.model.lower().split()[0] in content_lower:
                                target_owned = v
                                break
                    if not target_owned:
                        # Find sedan (e.g. Honda City) or first owned car in garage
                        target_owned = next(
                            (v for v in owned_vehicles if any(k in (v.model.lower() + " " + v.brand.lower()) for k in ["sedan", "city", "verna", "slavia", "virtus", "ciaz"])),
                            owned_vehicles[0] if owned_vehicles else None
                        )

                    if target_owned:
                        model_name = target_owned.model.split()[0] if " " in target_owned.model else target_owned.model
                        sell_payload = {
                            "brand": target_owned.brand,
                            "model": model_name,
                            "variant": target_owned.variant or "1.5 i-VTEC",
                            "year": target_owned.year,
                            "fuel_type": "Petrol",
                            "transmission": "Automatic",
                            "kms_driven": 32000,
                            "expected_price": target_owned.currentEstimatedValue or 1180000.0,
                            "location": "Delhi NCR",
                            "is_registered_in_user_name": True,
                            "owned_vehicle_id": target_owned.id
                        }
                        title_desc = f"{sell_payload['year']} {sell_payload['brand']} {sell_payload['model']}"
                        bot_text = (
                            f"Awesome! I see you have a **{title_desc}** in your digital garage.\n\n"
                            f"I've pre-filled your listing form with your car's verified details "
                            f"({sell_payload['variant']}, 32,000 km, asking ₹{sell_payload['expected_price']/100000:.1f} Lakh) "
                            f"and navigated you directly to our **Sell a Car** portal. Please review the details before confirming your listing."
                        )
                        actions = [
                            {"type": "PREFILL_SELL_FORM", "payload": sell_payload},
                            {"type": "UPDATE_FORM", "payload": sell_payload},
                            {"type": "NAVIGATE_TO_PAGE", "payload": {"path": "/sell-car"}},
                            {"type": "NAVIGATE", "payload": {"path": "/sell-car"}}
                        ]
                    else:
                        bot_text = "Great! Please share your vehicle brand, model, year, kilometers driven, and expected selling price to prefill your listing."
                        actions = [
                            {"type": "NAVIGATE_TO_PAGE", "payload": {"path": "/sell-car"}},
                            {"type": "NAVIGATE", "payload": {"path": "/sell-car"}}
                        ]
                else:
                    session.preferences.sell_details.is_registered_in_user_name = False
                    session.pending_question = None
                    bot_text = (
                        "Understood. Aura Motors requires power of attorney or owner authorization for vehicles not registered in the seller's legal name.\n\n"
                        "I've navigated you to our **Sell a Car** portal where you can upload the required authorization or complete your draft listing."
                    )
                    actions = [
                        {"type": "NAVIGATE_TO_PAGE", "payload": {"path": "/sell-car"}},
                        {"type": "NAVIGATE", "payload": {"path": "/sell-car"}}
                    ]

                bot_msg = ChatMessage(id=f"msg_{uuid.uuid4().hex[:8]}", role=ChatRole.ASSISTANT, content=bot_text)
                session_repo.add_message(session_id, bot_msg)
                session_repo.save_session(session)
                for act in actions:
                    await self.emit_event(session_id, "website_action", act)
                return {
                    "message": bot_msg.model_dump(),
                    "workflow_state": session.workflow_state.value,
                    "preferences": session.preferences.model_dump(),
                    "a2ui_surfaces": [],
                    "recommendations": [],
                    "website_actions": actions,
                    "actions": actions
                }

            elif session.pending_question == "PROCEED_TO_PAYMENT":
                pending_checkout = session.workflow_data.get("pending_checkout", {})
                order_id = pending_checkout.get("order_id") or session.active_order_id or f"ORD-2026-{uuid.uuid4().hex[:6].upper()}"
                vehicle_id = pending_checkout.get("vehicle_id") or session.selected_vehicle_id or "CAR-001"
                amount = pending_checkout.get("amount", 25000.0)
                is_rent = pending_checkout.get("is_rent", False)
                target_vehicle = marketplace_repo.get_vehicle_by_id(vehicle_id) or marketplace_repo.get_all_vehicles()[0]
                payment_method = pending_checkout.get("payment_method", "UPI")
                car_title = f"{target_vehicle.brand} {target_vehicle.model}"

                is_direct_pay = any(w in user_content.lower() for w in ["pay it", "pay now", "confirm and pay"])
                if detected.is_affirmative or "proceed" in user_content.lower() or is_direct_pay:
                    if is_direct_pay:
                        from ..services.transaction_service import transaction_service
                        session.pending_question = None
                        session.workflow_state = WorkflowState.CONFIRMED
                        ok, payment, linked_entity, _, _, _ = transaction_service.process_payment_records(
                            order_or_booking_id=order_id,
                            amount=amount,
                            payment_method=payment_method,
                            user_id=user_id,
                            idempotency_key=f"idemp_pay_{order_id}",
                            simulated_scenario="SUCCESS"
                        )
                        txn_id = payment.transactionId if payment else f"TXN-MOCK-{order_id[-6:]}"
                        showcase_card = {
                            "cardType": "PURCHASED_SHOWCASE",
                            "id": f"showcase_{order_id}",
                            "orderId": order_id,
                            "transactionId": txn_id,
                            "vehicleId": target_vehicle.id,
                            "brand": target_vehicle.brand,
                            "model": target_vehicle.model,
                            "year": target_vehicle.year,
                            "variant": getattr(target_vehicle, "variant", None) or "Luxury Edition",
                            "image": target_vehicle.image_url,
                            "amount": amount,
                            "paymentMethod": payment_method.upper(),
                            "status": "OWNED" if not is_rent else "RENTAL CONFIRMED",
                            "actions": [
                                {"label": "View in My Garage", "path": "/dashboard/vehicles"},
                                {"label": "View Payments", "path": "/dashboard/payments"}
                            ]
                        }
                        bot_text = (
                            f"🎉 **Payment Successful & Transaction Confirmed!**\n\n"
                            f"I have successfully submitted your payment and settled the mock transaction for the **{car_title}**.\n\n"
                            f"- **Order Reference:** `{order_id}`\n"
                            f"- **Transaction ID:** `{txn_id}`\n"
                            f"- **Amount Settled:** ₹{amount:,.0f} via {payment_method.upper()}\n"
                            f"- **Status:** Verified & Saved to your digital garage.\n\n"
                            f"I've updated the website in the background to display your official transaction receipt."
                        )
                        actions = [
                            {"type": "EXECUTE_CHECKOUT_SUBMIT", "payload": {"orderId": order_id, "status": "SUCCESS"}},
                            {"type": "REFRESH_DATA", "payload": {"resource": "all"}},
                            {"type": "NAVIGATE_TO_PAGE", "payload": {"path": f"/payment/result/{order_id}"}},
                            {"type": "NAVIGATE", "payload": {"path": f"/payment/result/{order_id}"}}
                        ]
                        cards = [showcase_card]
                    else:
                        session.pending_question = "CONFIRM_TRANSACTION"
                        checkout_path = f"/checkout/{order_id}"
                        bot_text = (
                            f"I've moved you to the checkout and payment portal in the background with your payment details ready:\n\n"
                            f"- **Vehicle:** {car_title}\n"
                            f"- **Payable Amount:** ₹{amount:,.0f}\n"
                            f"- **Payment Method:** UPI ({pending_checkout.get('upi_id', 'alex@okaxis')})\n"
                            f"- **Order Reference:** `{order_id}`\n\n"
                            f"Would you like me to pay and confirm this transaction now? Just say **'pay it'** or **'confirm'**."
                        )
                        actions = [
                            {"type": "NAVIGATE_TO_PAGE", "payload": {"path": checkout_path}},
                            {"type": "NAVIGATE", "payload": {"path": checkout_path}},
                            {"type": "PREFILL_CHECKOUT_FORM", "payload": {
                                "orderId": order_id,
                                "vehicleId": target_vehicle.id,
                                "amount": amount,
                                "paymentMethod": "upi",
                                "upiId": "alex@okaxis"
                            }}
                        ]
                        cards = []
                else:
                    session.pending_question = None
                    bot_text = (
                        "Understood! I have kept your reservation in draft state on the booking page. "
                        "You can review or adjust your details anytime before finalizing."
                    )
                    actions = []
                    cards = []

                bot_msg = ChatMessage(
                    id=f"msg_{uuid.uuid4().hex[:8]}",
                    role=ChatRole.ASSISTANT,
                    content=bot_text,
                    data={"messageType": "BOOKING_PROCEED", "cards": cards, "actions": actions}
                )
                session_repo.add_message(session_id, bot_msg)
                session_repo.save_session(session)
                for act in actions:
                    await self.emit_event(session_id, "website_action", act)
                return {
                    "message": bot_msg.model_dump(),
                    "workflow_state": session.workflow_state.value,
                    "preferences": session.preferences.model_dump(),
                    "a2ui_surfaces": [],
                    "recommendations": [],
                    "website_actions": actions,
                    "actions": actions,
                    "cards": cards
                }

            elif session.pending_question == "CONFIRM_TRANSACTION":
                pending_checkout = session.workflow_data.get("pending_checkout", {})
                order_id = pending_checkout.get("order_id") or session.active_order_id or f"ORD-2026-{uuid.uuid4().hex[:6].upper()}"
                vehicle_id = pending_checkout.get("vehicle_id") or session.selected_vehicle_id or "CAR-001"
                amount = pending_checkout.get("amount", 25000.0)
                is_rent = pending_checkout.get("is_rent", False)
                target_vehicle = marketplace_repo.get_vehicle_by_id(vehicle_id) or marketplace_repo.get_all_vehicles()[0]
                payment_method = pending_checkout.get("payment_method", "UPI")

                if detected.is_affirmative:
                    session.pending_question = None
                    session.workflow_state = WorkflowState.CONFIRMED

                    # Process authoritative mock payment
                    from ..services.transaction_service import transaction_service
                    ok, payment, linked_entity, _, _, _ = transaction_service.process_payment_records(
                        order_or_booking_id=order_id,
                        amount=amount,
                        payment_method=payment_method,
                        user_id=user_id,
                        idempotency_key=f"idemp_pay_{order_id}",
                        simulated_scenario="SUCCESS"
                    )

                    car_title = f"{target_vehicle.brand} {target_vehicle.model}"
                    txn_id = payment.transactionId if payment else f"TXN-MOCK-{order_id[-6:]}"

                    showcase_card = {
                        "cardType": "PURCHASED_SHOWCASE",
                        "id": f"showcase_{order_id}",
                        "orderId": order_id,
                        "transactionId": txn_id,
                        "vehicleId": target_vehicle.id,
                        "brand": target_vehicle.brand,
                        "model": target_vehicle.model,
                        "year": target_vehicle.year,
                        "variant": getattr(target_vehicle, "variant", None) or "Luxury Edition",
                        "image": target_vehicle.image_url,
                        "amount": amount,
                        "paymentMethod": payment_method.upper(),
                        "status": "OWNED" if not is_rent else "RENTAL CONFIRMED",
                        "actions": [
                            {"label": "View in My Garage", "path": "/dashboard/vehicles"},
                            {"label": "View Payments", "path": "/dashboard/payments"}
                        ]
                    }

                    bot_text = (
                        f"🎉 **Transaction Complete & Confirmed!**\n\n"
                        f"I have successfully submitted your checkout and settled the mock transaction for the **{car_title}**.\n\n"
                        f"- **Order Reference:** `{order_id}`\n"
                        f"- **Transaction ID:** `{txn_id}`\n"
                        f"- **Amount Settled:** ₹{amount:,.0f} via {payment_method.upper()}\n"
                        f"- **Status:** Verified & Saved to your digital garage.\n\n"
                        f"I've updated the website in the background to display your official transaction receipt."
                    )

                    actions = [
                        {"type": "EXECUTE_CHECKOUT_SUBMIT", "payload": {"orderId": order_id, "status": "SUCCESS"}},
                        {"type": "REFRESH_DATA", "payload": {"resource": "all"}},
                        {"type": "NAVIGATE_TO_PAGE", "payload": {"path": f"/payment/result/{order_id}"}},
                        {"type": "NAVIGATE", "payload": {"path": f"/payment/result/{order_id}"}}
                    ]
                else:
                    session.pending_question = None
                    bot_text = (
                        "Understood! I have kept your reservation in draft state on the checkout page. "
                        "You can review or adjust your details anytime before finalizing."
                    )
                    actions = [
                        {"type": "NAVIGATE_TO_PAGE", "payload": {"path": f"/checkout/{order_id}"}},
                        {"type": "NAVIGATE", "payload": {"path": f"/checkout/{order_id}"}}
                    ]
                    showcase_card = None

                cards = [showcase_card] if showcase_card else []
                bot_msg = ChatMessage(
                    id=f"msg_{uuid.uuid4().hex[:8]}",
                    role=ChatRole.ASSISTANT,
                    content=bot_text,
                    data={"messageType": "TRANSACTION_CONFIRMATION", "cards": cards, "actions": actions}
                )
                session_repo.add_message(session_id, bot_msg)
                session_repo.save_session(session)
                for act in actions:
                    await self.emit_event(session_id, "website_action", act)
                return {
                    "message": bot_msg.model_dump(),
                    "workflow_state": session.workflow_state.value,
                    "preferences": session.preferences.model_dump(),
                    "a2ui_surfaces": [],
                    "recommendations": [],
                    "website_actions": actions,
                    "actions": actions,
                    "cards": cards
                }

        # -----------------------------------------------------------------
        # AUTONOMOUS CONTROLLER: BOOK_VEHICLE
        # "book this car", "buy this car", "book tata harrier", "book fortuner"
        # -----------------------------------------------------------------
        if detected.intent == "BOOK_VEHICLE":
            all_v = marketplace_repo.get_all_vehicles()
            v_name = detected.entities.get("vehicle_name", "").lower()
            target_vehicle = None
            if v_name:
                for v in all_v:
                    if v_name in v.model.lower() or v_name in v.brand.lower():
                        target_vehicle = v
                        break
            if not target_vehicle and session.selected_vehicle_id:
                target_vehicle = marketplace_repo.get_vehicle_by_id(session.selected_vehicle_id)
            if not target_vehicle and session.search_results:
                target_vehicle = marketplace_repo.get_vehicle_by_id(session.search_results[0]["vehicle"]["id"])
            if not target_vehicle:
                target_vehicle = all_v[0]

            is_rent = detected.entities.get("intent") == "rent" and session.preferences.intent != IntentType.BUY
            order_id = f"BK-2026-{uuid.uuid4().hex[:6].upper()}" if is_rent else f"ORD-2026-{uuid.uuid4().hex[:6].upper()}"
            daily_rate = target_vehicle.rental_price_per_day or 3500.0
            amount = round(daily_rate * 5 * 1.18 + 5000.0) if is_rent else 25000.0

            prefill_payload = {
                "customerName": "Alex Vance",
                "customerEmail": "demo@auramotors.com",
                "customerPhone": "+91 98765 43210",
                "deliveryCity": session.preferences.location or target_vehicle.location or "Delhi NCR",
                "pickupLocation": target_vehicle.location or "Delhi NCR",
                "pickupDate": "2026-12-15",
                "returnDate": "2026-12-20",
                "durationDays": 5,
                "paymentMethod": "upi",
                "upiId": "alex@okaxis",
                "vehicleId": target_vehicle.id,
                "amount": amount,
                "orderId": order_id
            }

            session.active_order_id = order_id
            session.selected_vehicle_id = target_vehicle.id
            session.pending_question = "PROCEED_TO_PAYMENT"
            session.workflow_data["pending_checkout"] = {
                "order_id": order_id,
                "vehicle_id": target_vehicle.id,
                "amount": amount,
                "is_rent": is_rent,
                "payment_method": "UPI",
                "upi_id": "alex@okaxis",
                "customer_name": "Alex Vance"
            }

            car_title = f"{target_vehicle.brand} {target_vehicle.model}"
            target_path = f"/booking/{target_vehicle.id}" if is_rent else f"/checkout/{order_id}"

            bot_text = (
                f"I have selected the **{car_title}** and opened the reservation page in the background.\n\n"
                f"I've filled in your verified details on the background booking form:\n"
                f"- **Vehicle:** {car_title} ({target_vehicle.year})\n"
                f"- **Pickup Location:** {prefill_payload['deliveryCity']}\n"
                f"- **Rental Dates:** Dec 15 to Dec 20, 2026 (5 Days)\n"
                f"- **Driver / Customer:** Alex Vance (+91 98765 43210)\n"
                f"- **Estimated Total:** ₹{amount:,.0f}\n\n"
                f"All fields have been filled on the background page. Would you like me to proceed to payment?"
            )

            actions = [
                {"type": "AUTO_CLICK_BOOK", "payload": {"vehicleId": target_vehicle.id, "orderId": order_id, "intent": "rent" if is_rent else "buy", "path": target_path}},
                {"type": "PREFILL_CHECKOUT_FORM", "payload": prefill_payload},
                {"type": "NAVIGATE_TO_PAGE", "payload": {"path": target_path}},
                {"type": "NAVIGATE", "payload": {"path": target_path}}
            ]

            bot_msg = ChatMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role=ChatRole.ASSISTANT,
                content=bot_text,
                data={"messageType": "CHECKOUT_PREFILL", "actions": actions}
            )
            session_repo.add_message(session_id, bot_msg)
            session_repo.save_session(session)
            for act in actions:
                await self.emit_event(session_id, "website_action", act)
            return {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": [],
                "recommendations": [],
                "website_actions": actions,
                "actions": actions
            }

        # -----------------------------------------------------------------
        # AUTONOMOUS CONTROLLER: VEHICLE_INQUIRY
        # "Tell me about Tata Harrier", "Show me Fortuner", "Hyundai Creta", etc.
        # -----------------------------------------------------------------
        if detected.intent == "VEHICLE_INQUIRY":
            all_v = marketplace_repo.get_all_vehicles()
            v_name = detected.entities.get("vehicle_name", "").lower()
            target_vehicle = None
            if v_name:
                for v in all_v:
                    if v_name in v.model.lower() or v_name in v.brand.lower():
                        target_vehicle = v
                        break
            if not target_vehicle and session.selected_vehicle_id:
                target_vehicle = marketplace_repo.get_vehicle_by_id(session.selected_vehicle_id)
            if not target_vehicle and session.search_results:
                target_vehicle = marketplace_repo.get_vehicle_by_id(session.search_results[0]["vehicle"]["id"])
            if not target_vehicle:
                target_vehicle = all_v[0]

            is_rent = (detected.entities.get("intent") == "rent") or (session.preferences.intent == IntentType.RENT)
            target_path = "/rent" if is_rent else "/buy"
            session.selected_vehicle_id = target_vehicle.id

            filter_payload = {
                "intent": "rent" if is_rent else "buy",
                "brand": target_vehicle.brand,
                "category": target_vehicle.category.value,
                "search": target_vehicle.model,
                "transmission": target_vehicle.transmission.value,
                "fuelType": target_vehicle.fuel_type.value,
                "seats": target_vehicle.seats,
            }

            actions = [
                {"type": "NAVIGATE_TO_PAGE", "payload": {"path": target_path}},
                {"type": "NAVIGATE", "payload": {"path": target_path}},
                {"type": "APPLY_FILTERS", "payload": filter_payload},
                {"type": "FILTER_VEHICLES", "payload": filter_payload}
            ]

            hp = getattr(getattr(target_vehicle, "specs", None), "horsepower", None)
            hp_str = f"{hp} HP" if hp else "2.0L Turbocharged (170 HP)"
            odo_str = f"{target_vehicle.odometer_km:,} km" if target_vehicle.odometer_km else "12,500 km"
            price_display = f"₹{target_vehicle.rental_price_per_day:,.0f}/day" if is_rent else f"₹{target_vehicle.purchase_price:,.0f}"

            bot_text = (
                f"### 🔍 Vehicle Deep-Dive: {target_vehicle.brand} {target_vehicle.model} ({target_vehicle.year})\n\n"
                f"I've synchronized the background page to **{target_path}** and applied the filter for the **{target_vehicle.brand} {target_vehicle.model}**.\n\n"
                f"**Key Architecture & Specifications:**\n"
                f"- **Powertrain & Performance:** {hp_str} • {target_vehicle.transmission.value} • {target_vehicle.fuel_type.value}\n"
                f"- **Seating & Cabin:** {target_vehicle.seats}-Seater luxury cabin with high-grade ergonomics\n"
                f"- **Odometer & Inspection:** {odo_str} • {target_vehicle.condition.upper()} (200-point safety certified)\n"
                f"- **Price / Valuation:** {price_display}\n\n"
                f"**Verdict:** The {target_vehicle.brand} {target_vehicle.model} delivers class-leading highway poise, safety ratings, and dependable daily drivability.\n\n"
                f"Would you like to book or reserve this car? Just say *\"book this car\"* or click **Book / Reserve** on the card below."
            )

            surface_id = f"surf_inquiry_{uuid.uuid4().hex[:6]}"
            card_id = f"rec_card_{target_vehicle.id}"
            comps = [
                A2UIComponent(
                    id="inquiry_grid",
                    component="Grid",
                    properties={"columns": 1, "gap": "md"},
                    children=[card_id]
                ),
                A2UIComponent(
                    id=card_id,
                    component="VehicleCard",
                    properties={
                        "vehicleId": target_vehicle.id,
                        "brand": target_vehicle.brand,
                        "model": target_vehicle.model,
                        "year": target_vehicle.year,
                        "category": target_vehicle.category.value,
                        "transmission": target_vehicle.transmission.value,
                        "fuelType": target_vehicle.fuel_type.value,
                        "seats": target_vehicle.seats,
                        "priceDisplay": price_display,
                        "matchScore": 96.0,
                        "positiveMatches": [f"{target_vehicle.seats}-Seater luxury cabin", f"{target_vehicle.fuel_type.value} dynamic poise", "200-point certified"],
                        "tradeOffs": ["High marketplace demand in city"],
                        "explanation": f"Excellent poise, highway stability, and comfort.",
                        "imageUrl": target_vehicle.image_url,
                        "actionId": "select_vehicle",
                        "actionData": {"vehicle_id": target_vehicle.id}
                    }
                )
            ]
            await self.emit_event(session_id, "a2ui", {
                "type": "createSurface",
                "surfaceId": surface_id,
                "components": [c.model_dump() for c in comps]
            })

            card = {
                "cardType": "VEHICLE",
                "id": target_vehicle.id,
                "brand": target_vehicle.brand,
                "model": target_vehicle.model,
                "year": target_vehicle.year,
                "category": target_vehicle.category.value,
                "purchasePrice": target_vehicle.purchase_price,
                "rentalPrice": target_vehicle.rental_price_per_day,
                "status": "AVAILABLE",
                "image": target_vehicle.image_url,
                "actions": [
                    {"label": "Book / Reserve", "action": "select_vehicle", "vehicleId": target_vehicle.id},
                    {"label": "View Details", "path": f"/vehicles/{target_vehicle.id}"}
                ]
            }

            bot_msg = ChatMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role=ChatRole.ASSISTANT,
                content=bot_text,
                a2ui_surfaces=[surface_id],
                data={"messageType": "VEHICLE_INQUIRY", "cards": [card], "actions": actions}
            )
            session_repo.add_message(session_id, bot_msg)
            session_repo.save_session(session)
            for act in actions:
                await self.emit_event(session_id, "website_action", act)
            return {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": [surface_id],
                "recommendations": [],
                "website_actions": actions,
                "actions": actions,
                "cards": [card]
            }

        # -----------------------------------------------------------------
        # SCENARIO A: VIEW_MY_VEHICLES (Show me my cars)
        # -----------------------------------------------------------------
        if detected.intent == "VIEW_MY_VEHICLES":
            vehicles = user_data_repo.get_user_owned_vehicles(user_id)
            cards = [
                {
                    "cardType": "OWNED_VEHICLE",
                    "id": v.id,
                    "vehicleId": v.vehicleId,
                    "brand": v.brand,
                    "model": v.model,
                    "variant": v.variant,
                    "year": v.year,
                    "currentEstimatedValue": v.currentEstimatedValue,
                    "source": v.source.value if hasattr(v.source, "value") else str(v.source),
                    "image": v.image,
                    "status": v.status,
                    "actions": [
                        {"label": "Sell Vehicle", "action": "SELL_VEHICLE", "vehicleId": v.id},
                        {"label": "View Garage", "path": "/dashboard/vehicles"}
                    ]
                }
                for v in vehicles
            ]
            bot_text = f"Here are the {len(vehicles)} vehicles associated with your account in your digital garage."
            actions = [
                {"type": "NAVIGATE_TO_PAGE", "payload": {"path": "/dashboard/vehicles"}},
                {"type": "NAVIGATE", "payload": {"path": "/dashboard/vehicles"}},
                {"type": "REFRESH_DATA", "payload": {"resource": "myVehicles"}}
            ]
            bot_msg = ChatMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role=ChatRole.ASSISTANT,
                content=bot_text,
                data={"messageType": "GARAGE_VEHICLES", "cards": cards, "actions": actions}
            )
            session_repo.add_message(session_id, bot_msg)
            session_repo.save_session(session)
            for act in actions:
                await self.emit_event(session_id, "website_action", act)
            return {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": [],
                "recommendations": [],
                "website_actions": actions,
                "actions": actions,
                "cards": cards
            }

        # -----------------------------------------------------------------
        # SCENARIO B: VIEW_PURCHASES (Show me all the cars I have purchased)
        # -----------------------------------------------------------------
        if detected.intent == "VIEW_PURCHASES":
            session.preferences.intent = IntentType.PURCHASE_HISTORY
            purchases = user_data_repo.get_user_purchases(user_id)
            cards = [
                {
                    "cardType": "PURCHASE",
                    "id": p.id,
                    "orderId": p.orderId,
                    "brand": p.vehicleSnapshot.brand,
                    "model": p.vehicleSnapshot.model,
                    "variant": p.vehicleSnapshot.variant,
                    "purchasePrice": p.purchasePrice,
                    "purchaseDate": p.purchaseDate,
                    "purchaseStatus": p.purchaseStatus.value if hasattr(p.purchaseStatus, "value") else str(p.purchaseStatus),
                    "transactionReference": p.transactionReference,
                    "image": p.vehicleSnapshot.image,
                    "deliveryCity": p.deliveryCity,
                    "actions": [
                        {"label": "View Purchases", "path": "/dashboard/purchases"}
                    ]
                }
                for p in purchases
            ]
            if purchases:
                p_lines = [f"{i}. **{p.vehicleSnapshot.brand} {p.vehicleSnapshot.model}** — ₹{p.purchasePrice:,.0f} (Order: `{p.orderId}`)" for i, p in enumerate(purchases[:3], 1)]
                bot_text = f"Here are your verified vehicle purchases on **Aura Motors**:\n\n" + "\n".join(p_lines) + f"\n\nI've navigated you directly to your **My Purchases** dashboard."
            else:
                bot_text = "You don't have any vehicle purchases recorded in your account yet. I've navigated you to your **My Purchases** dashboard."

            actions = [
                {"type": "NAVIGATE_TO_PAGE", "payload": {"path": "/dashboard/purchases"}},
                {"type": "NAVIGATE", "payload": {"path": "/dashboard/purchases"}},
                {"type": "REFRESH_DATA", "payload": {"resource": "myPurchases"}}
            ]
            bot_msg = ChatMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role=ChatRole.ASSISTANT,
                content=bot_text,
                data={"messageType": "PURCHASE_HISTORY", "cards": cards, "actions": actions}
            )
            session_repo.add_message(session_id, bot_msg)
            session_repo.save_session(session)
            for act in actions:
                await self.emit_event(session_id, "website_action", act)
            return {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": [],
                "recommendations": [],
                "website_actions": actions,
                "actions": actions,
                "cards": cards
            }

        # -----------------------------------------------------------------
        # SCENARIO C: VIEW_RENTALS (Show my rental history)
        # -----------------------------------------------------------------
        if detected.intent == "VIEW_RENTALS":
            session.preferences.intent = IntentType.RENTAL_HISTORY
            rentals = user_data_repo.get_user_rentals(user_id)
            cards = [
                {
                    "cardType": "RENTAL",
                    "id": r.id,
                    "orderId": r.orderId,
                    "brand": r.vehicleSnapshot.brand,
                    "model": r.vehicleSnapshot.model,
                    "pickupDate": r.pickupDate,
                    "returnDate": r.returnDate,
                    "durationDays": r.durationDays,
                    "rentalAmount": r.rentalAmount,
                    "rentalStatus": r.rentalStatus.value if hasattr(r.rentalStatus, "value") else str(r.rentalStatus),
                    "pickupLocation": r.pickupLocation,
                    "image": r.vehicleSnapshot.image,
                    "actions": [
                        {"label": "View Rentals", "path": "/dashboard/rentals"}
                    ]
                }
                for r in rentals
            ]
            if rentals:
                r_lines = [f"{i}. **{r.vehicleSnapshot.brand} {r.vehicleSnapshot.model}** — {r.pickupDate} to {r.returnDate} (Booking: `{r.orderId or r.id}`)" for i, r in enumerate(rentals[:3], 1)]
                bot_text = f"Here are your active rental reservations on **Aura Motors**:\n\n" + "\n".join(r_lines) + f"\n\nI've navigated you to your **My Rentals** dashboard."
            else:
                bot_text = "You don't have any active rental bookings on record currently. I've navigated you to your **My Rentals** dashboard."

            actions = [
                {"type": "NAVIGATE_TO_PAGE", "payload": {"path": "/dashboard/rentals"}},
                {"type": "NAVIGATE", "payload": {"path": "/dashboard/rentals"}},
                {"type": "REFRESH_DATA", "payload": {"resource": "myRentals"}}
            ]
            bot_msg = ChatMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role=ChatRole.ASSISTANT,
                content=bot_text,
                data={"messageType": "RENTAL_HISTORY", "cards": cards, "actions": actions}
            )
            session_repo.add_message(session_id, bot_msg)
            session_repo.save_session(session)
            for act in actions:
                await self.emit_event(session_id, "website_action", act)
            return {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": [],
                "recommendations": [],
                "website_actions": actions,
                "actions": actions,
                "cards": cards
            }

        # -----------------------------------------------------------------
        # SCENARIO G: VIEW_PAYMENT_HISTORY (Show my previous payments)
        # -----------------------------------------------------------------
        if detected.intent == "VIEW_PAYMENT_HISTORY":
            payments = user_data_repo.get_user_payments(user_id)
            cards = [
                {
                    "cardType": "PAYMENT",
                    "id": p.id,
                    "orderId": p.orderId,
                    "amount": p.amount,
                    "currency": p.currency,
                    "paymentMethod": p.paymentMethod,
                    "paymentStatus": p.paymentStatus.value if hasattr(p.paymentStatus, "value") else str(p.paymentStatus),
                    "paymentReference": p.paymentReference,
                    "createdAt": p.createdAt,
                    "actions": [
                        {"label": "View Payments", "path": "/dashboard/payments"}
                    ]
                }
                for p in payments
            ]
            p_lines = [f"{i}. **₹{p.amount:,.0f}** — {p.paymentMethod.upper()} • Status: **{p.paymentStatus.value}** (Ref: `{p.transactionId}`)" for i, p in enumerate(payments[:3], 1)]
            bot_text = f"Here is your payment history and transaction ledger on **Aura Motors**:\n\n" + "\n".join(p_lines) + f"\n\nI've navigated you to your **Payment History** dashboard."

            actions = [
                {"type": "NAVIGATE_TO_PAGE", "payload": {"path": "/dashboard/payments"}},
                {"type": "NAVIGATE", "payload": {"path": "/dashboard/payments"}},
                {"type": "REFRESH_DATA", "payload": {"resource": "myPayments"}}
            ]
            bot_msg = ChatMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role=ChatRole.ASSISTANT,
                content=bot_text,
                data={"messageType": "PAYMENT_HISTORY", "cards": cards, "actions": actions}
            )
            session_repo.add_message(session_id, bot_msg)
            session_repo.save_session(session)
            for act in actions:
                await self.emit_event(session_id, "website_action", act)
            return {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": [],
                "recommendations": [],
                "website_actions": actions,
                "actions": actions,
                "cards": cards
            }

        # -----------------------------------------------------------------
        # VIEW_SELLING_LISTINGS
        # -----------------------------------------------------------------
        if detected.intent == "VIEW_SELLING_LISTINGS":
            session.preferences.intent = IntentType.SELLING_HISTORY
            listings = user_data_repo.get_user_listings(user_id)
            cards = [
                {
                    "cardType": "LISTING",
                    "id": l.id,
                    "brand": l.brand,
                    "model": l.model,
                    "year": l.year,
                    "expectedPrice": l.expected_price,
                    "kmsDriven": l.kms_driven,
                    "status": l.status.value if hasattr(l.status, "value") else str(l.status),
                    "image": l.images[0] if l.images else "https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?auto=format&fit=crop&w=800&q=80",
                    "actions": [
                        {"label": "View Listing", "path": "/dashboard/listings"}
                    ]
                }
                for l in listings
            ]
            if listings:
                l_lines = [f"{i}. **{l.year} {l.brand} {l.model}** — Status: **{l.status.value}** (Asking ₹{l.expected_price:,.0f})" for i, l in enumerate(listings[:5], 1)]
                bot_text = "Here are your vehicle listings on **Aura Motors**:\n\n" + "\n".join(l_lines) + "\n\nI've navigated you to your **My Listings** dashboard."
            else:
                bot_text = "You don't have any vehicle listings on sale currently. I've navigated you to your **My Listings** dashboard."
            actions = [
                {"type": "NAVIGATE_TO_PAGE", "payload": {"path": "/dashboard/listings"}},
                {"type": "NAVIGATE", "payload": {"path": "/dashboard/listings"}},
                {"type": "REFRESH_DATA", "payload": {"resource": "myListings"}}
            ]
            bot_msg = ChatMessage(id=f"msg_{uuid.uuid4().hex[:8]}", role=ChatRole.ASSISTANT, content=bot_text, data={"cards": cards, "actions": actions})
            session_repo.add_message(session_id, bot_msg)
            session_repo.save_session(session)
            for act in actions:
                await self.emit_event(session_id, "website_action", act)
            return {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": [],
                "recommendations": [],
                "website_actions": actions,
                "actions": actions,
                "cards": cards
            }

        # -----------------------------------------------------------------
        # SCENARIO D: SELL_VEHICLE (I want to sell my sedan)
        # -----------------------------------------------------------------
        if detected.intent == "SELL_VEHICLE":
            from ..models.preferences import SellDetails
            from ..models.vehicle import VehicleCategory
            session.preferences.intent = IntentType.SELL
            if not session.preferences.sell_details:
                session.preferences.sell_details = SellDetails()
            if detected.entities.get("category"):
                try:
                    session.preferences.category = VehicleCategory(detected.entities["category"])
                    session.preferences.vehicle_category = detected.entities["category"]
                except Exception:
                    pass
            session.active_workflow = "SELL_WORKFLOW"
            session.pending_question = "IS_REGISTERED_IN_NAME"

            owned_vehicles = user_data_repo.get_user_owned_vehicles(user_id)
            cat_requested = detected.entities.get("category", "").lower()
            matching_owned = None
            if cat_requested:
                matching_owned = next((v for v in owned_vehicles if cat_requested in (v.model.lower() + " " + v.brand.lower())), None)
            elif owned_vehicles:
                matching_owned = owned_vehicles[0]

            if matching_owned:
                session.workflow_data["matching_owned_vehicle_id"] = matching_owned.id
                bot_text = f"I can certainly help you sell your **{matching_owned.brand} {matching_owned.model}** on Aura Motors.\n\nIs the vehicle currently registered in your name?"
            else:
                target_cat = detected.entities.get("category", "vehicle")
                bot_text = f"I can certainly help you list your {target_cat.lower()} for sale on Aura Motors.\n\nIs the vehicle currently registered in your name?"

            actions = [
                {"type": "NAVIGATE_TO_PAGE", "payload": {"path": "/sell-car"}},
                {"type": "NAVIGATE", "payload": {"path": "/sell-car"}}
            ]
            bot_msg = ChatMessage(id=f"msg_{uuid.uuid4().hex[:8]}", role=ChatRole.ASSISTANT, content=bot_text)
            session_repo.add_message(session_id, bot_msg)
            session_repo.save_session(session)
            for act in actions:
                await self.emit_event(session_id, "website_action", act)
            return {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": [],
                "recommendations": [],
                "website_actions": actions,
                "actions": actions
            }

        # -----------------------------------------------------------------
        # UPDATE_PROFILE & VIEW_PROFILE
        # -----------------------------------------------------------------
        if detected.intent == "UPDATE_PROFILE":
            phone = detected.entities.get("phone")
            if phone:
                from ..api.routes_auth import _USERS_DB
                if "demo@auramotors.com" in _USERS_DB:
                    _USERS_DB["demo@auramotors.com"]["phone"] = phone
                bot_text = f"I have updated your phone number to **{phone}** and navigated you to your **Member Profile**."
            else:
                bot_text = "I've navigated you to your **Member Profile** where you can review your verified KYC credentials and contact details."

            actions = [
                {"type": "NAVIGATE_TO_PAGE", "payload": {"path": "/dashboard/profile"}},
                {"type": "NAVIGATE", "payload": {"path": "/dashboard/profile"}}
            ]
            bot_msg = ChatMessage(id=f"msg_{uuid.uuid4().hex[:8]}", role=ChatRole.ASSISTANT, content=bot_text)
            session_repo.add_message(session_id, bot_msg)
            session_repo.save_session(session)
            for act in actions:
                await self.emit_event(session_id, "website_action", act)
            return {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": [],
                "recommendations": [],
                "website_actions": actions,
                "actions": actions
            }

        # -----------------------------------------------------------------
        # VIEW_DASHBOARD
        # -----------------------------------------------------------------
        if detected.intent == "VIEW_DASHBOARD":
            bot_text = "I've navigated you to your **User Dashboard** overview."
            actions = [
                {"type": "NAVIGATE_TO_PAGE", "payload": {"path": "/dashboard"}},
                {"type": "NAVIGATE", "payload": {"path": "/dashboard"}}
            ]
            bot_msg = ChatMessage(id=f"msg_{uuid.uuid4().hex[:8]}", role=ChatRole.ASSISTANT, content=bot_text)
            session_repo.add_message(session_id, bot_msg)
            session_repo.save_session(session)
            for act in actions:
                await self.emit_event(session_id, "website_action", act)
            return {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": [],
                "recommendations": [],
                "website_actions": actions,
                "actions": actions
            }

        # -----------------------------------------------------------------
        # CANCEL_BOOKING
        # -----------------------------------------------------------------
        if detected.intent == "CANCEL_BOOKING":
            order_id = detected.entities.get("order_id")
            from ..models.rental import RentalStatus
            cancelled_ref = "your booking"
            if order_id:
                rental = user_data_repo.get_rental_by_order(order_id)
                if rental:
                    rental.rentalStatus = RentalStatus.CANCELLED
                    cancelled_ref = f"booking `{order_id}`"
            else:
                # Cancel latest rental if available
                user_rentals = user_data_repo.get_user_rentals(user_id)
                if user_rentals:
                    user_rentals[0].rentalStatus = RentalStatus.CANCELLED
                    cancelled_ref = f"booking `{user_rentals[0].orderId}`"

            bot_text = f"{cancelled_ref.capitalize()} has been successfully cancelled. I've updated your rentals dashboard."
            actions = [
                {"type": "NAVIGATE_TO_PAGE", "payload": {"path": "/dashboard/rentals"}},
                {"type": "NAVIGATE", "payload": {"path": "/dashboard/rentals"}},
                {"type": "REFRESH_DATA", "payload": {"resource": "myRentals"}},
                {"type": "SHOW_NOTIFICATION", "payload": {"message": "Booking cancelled successfully"}}
            ]
            bot_msg = ChatMessage(id=f"msg_{uuid.uuid4().hex[:8]}", role=ChatRole.ASSISTANT, content=bot_text)
            session_repo.add_message(session_id, bot_msg)
            session_repo.save_session(session)
            for act in actions:
                await self.emit_event(session_id, "website_action", act)
            return {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": [],
                "recommendations": [],
                "website_actions": actions,
                "actions": actions
            }

        # -----------------------------------------------------------------
        # NAVIGATE
        # -----------------------------------------------------------------
        if detected.intent == "NAVIGATE":
            target_path = detected.entities.get("path", "/")
            bot_text = f"Navigating to **{target_path}**."
            actions = [
                {"type": "NAVIGATE_TO_PAGE", "payload": {"path": target_path}},
                {"type": "NAVIGATE", "payload": {"path": target_path}}
            ]
            bot_msg = ChatMessage(id=f"msg_{uuid.uuid4().hex[:8]}", role=ChatRole.ASSISTANT, content=bot_text)
            session_repo.add_message(session_id, bot_msg)
            session_repo.save_session(session)
            for act in actions:
                await self.emit_event(session_id, "website_action", act)
            return {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": [],
                "recommendations": [],
                "website_actions": actions,
                "actions": actions
            }

        # -----------------------------------------------------------------
        # SCENARIO: COMPARE_VEHICLES (Compare two vehicles side-by-side)
        # -----------------------------------------------------------------
        if detected.intent == "COMPARE_VEHICLES":
            all_v = marketplace_repo.get_all_vehicles()
            text_lower = user_content.lower()
            matched_vehicles = []
            for v in all_v:
                b_name = v.brand.lower()
                m_name = v.model.lower()
                primary_model_word = m_name.split()[0]
                if f"{b_name} {primary_model_word}" in text_lower or (b_name in text_lower and primary_model_word in text_lower):
                    if v not in matched_vehicles:
                        matched_vehicles.append(v)

            if len(matched_vehicles) >= 2:
                comp_v1, comp_v2 = matched_vehicles[0], matched_vehicles[1]
                compared_ids = [comp_v1.id, comp_v2.id]
            elif session.search_results and len(session.search_results) >= 2:
                compared_ids = [session.search_results[0]["vehicle"]["id"], session.search_results[1]["vehicle"]["id"]]
                comp_v1 = marketplace_repo.get_vehicle_by_id(compared_ids[0])
                comp_v2 = marketplace_repo.get_vehicle_by_id(compared_ids[1])
            elif len(matched_vehicles) == 1:
                comp_v1 = matched_vehicles[0]
                comp_v2 = next((v for v in all_v if v.category == comp_v1.category and v.id != comp_v1.id), all_v[0])
                compared_ids = [comp_v1.id, comp_v2.id]
            else:
                comp_v1, comp_v2 = all_v[0], all_v[1]
                compared_ids = [comp_v1.id, comp_v2.id]

            v1_name = f"{comp_v1.brand} {comp_v1.model}" if comp_v1 else "Vehicle 1"
            v2_name = f"{comp_v2.brand} {comp_v2.model}" if comp_v2 else "Vehicle 2"

            bot_text = (
                f"### Benchmark Analysis: {v1_name} vs {v2_name}\n\n"
                f"I've configured your side-by-side comparison matrix and navigated the website directly to the **Compare Cars** page.\n\n"
                f"**1. Driving Dynamics & Engine Output:**\n"
                f"- **{v1_name}**: Features refined suspension geometry, agile power delivery, and superior maneuverability for daily urban driving.\n"
                f"- **{v2_name}**: Dominant road presence, high torque output, and unshakable highway stability for long journeys.\n\n"
                f"**2. Fuel Efficiency & Maintenance:**\n"
                f"- **{v1_name}**: Approx {getattr(comp_v1, 'mileage_kmpl', 16.5) or 16.5} KMPL, lower scheduled servicing overheads.\n"
                f"- **{v2_name}**: Approx {getattr(comp_v2, 'mileage_kmpl', 14.2) or 14.2} KMPL, proven legendary durability with industry-leading resale retention.\n\n"
                f"**Verdict:** Choose **{v1_name}** for city comfort, ergonomics, and daily touring; choose **{v2_name}** for uncompromising presence, off-road authority, and long-distance touring."
            )

            actions = [
                {"type": "ADD_TO_COMPARISON", "payload": {"vehicleIds": compared_ids}},
                {"type": "NAVIGATE_TO_PAGE", "payload": {"path": "/compare"}},
                {"type": "NAVIGATE", "payload": {"path": "/compare"}}
            ]
            bot_msg = ChatMessage(id=f"msg_{uuid.uuid4().hex[:8]}", role=ChatRole.ASSISTANT, content=bot_text)
            session_repo.add_message(session_id, bot_msg)
            session_repo.save_session(session)
            for act in actions:
                await self.emit_event(session_id, "website_action", act)
            return {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": [],
                "recommendations": [],
                "website_actions": actions,
                "actions": actions
            }

        # -----------------------------------------------------------------
        # SCENARIO E: SEARCH_VEHICLES (Find an SUV under ₹15 lakh / i want to buy a sedan)
        # -----------------------------------------------------------------
        if detected.intent == "SEARCH_VEHICLES":
            from ..models.vehicle import VehicleCategory
            updated_prefs, _ = AdaptiveInterviewAgent.extract_preferences(
                user_content, session.preferences
            )
            session.preferences = updated_prefs
            session.preferences.intent = IntentType.BUY
            if detected.entities.get("category"):
                try:
                    session.preferences.category = VehicleCategory(detected.entities["category"])
                except Exception:
                    pass
            if detected.entities.get("budget_max"):
                session.preferences.budget_max = detected.entities["budget_max"]
            if detected.entities.get("location"):
                session.preferences.location = detected.entities["location"]

            cat_val = session.preferences.category.value if session.preferences.category else None
            max_b = session.preferences.budget_max
            loc = session.preferences.location
            seats = session.preferences.seating_capacity

            matching_vehicles = marketplace_repo.search_vehicles(
                intent="buy",
                category=cat_val,
                location=loc,
                max_price=max_b,
                seats=seats
            )
            ranked = RankingEngine.rank_vehicles(matching_vehicles, session.preferences, limit=5)
            session.search_results = [r.to_dict() for r in ranked]

            filter_payload = {
                "intent": "buy",
                "category": cat_val or "",
                "location": loc or "",
                "maxPrice": max_b or 50000000.0,
                "minPrice": 0
            }
            if seats:
                filter_payload["seats"] = seats

            actions = [
                {"type": "NAVIGATE_TO_PAGE", "payload": {"path": "/buy"}},
                {"type": "NAVIGATE", "payload": {"path": "/buy"}},
                {"type": "APPLY_FILTERS", "payload": filter_payload},
                {"type": "FILTER_VEHICLES", "payload": filter_payload}
            ]

            cards = [
                {
                    "cardType": "VEHICLE",
                    "id": r.vehicle.id,
                    "brand": r.vehicle.brand,
                    "model": r.vehicle.model,
                    "year": r.vehicle.year,
                    "category": r.vehicle.category.value,
                    "purchasePrice": r.vehicle.purchase_price,
                    "status": "AVAILABLE",
                    "image": r.vehicle.image_url,
                    "actions": [
                        {"label": "View Details", "path": f"/vehicles/{r.vehicle.id}"}
                    ]
                }
                for r in ranked
            ]

            cat_display = cat_val or (f"{seats}-seater" if seats else "vehicle")
            budget_display = f" under ₹{max_b/100000:,.0f} Lakh" if max_b else ""
            loc_display = f" in {loc}" if loc else ""

            if loc and max_b:
                bot_text = (
                    f"I've updated our vehicle catalogue and navigated you directly to our **Buy Cars** inventory filtered for **{cat_display}s**{budget_display}{loc_display}.\n\n"
                    f"Here are {len(ranked)} verified recommendations matching your exact criteria with complete inspection reports."
                )
            else:
                followup_q = AdaptiveInterviewAgent.generate_followup_question(session.preferences)
                bot_text = (
                    f"I've updated our website catalogue and navigated you to the **Buy Cars** inventory filtered for **{cat_display}s**{budget_display}.\n\n"
                    f"You can explore all matching listings on this page. {followup_q}"
                )

            session.workflow_state = WorkflowState.RECOMMENDATIONS_READY

            a2ui_surfaces = []
            if ranked:
                surface_id = f"surf_rec_{uuid.uuid4().hex[:6]}"
                rec_components = self._build_recommendations_a2ui_components(ranked, False)
                await self.emit_event(session_id, "a2ui", {
                    "type": "createSurface",
                    "surfaceId": surface_id,
                    "components": [c.model_dump() for c in rec_components]
                })
                a2ui_surfaces = [surface_id]

            bot_msg = ChatMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role=ChatRole.ASSISTANT,
                content=bot_text,
                a2ui_surfaces=a2ui_surfaces,
                data={"messageType": "VEHICLE_SEARCH", "cards": cards, "actions": actions}
            )
            session_repo.add_message(session_id, bot_msg)
            session_repo.save_session(session)
            for act in actions:
                await self.emit_event(session_id, "website_action", act)
            return {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": a2ui_surfaces,
                "recommendations": session.search_results,
                "website_actions": actions,
                "actions": actions,
                "cards": cards
            }

        # -----------------------------------------------------------------
        # SCENARIO F: RENT_VEHICLE (I want to rent a sedan in Delhi)
        # -----------------------------------------------------------------
        if detected.intent == "RENT_VEHICLE":
            from ..models.vehicle import VehicleCategory
            updated_prefs, _ = AdaptiveInterviewAgent.extract_preferences(
                user_content, session.preferences
            )
            session.preferences = updated_prefs
            session.preferences.intent = IntentType.RENT
            if detected.entities.get("category"):
                try:
                    session.preferences.category = VehicleCategory(detected.entities["category"])
                except Exception:
                    pass
            if detected.entities.get("location"):
                session.preferences.location = detected.entities["location"]

            cat_val = session.preferences.category.value if session.preferences.category else None
            loc = session.preferences.location
            seats = session.preferences.seating_capacity

            max_b = session.preferences.budget_max or (session.preferences.budget.amount if session.preferences.budget else None)
            matching_vehicles = marketplace_repo.search_vehicles(
                intent="rent",
                category=cat_val,
                location=loc,
                seats=seats,
                max_price=max_b
            )
            ranked = RankingEngine.rank_vehicles(matching_vehicles, session.preferences, limit=5)
            session.search_results = [r.to_dict() for r in ranked]

            filter_payload = {
                "intent": "rent",
                "category": cat_val or "",
                "location": loc or "",
                "maxPrice": max_b or 50000.0,
                "minPrice": 0
            }
            if seats:
                filter_payload["seats"] = seats

            actions = [
                {"type": "NAVIGATE_TO_PAGE", "payload": {"path": "/rent"}},
                {"type": "NAVIGATE", "payload": {"path": "/rent"}},
                {"type": "APPLY_FILTERS", "payload": filter_payload},
                {"type": "FILTER_VEHICLES", "payload": filter_payload}
            ]

            cards = [
                {
                    "cardType": "VEHICLE",
                    "id": r.vehicle.id,
                    "brand": r.vehicle.brand,
                    "model": r.vehicle.model,
                    "year": r.vehicle.year,
                    "category": r.vehicle.category.value,
                    "totalAmount": r.vehicle.rental_price_per_day,
                    "status": "AVAILABLE",
                    "image": r.vehicle.image_url,
                    "actions": [
                        {"label": "Book Now", "path": f"/vehicles/{r.vehicle.id}"}
                    ]
                }
                for r in ranked
            ]

            cat_display = cat_val or (f"{seats}-seater" if seats else "vehicle")
            loc_display = f" in {loc}" if loc else ""
            bot_text = (
                f"I've updated our rental fleet filters and navigated you to the **Rent a Car** portal for **{cat_display}s**{loc_display}.\n\n"
                f"How many days would you like to rent (e.g., 3 days or 5 days), and what is your pickup date?"
            )

            a2ui_surfaces = []
            has_date = bool(session.preferences.rental_start_date or (session.preferences.rental_details and session.preferences.rental_details.pickup_date))
            has_dur = bool(session.preferences.rental_details and session.preferences.rental_details.rental_duration_days)
            diag = None
            if not has_date or not has_dur:
                session.workflow_state = WorkflowState.INTERVIEWING
                session.search_results = []
            elif ranked:
                session.workflow_state = WorkflowState.RECOMMENDATIONS_READY
                surface_id = f"surf_rec_{uuid.uuid4().hex[:6]}"
                rec_components = self._build_recommendations_a2ui_components(ranked, True)
                await self.emit_event(session_id, "a2ui", {
                    "type": "createSurface",
                    "surfaceId": surface_id,
                    "components": [c.model_dump() for c in rec_components]
                })
                a2ui_surfaces = [surface_id]
            else:
                session.workflow_state = WorkflowState.RECOMMENDATIONS_READY
                all_v = marketplace_repo.get_all_vehicles()
                diag = RankingEngine.diagnose_zero_results(all_v, session.preferences)
                surface_id = f"surf_zero_{uuid.uuid4().hex[:6]}"
                a2ui_surfaces = [surface_id]

            bot_msg = ChatMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role=ChatRole.ASSISTANT,
                content=bot_text,
                a2ui_surfaces=a2ui_surfaces,
                data={"messageType": "RENTAL_SEARCH", "cards": cards, "actions": actions}
            )
            session_repo.add_message(session_id, bot_msg)
            session_repo.save_session(session)
            for act in actions:
                await self.emit_event(session_id, "website_action", act)
            res_dict = {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": a2ui_surfaces,
                "recommendations": session.search_results,
                "website_actions": actions,
                "actions": actions,
                "cards": cards
            }
            if diag:
                res_dict["diagnostics"] = diag
            return res_dict

        # -----------------------------------------------------------------
        # Preference Extraction for Vehicle Search, Buy, Rent, Compare
        # -----------------------------------------------------------------
        updated_prefs, extracted_fields = AdaptiveInterviewAgent.extract_preferences(
            user_content, session.preferences
        )
        session.preferences = updated_prefs

        # Check for Comparison Request: "compare", "comparison", " vs ", "versus", "difference between"
        text_lower = user_content.lower()
        is_comparison = any(term in text_lower for term in ["compare", "comparison", " vs ", "versus", "difference between"])
        if is_comparison:
            all_v = marketplace_repo.get_all_vehicles()
            # Match specific vehicles mentioned in text
            matched_vehicles = []
            for v in all_v:
                b_name = v.brand.lower()
                m_name = v.model.lower()
                primary_model_word = m_name.split()[0]
                if f"{b_name} {primary_model_word}" in text_lower or (b_name in text_lower and primary_model_word in text_lower):
                    if v not in matched_vehicles:
                        matched_vehicles.append(v)

            if len(matched_vehicles) >= 2:
                comp_v1, comp_v2 = matched_vehicles[0], matched_vehicles[1]
                compared_ids = [comp_v1.id, comp_v2.id]
            elif session.search_results and len(session.search_results) >= 2:
                compared_ids = [session.search_results[0]["vehicle"]["id"], session.search_results[1]["vehicle"]["id"]]
                comp_v1 = marketplace_repo.get_vehicle_by_id(compared_ids[0])
                comp_v2 = marketplace_repo.get_vehicle_by_id(compared_ids[1])
            else:
                comp_v1, comp_v2 = all_v[0], all_v[1]
                compared_ids = [comp_v1.id, comp_v2.id]

            v1_name = f"{comp_v1.brand} {comp_v1.model}" if comp_v1 else "Vehicle 1"
            v2_name = f"{comp_v2.brand} {comp_v2.model}" if comp_v2 else "Vehicle 2"

            bot_text = (
                f"### Benchmark Analysis: {v1_name} vs {v2_name}\n\n"
                f"I've configured your side-by-side comparison matrix and navigated the website directly to the **Compare Cars** page.\n\n"
                f"**1. Driving Dynamics & Engine Output:**\n"
                f"- **{v1_name}**: Features refined suspension geometry, agile power delivery, and superior maneuverability for daily urban driving.\n"
                f"- **{v2_name}**: Heavy-duty ladder-frame chassis with dominant ground clearance, high torque output, and unshakable highway stability.\n\n"
                f"**2. Fuel Efficiency & Maintenance:**\n"
                f"- **{v1_name}**: Approx {comp_v1.mileage_kmpl or 16.5} KMPL, lower scheduled servicing overheads.\n"
                f"- **{v2_name}**: Approx {comp_v2.mileage_kmpl or 14.2} KMPL, proven legendary durability with industry-leading resale retention.\n\n"
                f"**Verdict:** Choose **{v1_name}** for city comfort, ergonomics, and daily touring; choose **{v2_name}** for uncompromising presence, off-road authority, and long-distance touring."
            )

            actions = [
                {
                    "type": "ADD_TO_COMPARISON",
                    "payload": {"vehicleIds": compared_ids}
                },
                {
                    "type": "NAVIGATE_TO_PAGE",
                    "payload": {"path": "/compare"}
                }
            ]

            bot_msg = ChatMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role=ChatRole.ASSISTANT,
                content=bot_text
            )
            session_repo.add_message(session_id, bot_msg)
            session_repo.save_session(session)

            for act in actions:
                await self.emit_event(session_id, "website_action", act)

            return {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": [],
                "recommendations": session.search_results,
                "website_actions": actions
            }

        # 4. Check if interview is complete or more info is needed
        missing = AdaptiveInterviewAgent.check_missing_fields(session.preferences)

        if missing:
            # Need more details: stay in or return to INTERVIEWING
            if session.workflow_state != WorkflowState.INTERVIEWING:
                StateMachine.validate_transition(session.workflow_state, WorkflowState.INTERVIEWING)
                session.workflow_state = WorkflowState.INTERVIEWING

            # Invalidate stale recommendations since requirements are incomplete
            session.search_results = []
            session.selected_vehicle_id = None

            followup_text = AdaptiveInterviewAgent.generate_followup_question(session.preferences)

            # Determine appropriate website navigation route
            is_rent = (session.preferences.intent == "RENT" or session.preferences.intent == IntentType.RENT)
            if not is_rent:
                target_path = "/buy"
                portal_label = "Buy Cars"
            else:
                target_path = "/rent"
                portal_label = "Rent a Car"

            # Build website filter payload with clear budget defaults to avoid cross-intent contamination
            default_max = 50000000.0 if not is_rent else 50000.0
            filter_payload = {
                "intent": "rent" if is_rent else "buy",
                "category": session.preferences.category.value if session.preferences.category else "",
                "transmission": session.preferences.transmission if session.preferences.transmission not in ["any", None] else "",
                "location": session.preferences.location or "",
                "brand": session.preferences.preferred_brands[0] if session.preferences.preferred_brands else "",
                "minPrice": session.preferences.budget_min or 0,
                "maxPrice": session.preferences.budget_max or (session.preferences.budget.amount if session.preferences.budget else default_max),
            }
            if session.preferences.seating_capacity:
                filter_payload["seats"] = session.preferences.seating_capacity

            actions = [
                {
                    "type": "NAVIGATE_TO_PAGE",
                    "payload": {"path": target_path}
                },
                {
                    "type": "APPLY_FILTERS",
                    "payload": filter_payload
                }
            ]

            # Query matching vehicles for live preview
            max_b = session.preferences.budget_max or (session.preferences.budget.amount if session.preferences.budget else None)
            min_b = session.preferences.budget_min
            preview_matches = marketplace_repo.search_vehicles(
                intent="rent" if is_rent else "buy",
                category=session.preferences.category.value if session.preferences.category else None,
                location=session.preferences.location,
                min_price=min_b,
                max_price=max_b,
                transmission=session.preferences.transmission if session.preferences.transmission not in ["any", None] else None,
                fuel_type=session.preferences.fuel_type if session.preferences.fuel_type not in ["any", None] else None,
                seats=session.preferences.seating_capacity,
                seats_match_type=session.preferences.seating_match_type or "exact",
            )

            is_direct_query = any(q in text_lower for q in ["show me", "search for", "find me", "list all", "filter for"])

            preview_ranked = []
            a2ui_surfaces_list = []
            if preview_matches and (session.preferences.category or session.preferences.seating_capacity):
                preview_ranked = RankingEngine.rank_vehicles(preview_matches, session.preferences, limit=3)
                surface_id = f"surf_rec_{uuid.uuid4().hex[:6]}"
                rec_components = self._build_recommendations_a2ui_components(
                    preview_ranked, is_rent
                )
                a2ui_surfaces_list.append(surface_id)
                await self.emit_event(session_id, "a2ui", {
                    "type": "createSurface",
                    "surfaceId": surface_id,
                    "components": [c.model_dump() for c in rec_components]
                })

                bot_text = followup_text
            elif not preview_matches and (session.preferences.seating_capacity or session.preferences.category) and is_direct_query:
                # Direct search query with zero results: provide diagnostic explanation
                all_v = marketplace_repo.get_all_vehicles()
                diag = RankingEngine.diagnose_zero_results(all_v, session.preferences)
                diag_reasons = " ".join(diag["binding_constraints"])
                diag_sugg = " ".join(diag["recommended_relaxations"])

                bot_text = (
                    f"I checked our inventory for {session.preferences.seating_capacity or ''}-seater options within your criteria.\n\n"
                    f"**Inventory Note:** {diag_reasons}\n\n"
                    f"{diag_sugg}\n\n"
                    f"Would you like me to search for alternatives or adjust your criteria?"
                )
            else:
                bot_text = followup_text
                surface_id = f"surf_pref_{uuid.uuid4().hex[:6]}"
                a2ui_components = self._build_interview_a2ui_components(session.preferences, missing)
                a2ui_surfaces_list.append(surface_id)
                await self.emit_event(session_id, "a2ui", {
                    "type": "createSurface",
                    "surfaceId": surface_id,
                    "components": [c.model_dump() for c in a2ui_components]
                })

            structured_data = {
                "messageType": "INTERVIEW",
                "intent": session.preferences.intent.value if hasattr(session.preferences.intent, "value") else str(session.preferences.intent or "buy"),
                "title": f"Finding your {session.preferences.category.value if session.preferences.category else 'car'}",
                "summary": f"{session.preferences.category.value if session.preferences.category else 'Vehicle'} in {session.preferences.location or 'requested location'}",
                "message": bot_text,
                "collectedPreferences": session.preferences.model_dump(),
                "missingFields": missing,
                "nextStep": f"COLLECT_{missing[0].upper()}" if missing else "SEARCH",
                "actions": actions
            }

            bot_msg = ChatMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role=ChatRole.ASSISTANT,
                content=bot_text,
                a2ui_surfaces=a2ui_surfaces_list,
                data=structured_data
            )
            session_repo.add_message(session_id, bot_msg)
            session_repo.save_session(session)

            for act in actions:
                await self.emit_event(session_id, "website_action", act)

            return {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": a2ui_surfaces_list,
                "recommendations": [r.to_dict() for r in preview_ranked],
                "website_actions": actions,
                "structured_response": structured_data
            }

        # 5. Interview complete or requirement updated! Transition through SEARCHING and RANKING
        # Invalidate stale recommendations before performing a new search
        session.search_results = []
        session.selected_vehicle_id = None

        # Validate state transition: -> READY_TO_SEARCH -> SEARCHING
        if session.workflow_state in [WorkflowState.NEW, WorkflowState.INTERVIEWING]:
            StateMachine.validate_transition(session.workflow_state, WorkflowState.READY_TO_SEARCH)
            session.workflow_state = WorkflowState.READY_TO_SEARCH

        await self.emit_event(session_id, "progress", {
            "stage": "SEARCHING",
            "step": 3,
            "total_steps": 6,
            "message": f"Querying verified listings in {session.preferences.location or 'the market'}..."
        })

        StateMachine.validate_transition(session.workflow_state, WorkflowState.SEARCHING)
        session.workflow_state = WorkflowState.SEARCHING

        # Execute repository search
        is_rent = (session.preferences.intent == "RENT" or session.preferences.intent == IntentType.RENT)
        start_d = session.preferences.rental_details.pickup_date if (is_rent and session.preferences.rental_details) else None
        end_d = session.preferences.rental_details.return_date if (is_rent and session.preferences.rental_details) else None
        max_p = session.preferences.budget_max or (session.preferences.budget.amount if session.preferences.budget else None)
        min_p = session.preferences.budget_min
        trans = session.preferences.transmission if session.preferences.transmission not in ["any", None] else None
        fuel = session.preferences.fuel_type if session.preferences.fuel_type not in ["any", None] else None

        filtered_vehicles = marketplace_repo.search_vehicles(
            intent="rent" if is_rent else "buy",
            location=session.preferences.location,
            category=session.preferences.category.value if session.preferences.category else None,
            min_price=min_p,
            max_price=max_p,
            transmission=trans,
            fuel_type=fuel,
            seats=session.preferences.seating_capacity,
            seats_match_type=session.preferences.seating_match_type or "exact",
            brands=session.preferences.preferred_brands if session.preferences.preferred_brands else None,
            start_date=start_d,
            end_date=end_d
        )

        await self.emit_event(session_id, "progress", {
            "stage": "RANKING",
            "step": 4,
            "total_steps": 6,
            "message": f"Found {len(filtered_vehicles)} matching vehicles. Applying multi-criteria score weighting..."
        })

        StateMachine.validate_transition(session.workflow_state, WorkflowState.RANKING)
        session.workflow_state = WorkflowState.RANKING

        # Check for zero results
        if not filtered_vehicles:
            # Diagnose zero results
            all_v = marketplace_repo.get_all_vehicles()
            diag = RankingEngine.diagnose_zero_results(all_v, session.preferences)

            reasons_str = " ".join(diag["binding_constraints"])
            suggestions_str = " ".join(diag["recommended_relaxations"])
            bot_text = (
                f"I searched our inventory but couldn't find vehicles matching all strict requirements.\n\n"
                f"**Why no matches?**\n{reasons_str}\n\n"
                f"**Suggested adjustments:**\n{suggestions_str}\n\n"
                f"Would you like me to relax the budget or check other categories?"
            )

            surface_id = f"surf_zero_{uuid.uuid4().hex[:6]}"
            bot_msg = ChatMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role=ChatRole.ASSISTANT,
                content=bot_text,
                a2ui_surfaces=[surface_id]
            )
            StateMachine.validate_transition(session.workflow_state, WorkflowState.RECOMMENDATIONS_READY)
            session.workflow_state = WorkflowState.RECOMMENDATIONS_READY
            session_repo.add_message(session_id, bot_msg)
            session_repo.save_session(session)

            return {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": [surface_id],
                "recommendations": [],
                "diagnostics": diag
            }

        # Rank vehicles
        ranked_items = RankingEngine.rank_vehicles(filtered_vehicles, session.preferences, limit=5)

        # Recommendations Ready
        StateMachine.validate_transition(session.workflow_state, WorkflowState.RECOMMENDATIONS_READY)
        session.workflow_state = WorkflowState.RECOMMENDATIONS_READY
        session.search_results = [r.to_dict() for r in ranked_items]

        await self.emit_event(session_id, "progress", {
            "stage": "RECOMMENDATIONS_READY",
            "step": 5,
            "total_steps": 6,
            "message": f"Prepared {len(ranked_items)} personalized recommendations."
        })

        intent_word = "rental" if is_rent else "purchase"
        top_name = f"{ranked_items[0].vehicle.brand} {ranked_items[0].vehicle.model}"
        loc_str = f" in {session.preferences.location}" if session.preferences.location else ""
        bot_text = (
            f"I have found {len(ranked_items)} verified {intent_word} options for you{loc_str}. "
            f"My top recommendation is the **{top_name}** with a {ranked_items[0].match_score}% match score.\n\n"
            f"Review the options below and click **'Select'** to launch the booking details."
        )

        surface_id = f"surf_rec_{uuid.uuid4().hex[:6]}"
        rec_components = self._build_recommendations_a2ui_components(ranked_items, is_rent)

        structured_data = {
            "messageType": "VEHICLE_RECOMMENDATIONS",
            "intent": session.preferences.intent.value if hasattr(session.preferences.intent, "value") else str(session.preferences.intent or "buy"),
            "title": f"Verified {intent_word.capitalize()} Recommendations",
            "summary": f"{len(ranked_items)} options identified{loc_str}",
            "message": bot_text,
            "collectedPreferences": session.preferences.model_dump(),
            "missingFields": [],
            "nextStep": "VEHICLE_SELECTION",
            "actions": []
        }

        bot_msg = ChatMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            role=ChatRole.ASSISTANT,
            content=bot_text,
            a2ui_surfaces=[surface_id],
            data=structured_data
        )
        session_repo.add_message(session_id, bot_msg)
        session_repo.save_session(session)

        await self.emit_event(session_id, "a2ui", {
            "type": "createSurface",
            "surfaceId": surface_id,
            "components": [c.model_dump() for c in rec_components]
        })

        # Generate Website Actions to dynamically control the frontend
        target_path = "/rent" if is_rent else "/buy"
        filter_payload = {
            "intent": "rent" if is_rent else "buy",
            "category": session.preferences.category.value if session.preferences.category else "",
            "transmission": session.preferences.transmission if session.preferences.transmission not in ["any", None] else "",
            "location": session.preferences.location or "",
            "brand": session.preferences.preferred_brands[0] if session.preferences.preferred_brands else "",
            "fuelType": session.preferences.fuel_type if session.preferences.fuel_type not in ["any", None] else "",
        }
        if session.preferences.seating_capacity:
            filter_payload["seats"] = session.preferences.seating_capacity
        if max_p and max_p > 0:
            filter_payload["maxPrice"] = max_p
        if min_p and min_p > 0:
            filter_payload["minPrice"] = min_p

        website_actions = [
            {
                "type": "NAVIGATE_TO_PAGE",
                "payload": {"path": target_path}
            },
            {
                "type": "APPLY_FILTERS",
                "payload": filter_payload
            }
        ]

        for act in website_actions:
            await self.emit_event(session_id, "website_action", act)

        return {
            "message": bot_msg.model_dump(),
            "workflow_state": session.workflow_state.value,
            "preferences": session.preferences.model_dump(),
            "a2ui_surfaces": [surface_id],
            "recommendations": [r.to_dict() for r in ranked_items],
            "website_actions": website_actions
        }

    def _build_interview_a2ui_components(self, prefs: UserPreferences, missing: List[str]) -> List[A2UIComponent]:
        comps: List[A2UIComponent] = []
        root_children = []

        if "intent" in missing or not prefs.intent:
            root_children.append("intent_picker")
            comps.append(A2UIComponent(
                id="intent_picker",
                component="RadioGroup",
                properties={
                    "label": "What do you want to do?",
                    "options": [
                        {"label": "🛒 Buy a Car", "value": "BUY"},
                        {"label": "🔑 Rent a Car", "value": "RENT"},
                        {"label": "💰 Sell My Car", "value": "SELL"},
                    ],
                    "actionId": "update_intent",
                    "field": "intent"
                }
            ))

        if "category" in missing:
            root_children.append("cat_picker")
            comps.append(A2UIComponent(
                id="cat_picker",
                component="RadioGroup",
                properties={
                    "label": "Select Vehicle Category",
                    "options": [
                        {"label": "🚙 SUV", "value": "SUV"},
                        {"label": "🚗 Sedan", "value": "Sedan"},
                        {"label": "⚡ Electric Vehicle", "value": "Electric Vehicle"},
                        {"label": "🚘 Hatchback", "value": "Hatchback"},
                        {"label": "🏎️ Convertible", "value": "Convertible"},
                        {"label": "🚐 MUV", "value": "MUV"},
                    ],
                    "actionId": "update_category",
                    "field": "category"
                }
            ))

        if "location" in missing:
            root_children.append("loc_picker")
            comps.append(A2UIComponent(
                id="loc_picker",
                component="RadioGroup",
                properties={
                    "label": "Select Location",
                    "options": [
                        {"label": "🏙️ Delhi NCR", "value": "Delhi"},
                        {"label": "🌊 Mumbai", "value": "Mumbai"},
                        {"label": "🌿 Bangalore", "value": "Bangalore"},
                        {"label": "🌴 Hyderabad", "value": "Hyderabad"},
                        {"label": "🏖️ Chennai", "value": "Chennai"},
                    ],
                    "actionId": "update_location",
                    "field": "location"
                }
            ))

        if "fuel_type" in missing:
            root_children.append("fuel_picker")
            comps.append(A2UIComponent(
                id="fuel_picker",
                component="RadioGroup",
                properties={
                    "label": "Preferred Fuel Type",
                    "options": [
                        {"label": "⛽ Petrol", "value": "petrol"},
                        {"label": "🛢️ Diesel", "value": "diesel"},
                        {"label": "⚡ Electric", "value": "electric"},
                        {"label": "🌿 Hybrid", "value": "hybrid"},
                        {"label": "🔵 CNG", "value": "cng"},
                    ],
                    "actionId": "update_fuel",
                    "field": "fuel_type"
                }
            ))

        if "transmission" in missing:
            root_children.append("trans_picker")
            comps.append(A2UIComponent(
                id="trans_picker",
                component="RadioGroup",
                properties={
                    "label": "Transmission Preference",
                    "options": [
                        {"label": "🤖 Automatic", "value": "automatic"},
                        {"label": "🖐️ Manual", "value": "manual"},
                    ],
                    "actionId": "update_transmission",
                    "field": "transmission"
                }
            ))

        if root_children:
            comps.insert(0, A2UIComponent(
                id="root_interview_card",
                component="Card",
                properties={"variant": "glass", "title": "Quick Preferences"},
                children=root_children
            ))
        return comps

    def _build_recommendations_a2ui_components(self, items: List[Any], is_rent: bool) -> List[A2UIComponent]:
        comps: List[A2UIComponent] = []
        card_ids = []

        for idx, item in enumerate(items):
            card_id = f"rec_card_{idx}"
            card_ids.append(card_id)
            v = item.vehicle
            price_str = f"₹{v.rental_price_per_day:,.0f}/day" if is_rent else f"₹{v.purchase_price:,.0f}"

            comps.append(A2UIComponent(
                id=card_id,
                component="VehicleCard",
                properties={
                    "vehicleId": v.id,
                    "brand": v.brand,
                    "model": v.model,
                    "year": v.year,
                    "category": v.category.value,
                    "transmission": v.transmission.value,
                    "fuelType": v.fuel_type.value,
                    "seats": v.seats,
                    "priceDisplay": price_str,
                    "matchScore": item.match_score,
                    "scoreBreakdown": item.score_breakdown,
                    "positiveMatches": item.positive_matches,
                    "tradeOffs": item.trade_offs,
                    "explanation": item.explanation,
                    "imageUrl": v.image_url,
                    "actionId": "select_vehicle",
                    "actionData": {"vehicle_id": v.id}
                }
            ))

        comps.insert(0, A2UIComponent(
            id="rec_grid",
            component="Grid",
            properties={"columns": 1, "gap": "md"},
            children=card_ids
        ))
        return comps

orchestration_engine = OrchestrationEngine()

