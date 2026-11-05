import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import settings
from .api import (
    routes_health,
    routes_sessions,
    routes_vehicles,
    routes_bookings,
    routes_payments,
    routes_a2ui,
    routes_auth
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("car_consultant")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} in '{settings.environment}' mode.")
    logger.info(f"Agent mode: '{settings.agent_mode}' | Storage: '{settings.storage_backend}'")
    yield

app = FastAPI(
    title=settings.app_name,
    description="Backend API for Amulate Summer Hackathon 2026: AI-Powered Car Rental & Purchase Consultant",
    version="1.0.0",
    lifespan=lifespan
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

# Mount MCP Apps static directory if it exists
mcp_apps_dir = Path(__file__).parent.parent.parent / "mcp-apps"
if mcp_apps_dir.exists():
    app.mount("/mcp-apps", StaticFiles(directory=str(mcp_apps_dir)), name="mcp-apps")


