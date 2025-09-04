"""
Quiz API endpoints.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from app.services.quiz_service import QuizService
from app.services.model_manager import ModelManager
from app.core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


class QuizRequest(BaseModel):
    """Request model for quiz generation."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to generate quiz from")
    max_qs: int = Field(5, ge=1, le=20, description="Maximum number of questions to generate")
    difficulty_level: str = Field("medium", description="Difficulty level: easy, medium, hard")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")


class QuizQuestion(BaseModel):
    """Quiz question model."""
    question: str = Field(..., description="Question text")
    options: List[str] = Field(..., description="Answer options")
    correct_answer: str = Field(..., description="Correct answer")
    explanation: str = Field(..., description="Explanation for the answer")
    difficulty: int = Field(..., ge=1, le=5, description="Difficulty level (1-5)")


class QuizResponse(BaseModel):
    """Response model for quiz generation."""
    count: int = Field(..., description="Number of questions generated")
    questions: List[QuizQuestion] = Field(..., description="Generated quiz questions")
    metadata: dict = Field(..., description="Generation metadata")


def get_quiz_service(request: Request) -> QuizService:
    """Get quiz service from app state."""
    model_manager = request.app.state.model_manager
    return QuizService(model_manager)


@router.post("/", response_model=QuizResponse)
async def generate_quiz(
    request_data: QuizRequest,
    service: QuizService = Depends(get_quiz_service),
    db: Session = Depends(get_db)
):
    """
    Generate quiz questions from input text.
    
    - **text**: The text to generate quiz from (1-5000 characters)
    - **max_qs**: Maximum number of questions to generate (1-20)
    - **difficulty_level**: Difficulty level (easy, medium, hard)
    - **session_id**: Optional session ID for tracking and analytics
    """
    try:
        result = await service.generate_quiz(
            text=request_data.text,
            max_questions=request_data.max_qs,
            difficulty_level=request_data.difficulty_level,
            session_id=request_data.session_id
        )
        
        return QuizResponse(
            count=result["count"],
            questions=result["questions"],
            metadata=result["metadata"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Quiz generation error: {e}")
        raise HTTPException(status_code=500, detail="Quiz generation failed")
