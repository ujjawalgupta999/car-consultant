import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..db.mongodb import mongodb_manager
from ..db.transfer_to_mongo import transfer_all_data_to_mongodb
from ..config import settings
from ..observability.langfuse_client import langfuse_manager

router = APIRouter(prefix="/api/db", tags=["Database & Migration"])
logger = logging.getLogger("car_consultant.api.db")

@router.get("/status")
def get_db_status() -> Dict[str, Any]:
    """Returns live connection and health status of MongoDB, OpenAI, and Langfuse."""
    mongo_status = mongodb_manager.get_status()
    db = mongodb_manager.get_database()
    counts = {}
    if db is not None:
        try:
            for coll in ["vehicles", "owned_vehicles", "purchase_orders", "payment_transactions", "selling_listings", "saved_vehicles", "user_profiles"]:
                counts[coll] = db[coll].count_documents({})
        except Exception:
            pass

    return {
        "mongodb": {
            **mongo_status,
            "counts": counts,
        },
        "openai": {
            "enabled": settings.is_openai_enabled,
            "model": settings.openai_model,
        },
        "langfuse": {
            "enabled": settings.is_langfuse_enabled,
            "host": settings.effective_langfuse_host
        }
    }

@router.post("/transfer")
def transfer_data() -> Dict[str, Any]:
    """Triggers migration of all vehicle and user data into MongoDB."""
    result = transfer_all_data_to_mongodb(force=True)
    if not result.get("success"):
        return {
            "status": "error",
            "message": result.get("error", "Data transfer failed"),
            "details": result
        }
    return {
        "status": "success",
        "message": "All data transferred to MongoDB successfully",
        "result": result
    }

