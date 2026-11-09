import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.app.config import settings
from backend.app.db.mongodb import mongodb_manager
from backend.app.db.transfer_to_mongo import transfer_all_data_to_mongodb
from backend.app.observability.langfuse_client import langfuse_manager
from backend.app.services.llm_service import llm_service

def test_config_and_keys():
    print("1. Testing configuration loading...", flush=True)
    assert settings.openai_api_key.startswith("sk-"), "OpenAI API key should be loaded"
    assert settings.langfuse_public_key.startswith("pk-lf-"), "Langfuse public key should be loaded"
    assert settings.langfuse_secret_key.startswith("sk-lf-"), "Langfuse secret key should be loaded"
    assert settings.is_openai_enabled is True, "OpenAI should be enabled"
    assert settings.is_langfuse_enabled is True, "Langfuse should be enabled"
    print("✓ Config keys successfully loaded from .env")

def test_mongodb_manager_safety():
    print("2. Testing MongoDB connection manager...", flush=True)
    status = mongodb_manager.get_status()
    print("MongoDB status:", status)
    assert "connected" in status
    assert "uri_configured" in status
    print("✓ MongoDB manager safely reports connection status")

def test_transfer_function():
    print("3. Testing data transfer function structure...", flush=True)
    result = transfer_all_data_to_mongodb(force=False)
    assert isinstance(result, dict)
    assert "success" in result
    print("✓ Transfer function returned:", result.get("error") or result.get("message"))

def test_llm_and_langfuse_services():
    print("4. Testing LLM and Langfuse services...", flush=True)
    assert llm_service is not None
    assert langfuse_manager is not None
    assert langfuse_manager.is_enabled() is True
    assert llm_service.is_available() is True
    print("✓ LLMService (GPT-4o) and LangfuseManager successfully initialized")

if __name__ == "__main__":
    test_config_and_keys()
    test_mongodb_manager_safety()
    test_transfer_function()
    test_llm_and_langfuse_services()
    print("\nALL DB, OPENAI, AND LANGFUSE VERIFICATION TESTS PASSED!")

