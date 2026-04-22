import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router
from app.rag.engine import rag_engine
from app.utils.logger import logger
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-ready AI Outbound Calling Engine with RAG and Intent Detection."
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing AI Calling Engine...")
    # Initialize RAG engine by building index from DOCX files
    try:
        rag_engine.build_index()
    except Exception as e:
        logger.error(f"Failed to initialize RAG: {e}")

@app.get("/")
async def root():
    return {
        "message": "Welcome to InsureFlow AI Outbound Calling Engine",
        "docs": "/docs",
        "health": "/api/v1/health"
    }                 

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
