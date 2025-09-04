"""
Keywords API endpoints.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from app.services.keywords_service import KeywordsService
from app.services.model_manager import ModelManager
from app.core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


class KeywordsRequest(BaseModel):
    """Request model for keyword extraction."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to extract keywords from")
    top_k: int = Field(10, ge=1, le=50, description="Number of top keywords to extract")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")


class KeywordsResponse(BaseModel):
    """Response model for keyword extraction."""
    count: int = Field(..., description="Number of keywords extracted")
    keywords: List[str] = Field(..., description="Extracted keywords")
    metadata: dict = Field(..., description="Extraction metadata")


def get_keywords_service(request: Request) -> KeywordsService:
    """Get keywords service from app state."""
    model_manager = request.app.state.model_manager
    return KeywordsService(model_manager)


@router.post("/", response_model=KeywordsResponse)
async def extract_keywords(
    request_data: KeywordsRequest,
    service: KeywordsService = Depends(get_keywords_service),
    db: Session = Depends(get_db)
):
    """
    Extract keywords from input text.
    
    - **text**: The text to extract keywords from (1-5000 characters)
    - **top_k**: Number of top keywords to extract (1-50)
    - **session_id**: Optional session ID for tracking and analytics
    """
    try:
        result = await service.extract_keywords(
            text=request_data.text,
            top_k=request_data.top_k,
            session_id=request_data.session_id
        )
        
        return KeywordsResponse(
            count=result["count"],
            keywords=result["keywords"],
            metadata=result["metadata"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Keyword extraction error: {e}")
        raise HTTPException(status_code=500, detail="Keyword extraction failed")
