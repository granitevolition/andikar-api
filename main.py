from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1 import document  # importing existing document router

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    document.router,
    prefix=f"{settings.API_V1_STR}/documents",
    tags=["documents"]
)

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "API is running"}

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
