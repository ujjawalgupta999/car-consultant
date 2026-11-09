from fastapi import APIRouter
from datetime import datetime
from ..config import settings
from ..repositories.marketplace import marketplace_repo
from ..db.mongodb import mongodb_manager

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    all_v = marketplace_repo.get_all_vehicles()
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "environment": settings.environment,
        "agent_mode": settings.agent_mode,
        "storage_backend": "mongodb" if mongodb_manager.is_connected() else "json_marketplace",
        "total_listings": len(all_v),
        "categories_supported": 10,
        "mongodb": mongodb_manager.get_status(),
        "openai": {
            "enabled": settings.is_openai_enabled,
            "model": settings.openai_model
        },
        "langfuse": {
            "enabled": settings.is_langfuse_enabled,
            "host": settings.effective_langfuse_host
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

