from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from ..models.a2ui import A2UIActionPayload
from ..models.session import WorkflowState, ChatMessage, ChatRole
from ..repositories.session import session_repo
from ..repositories.marketplace import marketplace_repo
from ..orchestration.orchestrator import orchestration_engine
from ..orchestration.state_machine import StateMachine
import uuid

router = APIRouter(prefix="/api/a2ui", tags=["A2UI Actions"])

@router.post("/action")
async def handle_a2ui_action(payload: A2UIActionPayload):
    session = session_repo.get_or_create_session(payload.session_id)

    if payload.action_id == "select_vehicle":
        vehicle_id = payload.data.get("vehicle_id")
        if not vehicle_id:
            raise HTTPException(status_code=400, detail="vehicle_id required")

        vehicle = marketplace_repo.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")

        # Validate state transition
        StateMachine.validate_transition(session.workflow_state, WorkflowState.VEHICLE_SELECTED)
        session.workflow_state = WorkflowState.VEHICLE_SELECTED
        session.selected_vehicle_id = vehicle_id

        # Update session state
        raw_intent = session.preferences.intent
        intent_str = raw_intent.value.lower() if hasattr(raw_intent, "value") else str(raw_intent or "buy").lower()
        is_rent = (intent_str == "rent")

        order_id = f"BK-2026-{uuid.uuid4().hex[:6].upper()}" if is_rent else f"ORD-2026-{uuid.uuid4().hex[:6].upper()}"
        daily_rate = vehicle.rental_price_per_day or 3500.0
        amount = round(daily_rate * 5 * 1.18 + 5000.0) if is_rent else 25000.0
        target_path = f"/booking/{vehicle.id}" if is_rent else f"/checkout/{order_id}"

        prefill_payload = {
            "customerName": "Alex Vance",
            "customerEmail": "demo@auramotors.com",
            "customerPhone": "+91 98765 43210",
            "deliveryCity": session.preferences.location or vehicle.location or "Delhi NCR",
            "pickupLocation": vehicle.location or "Delhi NCR",
            "pickupDate": "2026-12-15",
            "returnDate": "2026-12-20",
            "durationDays": 5,
            "paymentMethod": "upi",
            "upiId": "alex@okaxis",
            "vehicleId": vehicle.id,
            "amount": amount,
            "orderId": order_id
        }

        session.active_order_id = order_id
        session.pending_question = "PROCEED_TO_PAYMENT"
        session.workflow_data["pending_checkout"] = {
            "order_id": order_id,
            "vehicle_id": vehicle.id,
            "amount": amount,
            "is_rent": is_rent,
            "payment_method": "UPI",
            "upi_id": "alex@okaxis",
            "customer_name": "Alex Vance"
        }

        actions = [
            {"type": "NAVIGATE_TO_PAGE", "payload": {"path": target_path}},
            {"type": "NAVIGATE", "payload": {"path": target_path}},
            {"type": "PREFILL_CHECKOUT_FORM", "payload": prefill_payload}
        ]

        action_msg = ChatMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            role=ChatRole.ASSISTANT,
            content=(
                f"I have selected the **{vehicle.year} {vehicle.brand} {vehicle.model}** and opened the reservation page in the background.\n\n"
                f"I've filled in your verified details on the background booking form:\n"
                f"- **Vehicle:** {vehicle.brand} {vehicle.model} ({vehicle.year})\n"
                f"- **Location:** {prefill_payload['deliveryCity']}\n"
                f"- **Dates:** Dec 15 to Dec 20, 2026 (5 Days)\n"
                f"- **Customer:** Alex Vance (+91 98765 43210)\n"
                f"- **Estimated Total:** ₹{amount:,.0f}\n\n"
                f"All fields have been filled on the background page. Would you like me to proceed to payment?"
            ),
            data={
                "vehicle": vehicle.model_dump(),
                "intent": intent_str,
                "preferences": session.preferences.model_dump(),
                "actions": actions
            }
        )
        session_repo.add_message(payload.session_id, action_msg)
        session_repo.save_session(session)

        for act in actions:
            await orchestration_engine.emit_event(payload.session_id, "website_action", act)

        return {
            "status": "success",
            "workflow_state": session.workflow_state.value,
            "message": action_msg.model_dump(),
            "selected_vehicle": vehicle.model_dump(),
            "website_actions": actions,
            "actions": actions
        }

    elif payload.action_id == "update_category":
        cat = payload.data.get("category")
        if cat:
            from ..models.vehicle import VehicleCategory
            try:
                session.preferences.category = VehicleCategory(cat)
            except ValueError:
                pass
            session_repo.save_session(session)
            return await orchestration_engine.process_user_turn(
                payload.session_id, f"I prefer the {cat} category."
            )

    elif payload.action_id == "update_location":
        loc = payload.data.get("location")
        if loc:
            session.preferences.location = loc
            session_repo.save_session(session)
            return await orchestration_engine.process_user_turn(
                payload.session_id, f"My location is {loc}."
            )

    elif payload.action_id == "update_fuel":
        fuel = payload.data.get("fuel_type")
        if fuel:
            session.preferences.fuel_type = fuel.lower()
            session_repo.save_session(session)
            return await orchestration_engine.process_user_turn(
                payload.session_id, f"I want {fuel} fuel type."
            )

    elif payload.action_id == "update_transmission":
        trans = payload.data.get("transmission")
        if trans:
            session.preferences.transmission = trans.lower()
            session_repo.save_session(session)
            return await orchestration_engine.process_user_turn(
                payload.session_id, f"I prefer {trans} transmission."
            )

    elif payload.action_id == "update_intent":
        intent_val = payload.data.get("intent")
        if intent_val:
            from ..models.preferences import IntentType
            try:
                session.preferences.intent = IntentType(intent_val.upper())
            except ValueError:
                pass
            session_repo.save_session(session)
            return await orchestration_engine.process_user_turn(
                payload.session_id, f"I want to {intent_val.lower()} a car."
            )

    elif payload.action_id == "update_preference":
        # Generic preference update: handles any field=value pair
        field = payload.data.get("field")
        value = payload.data.get("value")
        if field and value is not None:
            if field == "category":
                from ..models.vehicle import VehicleCategory
                try:
                    session.preferences.category = VehicleCategory(value)
                except ValueError:
                    pass
            elif field == "location":
                session.preferences.location = str(value)
            elif field == "fuel_type":
                session.preferences.fuel_type = str(value).lower()
            elif field == "transmission":
                session.preferences.transmission = str(value).lower()
            elif field == "intent":
                from ..models.preferences import IntentType
                try:
                    session.preferences.intent = IntentType(str(value).upper())
                except ValueError:
                    pass
            session_repo.save_session(session)
            return await orchestration_engine.process_user_turn(
                payload.session_id, f"Update {field} to {value}."
            )

    return {"status": "unhandled_action", "action_id": payload.action_id}

