from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
import time
from typing import List, Optional
from pydantic import BaseModel
from app.core.config import settings
from app.core.logging import setup_logging
from app.services.openai_service import OpenAIService
import asyncio
from datetime import datetime, timedelta

# Schema definitions
class TextRequest(BaseModel):
    content: str
    style: Optional[str] = "scholar"

class TextResponse(BaseModel):
    original: str
    rewritten: str
    cleaned: str
    processing_time: float

class ParagraphRequest(BaseModel):
    text: str
    style: Optional[str] = "scholar"
    min_paragraph_length: Optional[int] = 100

class ParagraphResponse(BaseModel):
    paragraphs: List[TextResponse]
    total_paragraphs: int
    processing_time: float

# Rate limiter as a dependency
class RateLimiter:
    def __init__(self):
        self.requests = {}
        self.CALLS = 10
        self.RATE_TIME = 60  # 1 minute

    async def is_rate_limited(self, request: Request) -> bool:
        client_ip = request.client.host
        now = time.time()
        
        # Initialize or get client's request history
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Clean old requests
        self.requests[client_ip] = [req_time for req_time in self.requests[client_ip] 
                                  if now - req_time < self.RATE_TIME]
        
        # Check if rate limit is exceeded
        if len(self.requests[client_ip]) >= self.CALLS:
            return True
            
        self.requests[client_ip].append(now)
        return False

limiter = RateLimiter()

async def rate_limit(request: Request):
    if await limiter.is_rate_limited(request):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again in a minute."
        )

# Initialize services
setup_logging()
logger = logging.getLogger(__name__)
openai_service = OpenAIService()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/rate-limit-status")
async def rate_limit_status(request: Request):
    """Get current rate limit status"""
    client_ip = request.client.host
    now = time.time()
    
    if client_ip not in limiter.requests:
        return {
            "requests_in_last_minute": 0,
            "max_requests_per_minute": limiter.CALLS,
            "remaining_requests": limiter.CALLS
        }
    
    # Clean and count recent requests
    recent_requests = [req_time for req_time in limiter.requests[client_ip] 
                      if now - req_time < limiter.RATE_TIME]
    
    return {
        "requests_in_last_minute": len(recent_requests),
        "max_requests_per_minute": limiter.CALLS,
        "remaining_requests": max(0, limiter.CALLS - len(recent_requests))
    }

@app.post("/process-text", response_model=TextResponse, dependencies=[Depends(rate_limit)])
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

@app.post("/process-paragraphs", response_model=ParagraphResponse, dependencies=[Depends(rate_limit)])
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
