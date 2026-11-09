import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import pymongo

from .mongodb import mongodb_manager
from ..config import settings

logger = logging.getLogger("car_consultant.db.transfer")

def transfer_all_data_to_mongodb(force: bool = False) -> Dict[str, Any]:
    """
    Transfers vehicles dataset and user data portfolio into MongoDB.
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
        "owned_vehicles": 0,
        "purchase_orders": 0,
        "payment_transactions": 0,
        "selling_listings": 0,
        "saved_vehicles": 0,
        "user_profiles": 0
    }

    try:
        # 1. Create indexes
        db.vehicles.create_index([("id", pymongo.ASCENDING)], unique=True)
        db.vehicles.create_index([("category", pymongo.ASCENDING)])
        db.vehicles.create_index([("brand", pymongo.ASCENDING)])
        db.vehicles.create_index([("purchase_price", pymongo.ASCENDING)])

        db.owned_vehicles.create_index([("id", pymongo.ASCENDING)], unique=True)
        db.owned_vehicles.create_index([("userId", pymongo.ASCENDING)])

        db.purchase_orders.create_index([("id", pymongo.ASCENDING)], unique=True)
        db.purchase_orders.create_index([("userId", pymongo.ASCENDING)])
        db.purchase_orders.create_index([("orderId", pymongo.ASCENDING)])

        db.payment_transactions.create_index([("id", pymongo.ASCENDING)], unique=True)
        db.payment_transactions.create_index([("transactionId", pymongo.ASCENDING)], unique=True)
        db.payment_transactions.create_index([("userId", pymongo.ASCENDING)])

        db.selling_listings.create_index([("id", pymongo.ASCENDING)], unique=True)
        db.selling_listings.create_index([("userId", pymongo.ASCENDING)])

        db.user_profiles.create_index([("id", pymongo.ASCENDING)], unique=True)

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
            logger.info(f"Successfully migrated {len(vehicles_data)} vehicles to MongoDB 'vehicles' collection.")

        # 3. Transfer User Demo Portfolio from UserDataRepository
        from ..repositories.user_data_repo import user_data_repo

        # User Profile
        demo_user = user_data_repo.get_profile()
        if demo_user:
            user_doc = demo_user.model_dump()
            db.user_profiles.update_one(
                {"id": user_doc["id"]},
                {"$set": user_doc},
                upsert=True
            )
            counts["user_profiles"] = db.user_profiles.count_documents({})

        # Owned Vehicles (Digital Garage)
        for ov in user_data_repo.get_all_owned_vehicles():
            doc = ov.model_dump()
            db.owned_vehicles.update_one(
                {"id": doc["id"]},
                {"$set": doc},
                upsert=True
            )
        counts["owned_vehicles"] = db.owned_vehicles.count_documents({})

        # Purchase Orders
        for po in user_data_repo.get_all_purchases():
            doc = po.model_dump()
            db.purchase_orders.update_one(
                {"id": doc["id"]},
                {"$set": doc},
                upsert=True
            )
        counts["purchase_orders"] = db.purchase_orders.count_documents({})

        # Payment Transactions
        for pt in user_data_repo.get_all_payments():
            doc = pt.model_dump()
            db.payment_transactions.update_one(
                {"id": doc["id"]},
                {"$set": doc},
                upsert=True
            )
        counts["payment_transactions"] = db.payment_transactions.count_documents({})

        # Selling Listings
        for sl in user_data_repo.get_all_selling_listings():
            doc = sl.model_dump()
            db.selling_listings.update_one(
                {"id": doc["id"]},
                {"$set": doc},
                upsert=True
            )
        counts["selling_listings"] = db.selling_listings.count_documents({})

        # Saved Vehicles
        for sv_id in user_data_repo.get_saved_vehicle_ids():
            db.saved_vehicles.update_one(
                {"userId": demo_user.id if demo_user else "usr_demo_01", "vehicleId": sv_id},
                {"$set": {"userId": demo_user.id if demo_user else "usr_demo_01", "vehicleId": sv_id}},
                upsert=True
            )
        counts["saved_vehicles"] = db.saved_vehicles.count_documents({})

        logger.info(f"MongoDB Data Transfer Complete: {counts}")
        return {
            "success": True,
            "database": db.name,
            "counts": counts,
            "message": "All vehicles and user data successfully synchronized to MongoDB."
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

