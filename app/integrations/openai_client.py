import openai
from app.config import settings
from app.utils.logger import logger
from typing import List, Dict, Any

class OpenAIClient:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    async def generate_response(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]] = None, api_key: str = None) -> Any:
        try:
            client = self.client
            if api_key:
                client = openai.AsyncOpenAI(api_key=api_key)
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
            }
            if tools:
                kwargs["tools"] = tools
            
            response = await self.client.chat.completions.create(**kwargs)
            return response.choices[0].message
        except Exception as e:
            logger.error(f"OpenAI Error: {str(e)}")
            raise

    async def detect_intent(self, transcript: str) -> str:
        prompt = f"""
        Analyze the following call transcript and detect the customer's intent.
        Choose from: [INTERESTED, NOT_INTERESTED, OBJECTION, APPOINTMENT_REQUEST, CALLBACK_REQUEST]
        Return ONLY the intent keyword.

        Transcript: {transcript}
        """
        messages = [{"role": "system", "content": "You are an expert intent classifier."},
                    {"role": "user", "content": prompt}]
        
        response = await self.generate_response(messages)
        return response.content.strip().upper()

openai_client = OpenAIClient()
