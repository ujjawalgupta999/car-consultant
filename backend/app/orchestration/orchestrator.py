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

        # Check for Comparison Request: "compare", "compare the first two", "compare the two best options"
        text_lower = user_content.lower()
        if "compare" in text_lower:
            # Pick first 2 search results or first 2 matching vehicles
            compared_ids = []
            if session.search_results and len(session.search_results) >= 2:
                compared_ids = [session.search_results[0]["vehicle"]["id"], session.search_results[1]["vehicle"]["id"]]
            else:
                all_v = marketplace_repo.get_all_vehicles()
                compared_ids = [all_v[0].id, all_v[1].id]

            comp_v1 = marketplace_repo.get_vehicle_by_id(compared_ids[0])
            comp_v2 = marketplace_repo.get_vehicle_by_id(compared_ids[1])
            v1_name = f"{comp_v1.brand} {comp_v1.model}" if comp_v1 else "Vehicle 1"
            v2_name = f"{comp_v2.brand} {comp_v2.model}" if comp_v2 else "Vehicle 2"

            bot_text = (
                f"I've added the **{v1_name}** and **{v2_name}** to your comparison matrix "
                f"and navigated you to the **Compare Cars** page. Review their side-by-side specs, safety, and price value below."
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
            # Need more details: stay in INTERVIEWING
            if session.workflow_state == WorkflowState.NEW:
                StateMachine.validate_transition(session.workflow_state, WorkflowState.INTERVIEWING)
                session.workflow_state = WorkflowState.INTERVIEWING

            followup_text = AdaptiveInterviewAgent.generate_followup_question(session.preferences)
            if extracted_fields:
                ack = f"Got it: {', '.join(extracted_fields)}. "
                bot_text = ack + followup_text
            else:
                bot_text = followup_text

            # Create A2UI Surface for missing preferences
            surface_id = f"surf_pref_{uuid.uuid4().hex[:6]}"
            a2ui_components = self._build_interview_a2ui_components(session.preferences, missing)

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
                "components": [c.model_dump() for c in a2ui_components]
            })

            return {
                "message": bot_msg.model_dump(),
                "workflow_state": session.workflow_state.value,
                "preferences": session.preferences.model_dump(),
                "a2ui_surfaces": [surface_id],
                "recommendations": []
            }

        # 5. Interview complete! Transition through SEARCHING and RANKING
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
        is_rent = (session.preferences.intent == IntentType.RENT)
        start_d = session.preferences.rental_details.pickup_date if (is_rent and session.preferences.rental_details) else None
        end_d = session.preferences.rental_details.return_date if (is_rent and session.preferences.rental_details) else None
        max_p = session.preferences.budget.amount if session.preferences.budget else None

        filtered_vehicles = marketplace_repo.search_vehicles(
            intent=session.preferences.intent.value,
            location=session.preferences.location,
            category=session.preferences.category.value if session.preferences.category else None,
            max_price=max_p,
            transmission=session.preferences.transmission,
            fuel_type=session.preferences.fuel_type,
            seats=session.preferences.seating_capacity,
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
        bot_text = (
            f"I have found {len(ranked_items)} verified {intent_word} options for you in {session.preferences.location}. "
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
        website_actions = [
            {
                "type": "NAVIGATE_TO_PAGE",
                "payload": {"path": target_path}
            },
            {
                "type": "APPLY_FILTERS",
                "payload": {
                    "category": session.preferences.category.value if session.preferences.category else "",
                    "transmission": session.preferences.transmission or "",
                    "location": session.preferences.location or "",
                    "maxPrice": max_p,
                    "intent": "rent" if is_rent else "buy"
                }
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

