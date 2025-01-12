from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessingResponse(BaseModel):
    job_id: str
    status: ProcessingStatus
    message: str
    files: Optional[Dict[str, str]] = None

class TextRequest(BaseModel):
    content: str = Field(..., description="Text content to be processed")
    style: Optional[str] = Field("scholar", description="Desired writing style")
    
class TextResponse(BaseModel):
    original: str
    rewritten: str
    cleaned: str
    processing_time: float

class BatchTextRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to process")
    style: Optional[str] = "scholar"

class BatchTextResponse(BaseModel):
    results: List[TextResponse]
    total_processing_time: float
