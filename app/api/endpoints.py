import asyncio
import base64
import json
import shutil
import os
from fastapi import APIRouter, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

from app.schemas.call_schemas import (
    CallInitiateRequest, CallResponse, TwilioWebhookEvent, MessageProcessRequest
)
from app.services.call_service import call_service
from app.rag.engine import rag_engine
from app.utils.logger import logger

router = APIRouter()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AI Outbound Calling Engine"}


# ---------------------------------------------------------------------------
# Start outbound call
# ---------------------------------------------------------------------------

@router.post("/start-call", response_model=CallResponse)
async def start_call(request: CallInitiateRequest):
    try:
        response = await call_service.initiate_call(request.lead)
        return CallResponse(
            status="success",
            call_sid=response.get("call_sid"),
            message="Call initiated successfully",
        )
    except Exception as e:
        logger.error(f"Failed to start call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# TwiML — Twilio calls this URL when the call connects to get instructions
# ---------------------------------------------------------------------------

@router.get("/twiml/{call_sid}", response_class=Response)
async def get_twiml(call_sid: str):
    """
    Returns TwiML that tells Twilio to connect the answered call to our
    WebSocket media stream endpoint for real-time audio processing.
    """
    twiml = call_service.twilio_client_ref().generate_twiml(call_sid) \
        if hasattr(call_service, "twilio_client_ref") \
        else _build_twiml(call_sid)
    return Response(content=twiml, media_type="application/xml")


def _build_twiml(call_sid: str) -> str:
    from app.integrations.twilio_client import twilio_client
    return twilio_client.generate_twiml(call_sid)


# ---------------------------------------------------------------------------
# Twilio status-callback webhook (HTTP POST)
# ---------------------------------------------------------------------------

@router.post("/webhook/twilio")
async def twilio_webhook(event: TwilioWebhookEvent):
    try:
        result = await call_service.handle_webhook(event.event)
        return result
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# WebSocket media stream  (wss://.../api/v1/stream/{call_sid})
# Twilio Streams sends base64 μ-law audio chunks here in real time.
# ---------------------------------------------------------------------------

@router.websocket("/stream/{call_sid}")
async def websocket_stream(websocket: WebSocket, call_sid: str):
    await websocket.accept()
    logger.info(f"WebSocket stream connected for call: {call_sid}")

    try:
        while True:
            raw = await websocket.receive_text()
            message = json.loads(raw)
            event   = message.get("event")

            if event == "connected":
                logger.info(f"Twilio stream connected — call: {call_sid}")

            elif event == "start":
                logger.info(f"Twilio stream started — call: {call_sid}")

            elif event == "media":
                audio_payload = message.get("media", {}).get("payload", "")
                if not audio_payload:
                    continue

                audio_bytes    = base64.b64decode(audio_payload)
                response_audio = await call_service.handle_audio(call_sid, audio_bytes)

                if response_audio:
                    # Send the AI's audio response back to Twilio
                    audio_b64 = base64.b64encode(response_audio).decode("utf-8")
                    await websocket.send_text(json.dumps({
                        "event": "media",
                        "media": {"payload": audio_b64},
                    }))

            elif event == "stop":
                logger.info(f"Twilio stream stopped — call: {call_sid}")
                await call_service.finalize_call(call_sid, {})
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for call: {call_sid}")
        await call_service.finalize_call(call_sid, {})
    except Exception as e:
        logger.error(f"WebSocket error for call {call_sid}: {e}")


# ---------------------------------------------------------------------------
# Process message (manual / testing)  — was a stub, now fully implemented
# ---------------------------------------------------------------------------

@router.post("/process-message")
async def process_message(request: MessageProcessRequest):
    """
    Manually inject a transcript turn into an active call's AI agent.
    Useful for debugging or as an HTTP-based fallback when WebSockets
    are unavailable.
    """
    try:
        agent = call_service.get_agent(request.call_sid)
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"No active call found for call_sid: {request.call_sid}"
            )

        logger.info(f"Processing message for call {request.call_sid}: {request.transcript}")
        response_text = await agent.generate_response(request.transcript)
        return {"role": "assistant", "content": response_text}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# End call manually
# ---------------------------------------------------------------------------

@router.post("/end-call/{call_sid}")
async def end_call(call_sid: str):
    try:
        result = await call_service.finalize_call(call_sid, {})
        return result
    except Exception as e:
        logger.error(f"End call error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Upload knowledge base document
# ---------------------------------------------------------------------------

@router.post("/upload-knowledge")
async def upload_knowledge(file: UploadFile = File(...)):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported.")

    upload_dir = "knowledge"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        rag_engine.build_index()
        logger.info(f"Successfully uploaded and indexed: {file.filename}")
        return {"status": "success", "message": f"File {file.filename} indexed successfully."}
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to index file: {str(e)}")