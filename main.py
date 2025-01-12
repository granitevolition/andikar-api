from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
import time
from typing import List, Optional
from pydantic import BaseModel
from app.core.config import settings
from app.core.logging import setup_logging
from app.services.openai_service import OpenAIService
from fastapi.middleware.base import BaseHTTPMiddleware
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

# Add rate limiting implementation
class RateLimiter:
    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.requests = {}

    async def check_rate_limit(self, client_ip: str) -> bool:
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)

        # Clean old requests
        self.requests = {k: v for k, v in self.requests.items() 
                        if v[-1] > minute_ago}

        # Get or create client requests list
        client_requests = self.requests.get(client_ip, [])
        client_requests = [t for t in client_requests if t > minute_ago]

        # Check rate limit
        if len(client_requests) >= self.requests_per_minute:
            return False

        # Add new request
        client_requests.append(now)
        self.requests[client_ip] = client_requests
        return True

rate_limiter = RateLimiter()

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        if not await rate_limiter.check_rate_limit(client_ip):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again in a minute."
            )
        return await call_next(request)

# Initialize services
setup_logging()
logger = logging.getLogger(__name__)
openai_service = OpenAIService()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

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
    now = datetime.now()
    minute_ago = now - timedelta(minutes=1)
    
    # Get recent requests
    client_requests = rate_limiter.requests.get(client_ip, [])
    recent_requests = len([t for t in client_requests if t > minute_ago])
    
    return {
        "requests_in_last_minute": recent_requests,
        "max_requests_per_minute": rate_limiter.requests_per_minute,
        "remaining_requests": max(0, rate_limiter.requests_per_minute - recent_requests)
    }

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
