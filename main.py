from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import time
from app.core.config import settings
from app.core.logging import setup_logging
from app.models.schemas import TextRequest, TextResponse
from app.services.openai_service import OpenAIService

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize services
openai_service = OpenAIService()

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

@app.post("/process-text", response_model=TextResponse)
async def process_text(request: TextRequest):
    """Process a single text input"""
    try:
        start_time = time.time()
        logger.info("Processing text request")
        
        # Process the text using OpenAI
        rewritten = await openai_service.rewrite_text_chunk(
            request.content,
            style=request.style
        )
        
        processing_time = time.time() - start_time
        
        return TextResponse(
            original=request.content,
            rewritten=rewritten,
            cleaned=rewritten,  # For now, using rewritten as cleaned
            processing_time=processing_time
        )
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
