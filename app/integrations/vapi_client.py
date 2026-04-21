import httpx
from app.config import settings
from app.utils.logger import logger
from typing import Dict, Any, Optional

class VapiClient:
    def __init__(self):
        self.api_key = settings.VAPI_API_KEY
        self.base_url = settings.VAPI_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def start_outbound_call(
        self, 
        phone_number: str, 
        assistant_id: str, 
        lead_data: Dict[str, Any], 
        voice_id: str = None, 
        voice_api_key: str = None
    ) -> Dict[str, Any]:
        """
        Triggers an outbound call via Vapi.
        """
        url = f"{self.base_url}/call/phone"
        payload = {
            "assistantId": assistant_id,
            "phoneNumberId": settings.VAPI_PHONE_NUMBER_ID,
            "customer": {
                "number": phone_number,
                "name": lead_data.get("name", "Valued Customer")
            },
            "assistantOverrides": {
                "transcriber": {
                    "provider": "deepgram",
                    "model": "nova-2",
                    "language": "en-US"
                },
                "voice": {
                    "provider": "elevenlabs",
                    "voiceId": voice_id or settings.ELEVENLABS_VOICE_ID,
                    "apiKey": voice_api_key or settings.ELEVENLABS_API_KEY
                },
                "variableValues": {
                    "customerName": lead_data.get("name", ""),
                    "customerContext": str(lead_data.get("context", ""))
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Vapi API Error: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Vapi Request Error: {str(e)}")
                raise

    async def get_call_details(self, call_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/call/{call_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            return response.json()

vapi_client = VapiClient()
