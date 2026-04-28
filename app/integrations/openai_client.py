import openai
from app.config import settings
from app.utils.logger import logger
from app.agents.prompts import INTENT_PROMPT
from typing import List, Dict, Any, Optional


class OpenAIClient:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model  = settings.OPENAI_MODEL

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        tools:    Optional[List[Dict[str, Any]]] = None,
        api_key:  Optional[str] = None,
    ) -> Any:
        try:
            # Use a per-call client when an override key is supplied
            client = openai.AsyncOpenAI(api_key=api_key) if api_key else self.client

            kwargs: Dict[str, Any] = {
                "model":       self.model,
                "messages":    messages,
                "temperature": 0.7,
            }
            if tools:
                kwargs["tools"] = tools

            response = await client.chat.completions.create(**kwargs)
            return response.choices[0].message

        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise

    async def detect_intent(self, transcript: str) -> str:
        """
        Classify customer intent using the canonical INTENT_PROMPT from prompts.py.
        Returns: INTERESTED | NOT_INTERESTED | OBJECTION | APPOINTMENT_REQUEST | CALLBACK_REQUEST
        """
        formatted = INTENT_PROMPT.format(user_message=transcript)
        prompt = (
            f"{formatted}\n\n"
            "Choose from: [INTERESTED, NOT_INTERESTED, OBJECTION, APPOINTMENT_REQUEST, CALLBACK_REQUEST]\n"
            "Return ONLY the intent keyword, nothing else."
        )
        messages = [
            {"role": "system", "content": "You are an expert sales call intent classifier."},
            {"role": "user",   "content": prompt},
        ]
        response = await self.generate_response(messages)
        return response.content.strip().upper()


openai_client = OpenAIClient()
