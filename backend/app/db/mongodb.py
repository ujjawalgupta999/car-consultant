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

    @classmethod
    def get_instance(cls) -> "MongoDBManager":
        if cls._instance is None:
            cls._instance = MongoDBManager()
        return cls._instance

    def is_connected(self) -> bool:
        return self._is_connected and self._client is not None

    def get_database(self) -> Optional[Database]:
        if not self._is_connected:
            self.connect()
        return self._db

    def get_collection(self, name: str):
        db = self.get_database()
        if db is not None:
            return db[name]
        return None

    def connect(self) -> bool:
        """
        Attempts to connect to MongoDB using settings.mongodb_uri.
        Handles placeholders cleanly so app never crashes if credentials need updating.
        """
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
            # Set timeouts appropriate for cloud Atlas as well as local MongoDB
            client = pymongo.MongoClient(
                uri,
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
            return True
        except Exception as e:
            err_msg = f"MongoDB connection attempt failed: {e}"
            logger.warning(err_msg)
            self._last_error = str(e)
            self._client = None
            self._db = None
            self._is_connected = False
            return False

    def disconnect(self):
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
        self._client = None
        self._db = None
        self._is_connected = False

    def get_status(self) -> Dict[str, Any]:
        return {
            "connected": self._is_connected,
            "database": self._db.name if self._db is not None else None,
            "last_error": self._last_error,
            "uri_configured": bool(settings.mongodb_uri and "<db_username>" not in settings.mongodb_uri)
        }

mongodb_manager = MongoDBManager.get_instance()

