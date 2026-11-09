import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path

from .config import settings
from .orchestration.state_machine import InvalidStateTransitionError
from .api import (
    routes_health,
    routes_sessions,
    routes_vehicles,
    routes_bookings,
    routes_payments,
    routes_a2ui,
    routes_auth,
    routes_purchases,
    routes_dashboard,
    routes_listings,
    routes_rentals,
    routes_checkout,
    routes_db
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("car_consultant")

from contextlib import asynccontextmanager
from .db.mongodb import mongodb_manager
from .db.transfer_to_mongo import transfer_all_data_to_mongodb
from .observability.langfuse_client import langfuse_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} in '{settings.environment}' mode.")
    logger.info(f"Agent mode: '{settings.agent_mode}' | Storage: '{settings.storage_backend}'")
    
    # 1. Connect MongoDB & auto-transfer data if live
    if mongodb_manager.connect():
        logger.info("MongoDB connection active. Transferring/synchronizing catalog and user data...")
        transfer_all_data_to_mongodb(force=False)
    else:
        logger.info("MongoDB offline or placeholder username present; operating in high-performance memory/JSON mode.")

    # 2. Log Observability status
    if settings.is_openai_enabled:
        logger.info(f"OpenAI GPT-4o engine enabled. Model: {settings.openai_model}")
    if settings.is_langfuse_enabled:
        logger.info(f"Langfuse observability enabled. Host: {settings.effective_langfuse_host}")

    yield

    # Teardown
    mongodb_manager.disconnect()
    langfuse_manager.flush()

app = FastAPI(
    title=settings.app_name,
    description="Backend API for Amulate Summer Hackathon 2026: AI-Powered Car Rental & Purchase Consultant",
    version="1.0.0",
    lifespan=lifespan
)

@app.exception_handler(InvalidStateTransitionError)
async def invalid_state_transition_handler(request: Request, exc: InvalidStateTransitionError):
    logger.warning(f"Invalid state transition caught gracefully: {exc}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "invalid_state_transition",
            "message": str(exc),
            "current_state": exc.current_state.value if hasattr(exc, "current_state") else str(exc.current_state),
            "target_state": exc.target_state.value if hasattr(exc, "target_state") else str(exc.target_state),
        }
    )

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow development and sandboxed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(routes_health.router)
app.include_router(routes_sessions.router)
app.include_router(routes_vehicles.router)
app.include_router(routes_bookings.router)
app.include_router(routes_payments.router)
app.include_router(routes_a2ui.router)
app.include_router(routes_auth.router)
app.include_router(routes_purchases.router)
app.include_router(routes_dashboard.router)
app.include_router(routes_listings.router)
app.include_router(routes_rentals.router)
app.include_router(routes_checkout.router)
app.include_router(routes_db.router)

# Mount MCP Apps static directory if it exists
mcp_apps_dir = Path(__file__).parent.parent.parent / "mcp-apps"
if mcp_apps_dir.exists():
    app.mount("/mcp-apps", StaticFiles(directory=str(mcp_apps_dir)), name="mcp-apps")


