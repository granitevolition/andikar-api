from collections import deque
from typing import Dict, Any
import asyncio
import uuid
from app.models.schemas import ProcessingStatus

class QueueService:
    def __init__(self):
        self.queue = deque()
        self.results: Dict[str, Any] = {}
        self.status: Dict[str, ProcessingStatus] = {}

    async def add_job(self, content: bytes, filename: str) -> str:
        job_id = str(uuid.uuid4())
        self.queue.append((job_id, content, filename))
        self.status[job_id] = ProcessingStatus.PENDING
        return job_id

    def get_job_status(self, job_id: str) -> ProcessingStatus:
        return self.status.get(job_id, ProcessingStatus.FAILED)

    def set_job_result(self, job_id: str, result: Any) -> None:
        self.results[job_id] = result
        self.status[job_id] = ProcessingStatus.COMPLETED

    def get_job_result(self, job_id: str) -> Any:
        return self.results.get(job_id)