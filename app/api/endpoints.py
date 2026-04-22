from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
import shutil
import os
from app.schemas.call_schemas import CallInitiateRequest, CallResponse, TwilioWebhookEvent, MessageProcessRequest
from app.services.call_service import call_service
from app.rag.engine import rag_engine
from app.utils.logger import logger

router = APIRouter()

@router.post("/start-call", response_model=CallResponse)
async def start_call(request: CallInitiateRequest):
    try:
        response = await call_service.initiate_call(request.lead)
        return CallResponse(
            status="success",
            call_sid=response.get("call_sid"),
            message="Call initiated successfully"
        )
    except Exception as e:
        logger.error(f"Failed to start call: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/twilio")
async def twilio_webhook(event: TwilioWebhookEvent):
    try:
        result = await call_service.handle_webhook(event.event)
        return result
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.post("/process-message")
async def process_message(request: MessageProcessRequest):
    try:
        logger.info(f"Processing message for call {request.call_sid}: {request.transcript}")
        return {"status": "ok", "message": "Message processed"}
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/end-call/{call_sid}")
async def end_call(call_sid: str):
    try:
        result = await call_service.finalize_call(call_sid, {})
        return result
    except Exception as e:
        logger.error(f"End call error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-knowledge")
async def upload_knowledge(file: UploadFile = File(...)):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported.")
    
    upload_dir = "knowledge"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
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