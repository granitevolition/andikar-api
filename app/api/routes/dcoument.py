import time
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from app.services.document_processor import DocumentProcessor
from app.services.openai_service import OpenAIService
from app.models.schemas import (
    ProcessingResponse, ProcessingStatus,
    TextRequest, TextResponse,
    BatchTextRequest, BatchTextResponse
)
import logging

router = APIRouter()
processor = DocumentProcessor()
openai_service = OpenAIService()


@router.post("/process", response_model=ProcessingResponse)
async def process_document(
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user_from_api_key)
):
    pass

@router.get("/status/{job_id}", response_model=ProcessingResponse)
async def get_processing_status(job_id: str):
    status = queue_service.get_job_status(job_id)
    result = queue_service.get_job_result(job_id)
    
    return ProcessingResponse(
        job_id=job_id,
        status=status,
        message="Processing status retrieved",
        files=result if status == ProcessingStatus.COMPLETED else None
    )


@router.post("/process-text", response_model=TextResponse)
async def process_text(request: TextRequest):
    """Process a single text input"""
    try:
        start_time = time.time()

        # Process the text
        rewritten = await openai_service.rewrite_text_chunk(
            request.content,
            style=request.style
        )

        # Clean the rewritten text
        cleaned = await processor.clean_text(rewritten, request.content)

        processing_time = time.time() - start_time

        return TextResponse(
            original=request.content,
            rewritten=rewritten,
            cleaned=cleaned,
            processing_time=processing_time
        )
    except Exception as e:
        logging.error(f"Error processing text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-text-batch", response_model=BatchTextResponse)
async def process_text_batch(request: BatchTextRequest):
    """Process multiple texts in a single request"""
    try:
        start_time = time.time()

        # Process all texts in parallel
        rewritten_texts = await openai_service.process_text_batch(
            request.texts,
            style=request.style
        )

        # Clean all texts
        cleaned_texts = await asyncio.gather(*[
            processor.clean_text(rewritten, original)
            for rewritten, original in zip(rewritten_texts, request.texts)
        ])

        total_time = time.time() - start_time

        results = [
            TextResponse(
                original=original,
                rewritten=rewritten,
                cleaned=cleaned,
                processing_time=total_time / len(request.texts)
            )
            for original, rewritten, cleaned in zip(
                request.texts,
                rewritten_texts,
                cleaned_texts
            )
        ]

        return BatchTextResponse(
            results=results,
            total_processing_time=total_time
        )
    except Exception as e:
        logging.error(f"Error processing text batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-paragraphs")
async def process_paragraphs(
        text: str = Body(..., description="Text to be split and processed by paragraph"),
        style: str = Body("scholar")
):
    """Process text by splitting into paragraphs first"""
    try:
        # Split into paragraphs
        paragraphs = [p for p in text.split("\n\n") if p.strip()]

        # Process each paragraph
        rewritten_paragraphs = await openai_service.process_text_batch(
            paragraphs,
            style=style
        )

        # Join processed paragraphs
        result = "\n\n".join(rewritten_paragraphs)

        return {"result": result}
    except Exception as e:
        logging.error(f"Error processing paragraphs: {e}")
        raise HTTPException(status_code=500, detail=str(e))