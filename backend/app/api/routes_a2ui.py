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

        # Trigger MCP App event
        raw_intent = session.preferences.intent
        intent_str = raw_intent.value.lower() if hasattr(raw_intent, "value") else str(raw_intent or "buy").lower()
        is_rent = (intent_str == "rent")
        app_name = "booking"

        action_msg = ChatMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            role=ChatRole.ASSISTANT,
            content=(
                f"You selected the **{vehicle.year} {vehicle.brand} {vehicle.model}**! "
                f"I've opened the interactive booking portal below inside this conversation."
            ),
            mcp_app="booking",
            data={
                "vehicle": vehicle.model_dump(),
                "intent": intent_str,
                "preferences": session.preferences.model_dump()
            }
        )
        session_repo.add_message(payload.session_id, action_msg)
        session_repo.save_session(session)

        await orchestration_engine.emit_event(payload.session_id, "mcp_trigger", {
            "app": "booking",
            "uri": "ui://booking-form",
            "vehicle_id": vehicle_id,
            "intent": intent_str
        })

        return {
            "status": "success",
            "workflow_state": session.workflow_state.value,
            "message": action_msg.model_dump(),
            "selected_vehicle": vehicle.model_dump()
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

