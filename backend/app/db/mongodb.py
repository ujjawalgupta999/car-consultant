import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import pymongo
from pymongo.database import Database
from pymongo import MongoClient

from ..config import settings

logger = logging.getLogger("car_consultant.db")

class MongoDBManager:
    _instance: Optional["MongoDBManager"] = None

    def __init__(self):
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None
        self._is_connected: bool = False
        self._last_error: Optional[str] = None
        self._connect_attempted: bool = False

    @classmethod
    def get_instance(cls) -> "MongoDBManager":
        if cls._instance is None:
            cls._instance = MongoDBManager()
        return cls._instance

    def is_connected(self) -> bool:
        return self._is_connected and self._client is not None

    def get_database(self) -> Optional[Database]:
        if not self._is_connected and not self._connect_attempted:
            self.connect()
        return self._db

    def get_collection(self, name: str):
        db = self.get_database()
        if db is not None:
            return db[name]
        return None

    def connect(self, force: bool = False) -> bool:
        """
        Attempts to connect to MongoDB using settings.mongodb_uri.
        Handles placeholders cleanly so app never crashes if credentials need updating.
        """
        if self._is_connected and not force:
            return True
        if self._connect_attempted and not force:
            return self._is_connected

        self._connect_attempted = True
        if getattr(settings, "storage_backend", "auto") in ["inmemory", "json"]:
            logger.info("Storage backend explicitly set to inmemory/json. Skipping MongoDB connection.")
            self._is_connected = False
            return False

        uri = settings.mongodb_uri or ""
        if "<db_username>" in uri or "<db_password>" in uri:
            msg = "MongoDB URI contains unresolved placeholder '<db_username>' or '<db_password>'. Please update your username in .env."
            logger.warning(msg)
            self._last_error = msg
            self._is_connected = False
            return False

        try:
            # Set timeouts and clean connection pool appropriate for cloud Atlas
            client = pymongo.MongoClient(
                uri,
                maxPoolSize=50,
                minPoolSize=5,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=10000,
                retryWrites=True
            )
            # Ping to verify active connection
            client.admin.command("ping")

            # Determine target database
            db_name = settings.mongodb_db_name or "car_consultant"
            parsed = urlparse(uri)
            if parsed.path and parsed.path.strip("/"):
                path_db = parsed.path.strip("/").split("?")[0]
                if path_db:
                    db_name = path_db

            self._client = client
            self._db = client[db_name]
            self._is_connected = True
            self._last_error = None
            logger.info(f"Successfully connected to MongoDB Atlas database '{db_name}'.")

            # Automatically establish collections, indexes, and initial seeds
            self._init_db_indexes_and_seed()
            return True
        except Exception as e:
            err_msg = f"MongoDB connection attempt failed: {e}"
            logger.warning(err_msg)
            self._last_error = str(e)
            self._client = None
            self._db = None
            self._is_connected = False
            return False

    def _init_db_indexes_and_seed(self):
        """Creates clean indexes and seeds vehicles/users if collection is empty."""
        if self._db is None:
            return

        import json
        import hashlib
        from pathlib import Path
        from datetime import datetime

        try:
            # 1. Indexes
            self._db.users.create_index([("id", pymongo.ASCENDING)], unique=True)
            self._db.users.create_index([("email", pymongo.ASCENDING)], unique=True)

            self._db.vehicles.create_index([("id", pymongo.ASCENDING)], unique=True)
            self._db.vehicles.create_index([("category", pymongo.ASCENDING)])
            self._db.vehicles.create_index([("brand", pymongo.ASCENDING)])
            self._db.vehicles.create_index([("purchase_price", pymongo.ASCENDING)])

            self._db.purchases.create_index([("id", pymongo.ASCENDING)], unique=True)
            self._db.purchases.create_index([("orderId", pymongo.ASCENDING)])
            self._db.purchases.create_index([("userId", pymongo.ASCENDING)])

            self._db.orders.create_index([("id", pymongo.ASCENDING)], unique=True)
            self._db.orders.create_index([("orderId", pymongo.ASCENDING)])
            self._db.orders.create_index([("userId", pymongo.ASCENDING)])

            self._db.payments.create_index([("id", pymongo.ASCENDING)], unique=True)
            self._db.payments.create_index([("transactionId", pymongo.ASCENDING)], unique=True)
            self._db.payments.create_index([("orderId", pymongo.ASCENDING)])
            self._db.payments.create_index([("userId", pymongo.ASCENDING)])

            self._db.selling_listings.create_index([("id", pymongo.ASCENDING)], unique=True)
            self._db.selling_listings.create_index([("userId", pymongo.ASCENDING)])

            # 2. Seed vehicles if empty
            if self._db.vehicles.count_documents({}) == 0:
                vehicles_path = Path(__file__).parent.parent.parent / "data" / "vehicles.json"
                if vehicles_path.exists():
                    with open(vehicles_path, "r", encoding="utf-8") as f:
                        vehicles_data = json.load(f)
                    for v in vehicles_data:
                        self._db.vehicles.update_one({"id": v["id"]}, {"$set": v}, upsert=True)
                    logger.info(f"Seeded {len(vehicles_data)} vehicles directly into MongoDB Atlas.")

            # 3. Seed demo user in users collection if not present
            demo_user = self._db.users.find_one({"email": "demo@auramotors.com"})
            if not demo_user:
                self._db.users.update_one(
                    {"email": "demo@auramotors.com"},
                    {
                        "$set": {
                            "id": "usr_demo_01",
                            "name": "Alex Vance",
                            "email": "demo@auramotors.com",
                            "phone": "+91 98765 43210",
                            "password_hash": hashlib.sha256("Password123!".encode()).hexdigest(),
                            "saved_vehicles": ["CAR-001", "CAR-021"],
                            "created_at": "2026-11-01T10:00:00Z",
                            "updated_at": datetime.utcnow().isoformat() + "Z"
                        }
                    },
                    upsert=True
                )
                logger.info("Demo user 'demo@auramotors.com' seeded in MongoDB Atlas 'users' collection.")
        except Exception as e:
            logger.warning(f"Error during MongoDB indexes/seed setup: {e}")

    def disconnect(self):
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
        self._client = None
        self._db = None
        self._is_connected = False
        self._connect_attempted = False

    def get_status(self) -> Dict[str, Any]:
        return {
            "connected": self._is_connected,
            "database": self._db.name if self._db is not None else None,
            "last_error": self._last_error,
            "uri_configured": bool(settings.mongodb_uri and "<db_username>" not in settings.mongodb_uri)
        }

mongodb_manager = MongoDBManager.get_instance()

