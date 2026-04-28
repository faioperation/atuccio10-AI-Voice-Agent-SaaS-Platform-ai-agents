import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.endpoints import router as api_router
from app.rag.engine import rag_engine
from app.utils.logger import logger
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-ready AI Outbound Calling Engine with RAG and Intent Detection."
)

# ---------------------------------------------------------------------------
# CORS — restrict to configured origins in production
# ---------------------------------------------------------------------------
allowed_origins = (
    ["*"]
    if settings.ALLOWED_ORIGINS.strip() == "*"
    else [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Optional API key middleware — enabled only when API_SECRET_KEY is set.
# Twilio webhooks and health check are exempt (Twilio signs its own requests).
# ---------------------------------------------------------------------------
EXEMPT_PATHS = {"/", f"{settings.API_V1_STR}/health", f"{settings.API_V1_STR}/webhook/twilio"}

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if settings.API_SECRET_KEY and request.url.path not in EXEMPT_PATHS:
        # Accept the key in Authorization: Bearer <key>  OR  X-API-Key: <key>
        auth_header = request.headers.get("Authorization", "")
        x_api_key   = request.headers.get("X-API-Key", "")
        bearer_key  = auth_header.replace("Bearer ", "").strip()
        provided    = bearer_key or x_api_key

        if provided != settings.API_SECRET_KEY:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key. Use 'Authorization: Bearer <key>' or 'X-API-Key: <key>'"}
            )
    return await call_next(request)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing AI Calling Engine...")
    try:
        rag_engine.build_index()
    except Exception as e:
        logger.error(f"Failed to initialize RAG: {e}")

@app.get("/")
async def root():
    return {
        "message": "Welcome to InsureFlow AI Outbound Calling Engine",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
