"""
Flashcard API endpoints.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field, validator

from app.services.flashcard_service import FlashcardService
from app.services.model_manager import ModelManager
from app.core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


class FlashcardRequest(BaseModel):
    """Request model for flashcard generation."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to generate flashcards from")
    max_cards: int = Field(10, ge=1, le=50, description="Maximum number of flashcards to generate")
    difficulty_level: str = Field("medium", description="Difficulty level: easy, medium, hard")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    
    @validator('difficulty_level')
    def validate_difficulty_level(cls, v):
        if v not in ['easy', 'medium', 'hard']:
            raise ValueError('difficulty_level must be easy, medium, or hard')
        return v


class Flashcard(BaseModel):
    """Flashcard model."""
    term: str = Field(..., description="Flashcard term")
    definition: str = Field(..., description="Flashcard definition")
    type: str = Field(..., description="Type of flashcard (entity, definition, concept)")
    difficulty: int = Field(..., ge=1, le=5, description="Difficulty level (1-5)")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score (0.0-1.0)")


class FlashcardResponse(BaseModel):
    """Response model for flashcard generation."""
    count: int = Field(..., description="Number of flashcards generated")
    cards: List[Flashcard] = Field(..., description="Generated flashcards")
    metadata: dict = Field(..., description="Generation metadata")


class FlashcardReviewRequest(BaseModel):
    """Request model for flashcard review."""
    session_id: str = Field(..., description="Session ID")
    term: str = Field(..., description="Flashcard term")
    is_correct: bool = Field(..., description="Whether the answer was correct")
    response_time: float = Field(0.0, ge=0.0, description="Response time in seconds")


def get_flashcard_service(request: Request) -> FlashcardService:
    """Get flashcard service from app state."""
    model_manager = request.app.state.model_manager
    return FlashcardService(model_manager)


@router.post("/", response_model=FlashcardResponse)
async def generate_flashcards(
    request_data: FlashcardRequest,
    service: FlashcardService = Depends(get_flashcard_service),
    db: Session = Depends(get_db)
):
    """
    Generate flashcards from input text.
    
    - **text**: The text to generate flashcards from (1-5000 characters)
    - **max_cards**: Maximum number of flashcards to generate (1-50)
    - **difficulty_level**: Difficulty level (easy, medium, hard)
    - **session_id**: Optional session ID for tracking and analytics
    """
    try:
        result = await service.generate_flashcards(
            text=request_data.text,
            max_cards=request_data.max_cards,
            difficulty_level=request_data.difficulty_level,
            session_id=request_data.session_id
        )
        
        return FlashcardResponse(
            count=result["count"],
            cards=result["cards"],
            metadata=result["metadata"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Flashcard generation error: {e}")
        raise HTTPException(status_code=500, detail="Flashcard generation failed")


@router.post("/review")
async def review_flashcard(
    request_data: FlashcardReviewRequest,
    db: Session = Depends(get_db)
):
    """
    Record flashcard review performance for adaptive learning.
    
    - **session_id**: Session ID
    - **term**: Flashcard term
    - **is_correct**: Whether the answer was correct
    - **response_time**: Response time in seconds
    """
    try:
        # TODO: Implement flashcard review tracking
        # This would update the performance database and return recommendations
        
        return {
            "performance_updated": True,
            "next_recommendations": [],
            "current_performance": {}
        }
        
    except Exception as e:
        logger.error(f"Flashcard review error: {e}")
        raise HTTPException(status_code=500, detail="Flashcard review failed")


@router.get("/performance/{session_id}")
async def get_flashcard_performance(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get flashcard performance analytics for a session.
    
    - **session_id**: Session ID to get performance for
    """
    try:
        # TODO: Implement performance analytics
        return {
            "session_id": session_id,
            "total_cards": 0,
            "correct_answers": 0,
            "accuracy_rate": 0.0,
            "difficulty_progression": 0.0
        }
        
    except Exception as e:
        logger.error(f"Performance analytics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance analytics")
