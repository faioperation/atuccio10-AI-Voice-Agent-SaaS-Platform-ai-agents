from typing import Dict, Any, Optional
from app.integrations.vapi_client import vapi_client
from app.integrations.openai_client import openai_client
from app.agents.calling_agent import CallingAgent
from app.schemas.call_schemas import LeadData, CallResult, IntegrationConfig
from app.utils.logger import logger
from app.config import settings

# Global store for active agents (in a real app, use Redis or DB)
active_agents: Dict[str, CallingAgent] = {}

class CallService:
    async def initiate_call(self, lead: LeadData, integrations: IntegrationConfig = None) -> Dict[str, Any]:
        """
        Starts an outbound call and initializes the agent.
        """
        logger.info(f"Initiating call for {lead.name} at {lead.phone_number}")
        
        # Initialize the AI Agent for this call
        agent = CallingAgent(
            customer_name=lead.name, 
            customer_context=lead.metadata or {"context": lead.context},
            integration_config=integrations
        )
        
        # Trigger Vapi outbound call
        response = await vapi_client.start_outbound_call(
            phone_number=lead.phone_number,
            assistant_id=settings.VAPI_ASSISTANT_ID,
            lead_data=lead.dict(),
            voice_id=integrations.elevenlabs_voice_id if integrations else None,
            voice_api_key=integrations.elevenlabs_api_key if integrations else None
        )
        
        call_id = response.get("id")
        if call_id:
            active_agents[call_id] = agent
            logger.info(f"Call started with ID: {call_id}")
            
        return response

    async def handle_webhook(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handles incoming webhooks from Vapi.
        """
        message = event.get("message", {})
        msg_type = message.get("type")
        call_id = message.get("call", {}).get("id")
        
        logger.info(f"Received Vapi webhook: {msg_type} for call {call_id}")
        
        if msg_type == "transcript" and message.get("transcriptType") == "final":
            # Process individual turns if needed, or Vapi can handle the loop
            pass
        
        if msg_type == "end-of-call-report":
            # Call ended, finalize results
            return await self.finalize_call(call_id, message)
            
        return {"status": "ok"}

    async def finalize_call(self, call_id: str, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes the call outcome once it's ended.
        """
        agent = active_agents.pop(call_id, None)
        transcript_text = report.get("transcript", "")
        
        # Detect intent and generate summary
        intent = await openai_client.detect_intent(transcript_text)
        summary = await openai_client.generate_response([
            {"role": "system", "content": "Briefly summarize this call transcript and the outcome."},
            {"role": "user", "content": transcript_text}
        ])
        
        result = CallResult(
            status="completed",
            outcome=intent,
            summary=summary.content,
            transcript=[], # Full transcript parsing logic here
            appointment_created="appointment" in intent.lower()
        )
        
        logger.info(f"Call {call_id} finalized with outcome: {intent}")
        return result.dict()

call_service = CallService()
