"""
Paraphrase API endpoints.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from app.services.paraphrase_service import ParaphraseService
from app.services.model_manager import ModelManager
from app.core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


class ParaphraseRequest(BaseModel):
    """Request model for text paraphrasing."""
    text: str = Field(..., min_length=1, max_length=1000, description="Text to paraphrase")
    max_length: int = Field(128, ge=16, le=512, description="Maximum length of paraphrased text")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")


class ParaphraseResponse(BaseModel):
    """Response model for text paraphrasing."""
    paraphrase: str = Field(..., description="Paraphrased text")
    metadata: dict = Field(..., description="Paraphrasing metadata")


def get_paraphrase_service(request: Request) -> ParaphraseService:
    """Get paraphrase service from app state."""
    model_manager = request.app.state.model_manager
    return ParaphraseService(model_manager)


@router.post("/", response_model=ParaphraseResponse)
async def paraphrase_text(
    request_data: ParaphraseRequest,
    service: ParaphraseService = Depends(get_paraphrase_service),
    db: Session = Depends(get_db)
):
    """
    Paraphrase input text using AI model.
    
    - **text**: The text to paraphrase (1-1000 characters)
    - **max_length**: Maximum length of paraphrased text (16-512 characters)
    - **session_id**: Optional session ID for tracking and analytics
    """
    try:
        result = await service.paraphrase_text(
            text=request_data.text,
            max_length=request_data.max_length,
            session_id=request_data.session_id
        )
        
        return ParaphraseResponse(
            paraphrase=result["paraphrase"],
            metadata=result["metadata"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Paraphrasing error: {e}")
        raise HTTPException(status_code=500, detail="Paraphrasing failed")
