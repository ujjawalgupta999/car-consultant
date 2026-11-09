import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..config import settings
from ..observability.langfuse_client import langfuse_manager

logger = logging.getLogger("car_consultant.llm")

AURA_SYSTEM_PROMPT = """You are Aura, the premier AI Automotive Consultant for Aura Motors.
Your mission is to provide authoritative, transparent, and refined automotive guidance to car buyers.

Guiding Principles:
1. Focus strictly on purchasing, vehicle specifications, ownership experience, real-world mileage, safety ratings, maintenance costs, and financing.
2. Maintain an elegant, premium, yet approachable tone.
3. When discussing vehicles, highlight both strengths and honest trade-offs (e.g. city fuel efficiency, ride firmness, boot space).
4. Keep responses structured and concise using Markdown formatting (bolding key specs, bullet points for trade-offs).
5. Never hallucinate pricing or specs—stay grounded in the verified parameters provided in the context.
"""

class LLMService:
    _instance: Optional["LLMService"] = None

    def __init__(self):
        self._openai_client = None
        self._init_openai()

    @classmethod
    def get_instance(cls) -> "LLMService":
        if cls._instance is None:
            cls._instance = LLMService()
        return cls._instance

    def _init_openai(self):
        if not settings.is_openai_enabled:
            logger.info("OpenAI integration is in mock/offline mode (API key not provided or AGENT_MODE != 'openai').")
            self._openai_client = None
            return

        try:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=settings.openai_api_key)
            logger.info(f"OpenAI client initialized with model '{settings.openai_model}'.")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")
            self._openai_client = None

    def is_available(self) -> bool:
        return self._openai_client is not None

    def generate_chat_response(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: str = "sess_default",
        user_id: str = "usr_demo_01",
        turn_name: str = "aura_consultation"
    ) -> Optional[str]:
        """
        Generates an AI response using OpenAI GPT-4o and traces it to Langfuse.
        Falls back to None on any error so caller uses deterministic fallbacks.
        """
        if not self.is_available():
            return None

        context = context or {}
        messages = [{"role": "system", "content": AURA_SYSTEM_PROMPT}]

        # Inject contextual vehicle or preference details
        context_parts = []
        if context.get("vehicle"):
            v = context["vehicle"]
            context_parts.append(
                f"Selected Vehicle: {v.get('year')} {v.get('brand')} {v.get('model')} ({v.get('category')})\n"
                f"Ex-Showroom Price: ₹{v.get('purchase_price', 0):,.0f}\n"
                f"Fuel: {v.get('fuel_type')}, Transmission: {v.get('transmission')}, Seats: {v.get('seats')}\n"
                f"Location: {v.get('location')}, Rating: {v.get('rating')}/5"
            )
        if context.get("preferences"):
            p = context["preferences"]
            context_parts.append(
                f"User Preferences: Category={p.get('category')}, Budget=₹{p.get('budget', {}).get('amount', 0):,.0f}, "
                f"Location={p.get('location')}, Transmission={p.get('transmission')}"
            )
        if context.get("pending_order_id"):
            context_parts.append(f"Active Checkout Order ID: {context['pending_order_id']}")

        if context_parts:
            messages.append({
                "role": "system",
                "content": "Verified Inventory & Customer Context:\n" + "\n\n".join(context_parts)
            })

        messages.append({"role": "user", "content": user_message})

        try:
            response = self._openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=0.7,
                max_tokens=600
            )

            assistant_reply = response.choices[0].message.content or ""

            # Log to Langfuse for observability
            if langfuse_manager.is_enabled():
                langfuse_manager.trace_turn(
                    session_id=session_id,
                    user_id=user_id,
                    turn_name=turn_name,
                    user_message=user_message,
                    assistant_response=assistant_reply,
                    model=settings.openai_model,
                    metadata={
                        "context": context,
                        "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                        "completion_tokens": getattr(response.usage, "completion_tokens", 0)
                    }
                )

            return assistant_reply
        except Exception as e:
            logger.warning(f"OpenAI GPT-4o generation encountered an error: {e}. Falling back to rule engine.")
            return None

    def enhance_inquiry_advice(
        self,
        vehicle: Dict[str, Any],
        user_query: str,
        session_id: str = "sess_default",
        user_id: str = "usr_demo_01"
    ) -> Optional[str]:
        """Specific GPT-4o deep-dive advice for a vehicle inquiry."""
        return self.generate_chat_response(
            user_message=f"The customer is inquiring: '{user_query}'. Please provide an expert automotive appraisal of this vehicle.",
            context={"vehicle": vehicle},
            session_id=session_id,
            user_id=user_id,
            turn_name="vehicle_deep_dive"
        )

llm_service = LLMService.get_instance()

