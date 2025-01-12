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

# Keep existing schema definitions
# [Previous schema definitions remain the same...]

# Add rate limiting implementation
class RateLimiter:
    def __init__(self, requests_per_minute: int = 10):
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

# [Keep existing endpoints...]
# Add rate limit info endpoint
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

[Your existing endpoints remain the same...]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
