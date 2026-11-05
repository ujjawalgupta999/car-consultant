from fastapi import APIRouter
from datetime import datetime
from ..config import settings
from ..repositories.marketplace import marketplace_repo

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    all_v = marketplace_repo.get_all_vehicles()
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "environment": settings.environment,
        "agent_mode": settings.agent_mode,
        "storage_backend": "json_marketplace",
        "total_listings": len(all_v),
        "categories_supported": 10,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

