from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
import shutil
import os
from app.schemas.call_schemas import CallInitiateRequest, CallResponse, VapiWebhookEvent, MessageProcessRequest
from app.services.call_service import call_service
from app.utils.logger import logger

router = APIRouter()

@router.post("/start-call", response_model=CallResponse)
async def start_call(request: CallInitiateRequest):
    """
    Triggers an outbound AI call via Vapi for a specific lead.
    """
    try:
        response = await call_service.initiate_call(request.lead, request.integrations)
        return CallResponse(
            status="success",
            call_id=response.get("id"),
            message="Call initiated successfully"
        )
    except Exception as e:
        logger.error(f"Failed to start call: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/vapi")
async def vapi_webhook(event: VapiWebhookEvent):
    """
    Handles Vapi status updates, transcripts, and call ending events.
    """
    try:
        result = await call_service.handle_webhook(event.message)
        return result
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.post("/process-message")
async def process_message(request: MessageProcessRequest):
    """
    Manually process a conversation turn or use as a fallback brain.
    """
    try:
        # This could interact with the CallingAgent directly
        # For simplicity, we just log and return a stub response here
        # or integrate it with the service layer
        logger.info(f"Processing message for call {request.call_id}: {request.transcript}")
        return {"role": "assistant", "content": "I am processing your message."}
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/end-call")
async def end_call(call_id: str):
    """
    Finalize and return the result for a given call.
    """
    try:
        # In a real scenario, this would trigger the finalization logic
        # For now, we'll try to find the agent and return the result
        result = await call_service.finalize_call(call_id, {"transcript": "Call ended manually."})
        return result
    except Exception as e:
        logger.error(f"End call error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-knowledge")
async def upload_knowledge(file: UploadFile = File(...)):
    """
    Upload a DOCX file to the knowledge base and re-index the RAG engine.
    """
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported.")
    
    upload_dir = "knowledge"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Re-build RAG index with the new file
    try:
        rag_engine.build_index()
        logger.info(f"Successfully uploaded and indexed: {file.filename}")
        return {"status": "success", "message": f"File {file.filename} indexed successfully."}
    except Exception as e:
        logger.error(f"Indexing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to index file: {str(e)}")

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AI Outbound Calling Engine"}
