import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import pymongo

from .mongodb import mongodb_manager
from ..config import settings

logger = logging.getLogger("car_consultant.db.transfer")

def transfer_all_data_to_mongodb(force: bool = False) -> Dict[str, Any]:
    """
    Transfers vehicles dataset and user data portfolio into MongoDB Atlas.
    Uses upsert operations so it is completely safe, idempotent, and non-destructive.
    """
    if not mongodb_manager.is_connected():
        connected = mongodb_manager.connect()
        if not connected:
            status = mongodb_manager.get_status()
            logger.warning(f"Cannot transfer data to MongoDB: {status.get('last_error')}")
            return {
                "success": False,
                "error": status.get("last_error") or "Failed to connect to MongoDB",
                "counts": {}
            }

    db = mongodb_manager.get_database()
    if db is None:
        return {"success": False, "error": "Database handle unavailable", "counts": {}}

    counts = {
        "vehicles": 0,
        "users": 0,
        "purchases": 0,
        "payments": 0,
        "selling_listings": 0
    }

    try:
        # 1. Create indexes
        db.users.create_index([("id", pymongo.ASCENDING)], unique=True)
        db.users.create_index([("email", pymongo.ASCENDING)], unique=True)

        db.vehicles.create_index([("id", pymongo.ASCENDING)], unique=True)
        db.vehicles.create_index([("category", pymongo.ASCENDING)])
        db.vehicles.create_index([("brand", pymongo.ASCENDING)])
        db.vehicles.create_index([("purchase_price", pymongo.ASCENDING)])

        db.purchases.create_index([("id", pymongo.ASCENDING)], unique=True)
        db.purchases.create_index([("userId", pymongo.ASCENDING)])
        db.purchases.create_index([("orderId", pymongo.ASCENDING)])

        db.orders.create_index([("id", pymongo.ASCENDING)], unique=True)
        db.orders.create_index([("orderId", pymongo.ASCENDING)])
        db.orders.create_index([("userId", pymongo.ASCENDING)])

        db.payments.create_index([("id", pymongo.ASCENDING)], unique=True)
        db.payments.create_index([("transactionId", pymongo.ASCENDING)], unique=True)
        db.payments.create_index([("userId", pymongo.ASCENDING)])
        db.payments.create_index([("orderId", pymongo.ASCENDING)])

        db.selling_listings.create_index([("id", pymongo.ASCENDING)], unique=True)
        db.selling_listings.create_index([("userId", pymongo.ASCENDING)])

        # 2. Transfer Vehicles from vehicles.json
        vehicles_path = Path(__file__).parent.parent.parent / "data" / "vehicles.json"
        if vehicles_path.exists():
            with open(vehicles_path, "r", encoding="utf-8") as f:
                vehicles_data: List[Dict[str, Any]] = json.load(f)

            for v in vehicles_data:
                db.vehicles.update_one(
                    {"id": v["id"]},
                    {"$set": v},
                    upsert=True
                )
            counts["vehicles"] = db.vehicles.count_documents({})
            logger.info(f"Successfully migrated {len(vehicles_data)} vehicles to MongoDB Atlas 'vehicles' collection.")

        # 3. Transfer Users into 'users' collection
        demo_user_doc = {
            "id": "usr_demo_01",
            "name": "Alex Vance",
            "email": "demo@auramotors.com",
            "phone": "+91 98765 43210",
            "password_hash": hashlib.sha256("Password123!".encode()).hexdigest(),
            "saved_vehicles": ["CAR-001", "CAR-021"],
            "created_at": "2026-11-01T10:00:00Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        db.users.update_one({"email": demo_user_doc["email"]}, {"$set": demo_user_doc}, upsert=True)
        counts["users"] = db.users.count_documents({})

        # 4. Transfer Purchases from repository
        from ..repositories.user_data_repo import user_data_repo
        for po in user_data_repo.get_all_purchases():
            doc = po.model_dump() if hasattr(po, "model_dump") else dict(po)
            db.purchases.update_one(
                {"id": doc["id"]},
                {"$set": doc},
                upsert=True
            )
        counts["purchases"] = db.purchases.count_documents({})

        # 5. Transfer Payments
        for pt in user_data_repo.get_all_payments():
            doc = pt.model_dump() if hasattr(pt, "model_dump") else dict(pt)
            db.payments.update_one(
                {"id": doc["id"]},
                {"$set": doc},
                upsert=True
            )
        counts["payments"] = db.payments.count_documents({})

        # 6. Transfer Selling Listings
        for sl in user_data_repo.get_all_selling_listings():
            doc = sl.model_dump() if hasattr(sl, "model_dump") else dict(sl)
            db.selling_listings.update_one(
                {"id": doc["id"]},
                {"$set": doc},
                upsert=True
            )
        counts["selling_listings"] = db.selling_listings.count_documents({})

        logger.info(f"MongoDB Data Transfer Complete: {counts}")
        return {
            "success": True,
            "database": db.name,
            "counts": counts,
            "message": "All vehicles and user data successfully synchronized to MongoDB Atlas."
        }
    except Exception as e:
        logger.error(f"Error during MongoDB data transfer: {e}")
        return {
            "success": False,
            "error": str(e),
            "counts": counts
        }

if __name__ == "__main__":
    import sys
    print("Initiating MongoDB Data Transfer...")
    result = transfer_all_data_to_mongodb(force=True)
    print(json.dumps(result, indent=2))
