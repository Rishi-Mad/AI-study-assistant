"""
Summarization API endpoints.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field, validator

from app.services.summarization_service import SummarizationService
from app.services.model_manager import ModelManager
from app.core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


class SummarizeRequest(BaseModel):
    """Request model for text summarization."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to summarize")
    min_length: int = Field(40, ge=10, le=200, description="Minimum summary length")
    max_length: int = Field(140, ge=20, le=500, description="Maximum summary length")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    
    @validator('max_length')
    def max_length_must_be_greater_than_min(cls, v, values):
        if 'min_length' in values and v <= values['min_length']:
            raise ValueError('max_length must be greater than min_length')
        return v


class SummarizeResponse(BaseModel):
    """Response model for text summarization."""
    summary: str = Field(..., description="Generated summary")
    metadata: dict = Field(..., description="Summary metadata")


def get_summarization_service(request: Request) -> SummarizationService:
    """Get summarization service from app state."""
    model_manager = request.app.state.model_manager
    return SummarizationService(model_manager)


@router.post("/", response_model=SummarizeResponse)
async def summarize_text(
    request_data: SummarizeRequest,
    service: SummarizationService = Depends(get_summarization_service),
    db: Session = Depends(get_db)
):
    """
    Summarize input text using AI model.
    
    - **text**: The text to summarize (1-5000 characters)
    - **min_length**: Minimum length of the summary (10-200 characters)
    - **max_length**: Maximum length of the summary (20-500 characters)
    - **session_id**: Optional session ID for tracking and analytics
    """
    try:
        result = await service.summarize_text(
            text=request_data.text,
            min_length=request_data.min_length,
            max_length=request_data.max_length,
            session_id=request_data.session_id
        )
        
        return SummarizeResponse(
            summary=result["summary"],
            metadata=result["metadata"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        raise HTTPException(status_code=500, detail="Summarization failed")


@router.post("/batch")
async def batch_summarize(
    texts: list[str],
    min_length: int = 40,
    max_length: int = 140,
    service: SummarizationService = Depends(get_summarization_service)
):
    """
    Summarize multiple texts in batch.
    
    - **texts**: List of texts to summarize
    - **min_length**: Minimum length of summaries
    - **max_length**: Maximum length of summaries
    """
    try:
        if len(texts) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 texts allowed per batch")
        
        results = await service.batch_summarize(texts, min_length, max_length)
        return {"results": results}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch summarization error: {e}")
        raise HTTPException(status_code=500, detail="Batch summarization failed")
