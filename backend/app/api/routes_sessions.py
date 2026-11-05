import json
import asyncio
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging
from ..orchestration.state_machine import InvalidStateTransitionError

logger = logging.getLogger("car_consultant.sessions")
from ..repositories.session import session_repo
from ..orchestration.orchestrator import orchestration_engine
from ..models.session import Session, WorkflowState
from ..models.preferences import UserPreferences

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])

class CreateSessionRequest(BaseModel):
    user_id: Optional[str] = None

class SendMessageRequest(BaseModel):
    content: str

class UpdatePreferencesRequest(BaseModel):
    intent: Optional[str] = None
    location: Optional[str] = None
    category: Optional[str] = None
    budget_amount: Optional[float] = None
    transmission: Optional[str] = None
    fuel_type: Optional[str] = None
    rental_duration_days: Optional[int] = None
    pickup_date: Optional[str] = None

@router.post("", status_code=201)
def create_session(req: Optional[CreateSessionRequest] = None):
    session = session_repo.get_or_create_session()
    return {
        "session_id": session.session_id,
        "workflow_state": session.workflow_state.value,
        "preferences": session.preferences.model_dump(),
        "created_at": session.created_at
    }

@router.get("/{session_id}")
def get_session(session_id: str):
    session = session_repo.get_session(session_id)
    if not session:
        # Create it so user can seamlessly resume
        session = session_repo.get_or_create_session(session_id)
    messages = session_repo.get_messages(session_id)
    return {
        "session": session.model_dump(),
        "messages": [m.model_dump() for m in messages]
    }

@router.delete("/{session_id}")
def delete_session(session_id: str):
    # Reset session
    session = session_repo.get_or_create_session(session_id)
    session.workflow_state = WorkflowState.NEW
    session.preferences = UserPreferences(session_id=session_id)
    session.search_results = []
    session.selected_vehicle_id = None
    session_repo.save_session(session)
    return {"status": "reset", "session_id": session_id}

@router.post("/{session_id}/messages")
async def send_message(session_id: str, req: SendMessageRequest):
    if not req.content or not req.content.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")
    try:
        result = await orchestration_engine.process_user_turn(session_id, req.content.strip())
        return result
    except InvalidStateTransitionError as exc:
        logger.warning(f"Invalid state transition in session {session_id}: {exc}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_state_transition",
                "message": str(exc),
                "current_state": exc.current_state.value if hasattr(exc, "current_state") else str(exc.current_state),
                "target_state": exc.target_state.value if hasattr(exc, "target_state") else str(exc.target_state),
            }
        )

@router.get("/{session_id}/events")
async def sse_events(session_id: str):
    queue = orchestration_engine.subscribe_events(session_id)

    async def event_generator():
        try:
            # Send initial keepalive/ping
            yield f": ping\n\n"
            while True:
                # Wait for next event or send keepalive every 15 seconds
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    evt_name = payload.get("event", "message")
                    data_str = payload.get("data", "{}")
                    yield f"event: {evt_name}\ndata: {data_str}\n\n"
                except asyncio.TimeoutError:
                    yield f": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            orchestration_engine.unsubscribe_events(session_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.patch("/{session_id}/preferences")
def update_preferences(session_id: str, req: UpdatePreferencesRequest):
    session = session_repo.get_or_create_session(session_id)
    prefs = session.preferences
    if req.intent:
        from ..models.preferences import IntentType
        prefs.intent = IntentType(req.intent.lower())
    if req.location:
        prefs.location = req.location
    if req.category:
        from ..models.vehicle import VehicleCategory
        prefs.category = VehicleCategory(req.category)
    if req.budget_amount:
        from ..models.preferences import Budget, BudgetPeriod
        prefs.budget = Budget(amount=req.budget_amount, currency="INR", period=BudgetPeriod.PER_DAY)
    if req.transmission:
        prefs.transmission = req.transmission
    if req.fuel_type:
        prefs.fuel_type = req.fuel_type
    if req.rental_duration_days and prefs.rental_details:
        prefs.rental_details.rental_duration_days = req.rental_duration_days
    if req.pickup_date and prefs.rental_details:
        prefs.rental_details.pickup_date = req.pickup_date

    session.preferences = prefs
    session_repo.save_session(session)
    return {"status": "updated", "preferences": session.preferences.model_dump()}

