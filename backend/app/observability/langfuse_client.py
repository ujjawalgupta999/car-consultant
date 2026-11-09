import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..config import settings

logger = logging.getLogger("car_consultant.observability.langfuse")

class LangfuseManager:
    _instance: Optional["LangfuseManager"] = None

    def __init__(self):
        self._client = None
        self._is_enabled = False
        self._init_client()

    @classmethod
    def get_instance(cls) -> "LangfuseManager":
        if cls._instance is None:
            cls._instance = LangfuseManager()
        return cls._instance

    def _init_client(self):
        if not settings.is_langfuse_enabled:
            logger.info("Langfuse tracing is disabled (keys not configured).")
            self._client = None
            self._is_enabled = False
            return

        try:
            from langfuse import Langfuse
            host = settings.effective_langfuse_host
            self._client = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=host
            )
            self._is_enabled = True
            logger.info(f"Langfuse observability client initialized successfully targeting {host}.")
        except Exception as e:
            logger.warning(f"Failed to initialize Langfuse client: {e}")
            self._client = None
            self._is_enabled = False

    def is_enabled(self) -> bool:
        return self._is_enabled and self._client is not None

    def trace_turn(
        self,
        session_id: str,
        user_id: str,
        turn_name: str,
        user_message: str,
        assistant_response: str,
        model: str = "gpt-4o",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ):
        """
        Records a complete turn (input -> generation) to Langfuse.
        Runs safely without ever throwing or blocking.
        """
        if not self.is_enabled():
            return None

        try:
            trace = self._client.trace(
                name=turn_name,
                session_id=session_id,
                user_id=user_id,
                input=user_message,
                output=assistant_response,
                metadata=metadata or {},
                tags=tags or ["aura-ai-consultant", "automotive-marketplace"]
            )

            # Record generation details under the trace
            trace.generation(
                name=f"{turn_name}_generation",
                model=model,
                input=user_message,
                output=assistant_response,
                start_time=datetime.utcnow()
            )

            return trace
        except Exception as e:
            logger.debug(f"Langfuse trace creation notice: {e}")
            return None

    def flush(self):
        if self._client:
            try:
                self._client.flush()
            except Exception:
                pass

langfuse_manager = LangfuseManager.get_instance()

