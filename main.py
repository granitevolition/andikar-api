from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import time
from typing import List, Optional
from pydantic import BaseModel
from app.core.config import settings
from app.core.logging import setup_logging
from app.services.openai_service import OpenAIService

# Keep existing schema definitions
class TextRequest(BaseModel):
    content: str
    style: Optional[str] = "scholar"

class TextResponse(BaseModel):
    original: str
    rewritten: str
    cleaned: str
    processing_time: float

# Add new paragraph processing schemas
class ParagraphRequest(BaseModel):
    text: str
    style: Optional[str] = "scholar"
    min_paragraph_length: Optional[int] = 100

class ParagraphResponse(BaseModel):
    paragraphs: List[TextResponse]
    total_paragraphs: int
    processing_time: float

# Initialize services (keeping existing setup)
setup_logging()
logger = logging.getLogger(__name__)
openai_service = OpenAIService()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep existing endpoint
@app.post("/process-text", response_model=TextResponse)
async def process_text(request: TextRequest):
    """Process a single text input"""
    try:
        start_time = time.time()
        logger.info("Processing single text request")
        
        rewritten = await openai_service.rewrite_text_chunk(
            request.content,
            style=request.style
        )
        
        processing_time = time.time() - start_time
        
        return TextResponse(
            original=request.content,
            rewritten=rewritten,
            cleaned=rewritten,
            processing_time=processing_time
        )
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add new paragraph processing endpoint
@app.post("/process-paragraphs", response_model=ParagraphResponse)
async def process_paragraphs(request: ParagraphRequest):
    """Process text by paragraphs"""
    try:
        start_time = time.time()
        logger.info("Processing text by paragraphs")

        # Split text into paragraphs (split by double newline)
        paragraphs = [p.strip() for p in request.text.split("\n\n") if p.strip()]
        
        # Filter paragraphs by minimum length if specified
        paragraphs = [p for p in paragraphs if len(p) >= request.min_paragraph_length]

        results = []
        for paragraph in paragraphs:
            try:
                para_start_time = time.time()
                rewritten = await openai_service.rewrite_text_chunk(
                    paragraph,
                    style=request.style
                )
                
                results.append(TextResponse(
                    original=paragraph,
                    rewritten=rewritten,
                    cleaned=rewritten,
                    processing_time=time.time() - para_start_time
                ))
            except Exception as e:
                logger.error(f"Error processing paragraph: {e}")
                continue

        total_time = time.time() - start_time
        
        return ParagraphResponse(
            paragraphs=results,
            total_paragraphs=len(results),
            processing_time=total_time
        )
    except Exception as e:
        logger.error(f"Error in paragraph processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
