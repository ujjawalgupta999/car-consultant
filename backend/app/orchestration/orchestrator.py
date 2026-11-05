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
from ..repositories.marketplace import marketplace_repo
from ..repositories.session import session_repo
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

        # 3. Adaptive Interview Preference Extraction
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

            # Build website filter payload
            filter_payload = {
                "intent": "rent" if is_rent else "buy",
                "category": session.preferences.category.value if session.preferences.category else "",
                "transmission": session.preferences.transmission if session.preferences.transmission not in ["any", None] else "",
                "location": session.preferences.location or "",
                "brand": session.preferences.preferred_brands[0] if session.preferences.preferred_brands else "",
            }
            if session.preferences.seating_capacity:
                filter_payload["seats"] = session.preferences.seating_capacity
            if session.preferences.budget_max and session.preferences.budget_max > 0:
                filter_payload["maxPrice"] = session.preferences.budget_max
            elif session.preferences.budget and session.preferences.budget.amount > 0:
                filter_payload["maxPrice"] = session.preferences.budget.amount
            if session.preferences.budget_min and session.preferences.budget_min > 0:
                filter_payload["minPrice"] = session.preferences.budget_min

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

                if session.preferences.seating_capacity and not session.preferences.category:
                    bot_text = followup_text
                else:
                    if session.preferences.seating_capacity:
                        words = {2: "two-seater", 3: "three-seater", 4: "four-seater", 5: "five-seater", 7: "seven-seater"}
                        seat_word = words.get(session.preferences.seating_capacity, f"{session.preferences.seating_capacity}-seater")
                        cat_label = f"**{seat_word}** {session.preferences.category.value if session.preferences.category else 'vehicles'}"
                    else:
                        cat_label = f"**{session.preferences.category.value}s**"

                    bot_text = (
                        f"I've updated the website to navigate to our **{portal_label}** portal and filtered our catalogue for {cat_label} ({len(preview_matches)} models found)!\n\n"
                        f"{followup_text}"
                    )
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

                bot_text = followup_text

            bot_msg = ChatMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role=ChatRole.ASSISTANT,
                content=bot_text,
                a2ui_surfaces=a2ui_surfaces_list
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
                "website_actions": actions
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

        bot_msg = ChatMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            role=ChatRole.ASSISTANT,
            content=bot_text,
            a2ui_surfaces=[surface_id]
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
                        {"label": "🏎️ Convertible", "value": "Convertible"}
                    ],
                    "actionId": "update_category"
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
                        {"label": "Delhi NCR", "value": "Delhi"},
                        {"label": "Mumbai", "value": "Mumbai"},
                        {"label": "Bangalore", "value": "Bangalore"}
                    ],
                    "actionId": "update_location"
                }
            ))

        comps.insert(0, A2UIComponent(
            id="root_interview_card",
            component="Card",
            properties={"variant": "glass", "title": "Quick Preferences Form"},
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

