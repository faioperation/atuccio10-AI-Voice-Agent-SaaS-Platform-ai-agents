import httpx
from app.config import settings
from app.utils.logger import logger
from typing import Dict, Any, List, Optional

class GHLClient:
    """
    GoHighLevel (LeadConnector) Integration Client.
    Handles contact management and appointment booking.
    """
    def __init__(self):
        self.api_key = settings.GHL_API_KEY
        self.base_url = settings.GHL_API_BASE_URL
        self.location_id = settings.GHL_LOCATION_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Version": "2021-07-28" # GHL API version
        }

    async def get_contact_by_phone(self, phone: str, api_key: str = None, location_id: str = None) -> Optional[Dict[str, Any]]:
        """Retrieve a contact from GHL by phone number."""
        headers = self.headers.copy()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        loc_id = location_id or self.location_id
        url = f"{self.base_url}/contacts/"
        params = {"locationId": loc_id, "query": phone}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                contacts = response.json().get("contacts", [])
                return contacts[0] if contacts else None
            except Exception as e:
                logger.error(f"GHL Error (get_contact): {str(e)}")
                return None

    async def book_appointment(self, contact_id: str, calendar_id: str, start_time: str, title: str = "AI Sales Booking", api_key: str = None, location_id: str = None) -> Dict[str, Any]:
        """Book an appointment for a contact in a specific calendar."""
        headers = self.headers.copy()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            
        loc_id = location_id or self.location_id
        url = f"{self.base_url}/appointments/"
        payload = {
            "calendarId": calendar_id,
            "locationId": loc_id,
            "contactId": contact_id,
            "startTime": start_time,
            "title": title,
            "status": "confirmed"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"GHL Error (book_appointment): {str(e)}")
                return {"status": "error", "message": str(e)}

    async def create_lead(self, name: str, phone: str, email: str = None) -> Dict[str, Any]:
        """Create a new contact/lead in GHL."""
        url = f"{self.base_url}/contacts/"
        payload = {
            "locationId": self.location_id,
            "firstName": name.split()[0],
            "lastName": " ".join(name.split()[1:]) if " " in name else "",
            "phone": phone,
            "email": email,
            "source": "AI Outbound Engine"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"GHL Error (create_lead): {str(e)}")
                return {"status": "error", "message": str(e)}

ghl_client = GHLClient()
