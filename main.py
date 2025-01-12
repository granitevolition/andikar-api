from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.config import settings
from app.core.logging import setup_logging
from app.services.document_processor import DocumentProcessor
from app.services.openai_service import OpenAIService

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize services
processor = DocumentProcessor()
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

@app.post("/process")
async def process_document(file: UploadFile = File(...)):
    """Process a document and return the results"""
    try:
        content = await file.read()
        original, processed, cleaned = await processor.process_document(content)
        
        return {
            "message": "Document processed successfully",
            "files": {
                "original": original,
                "processed": processed,
                "cleaned": cleaned
            }
        }
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-text")
async def process_text(request: dict):
    """Process a single text input"""
    try:
        text = request.get("content")
        if not text:
            raise HTTPException(status_code=400, detail="No content provided")
            
        rewritten = await openai_service.rewrite_text_chunk(text)
        cleaned = await processor.clean_text(rewritten, text)
        
        return {
            "original": text,
            "rewritten": rewritten,
            "cleaned": cleaned
        }
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
