from typing import List, Dict, Any, Optional
from app.agents.prompts import SYSTEM_PROMPT_TEMPLATE
from app.rag.engine import rag_engine
from app.integrations.openai_client import openai_client
from app.integrations.ghl_client import ghl_client
from app.config import settings
from app.utils.logger import logger

class CallingAgent:
    def __init__(self, customer_name: str, customer_context: Dict[str, Any] = None):
        self.customer_name = customer_name
        self.customer_context = customer_context or {}
        self.history = []

    async def generate_response(self, user_message: str) -> str:
        context_chunks = rag_engine.query(user_message)
        
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            company_context=context_chunks,
            customer_name=self.customer_name,
            customer_context=self.customer_context
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        for turn in self.history:
            messages.append(turn)
        
        messages.append({"role": "user", "content": user_message})
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "book_appointment",
                    "description": "Books an appointment in the CRM",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "time": {"type": "string", "description": "Preferred time for the appointment"},
                            "notes": {"type": "string", "description": "Additional notes for the booking"}
                        },
                        "required": ["time"]
                    }
                }
            }
        ]
        
        response = await openai_client.generate_response(messages, tools=tools)
        
        if response.tool_calls:
            import json
            for tool_call in response.tool_calls:
                if tool_call.function.name == "book_appointment":
                    args = json.loads(tool_call.function.arguments)
                    
                    booking_result = await ghl_client.book_appointment(
                        contact_id=self.customer_context.get("contact_id", "STUB_CONTACT"),
                        calendar_id=self.customer_context.get("calendar_id", "STUB_CALENDAR"),
                        start_time=args.get("time"),
                        title=f"Interested Lead: {self.customer_name}"
                    )
                    
                    messages.append(response)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": "book_appointment",
                        "content": json.dumps(booking_result)
                    })
                    
                    final_response = await openai_client.generate_response(messages)
                    self.history.append({"role": "user", "content": user_message})
                    self.history.append({"role": "assistant", "content": final_response.content})
                    return final_response.content
        
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": response.content})
        return response.content

    async def get_summary(self) -> str:
        transcript = "\n".join([f"{m['role']}: {m['content']}" for m in self.history])
        messages = [
            {"role": "system", "content": "Summarize this sales call transcript briefly."},
            {"role": "user", "content": transcript}
        ]
        response = await openai_client.generate_response(messages)
        return response.content