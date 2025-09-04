"""
Main API router for v1 endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    summarize, flashcards, quiz, keywords, 
    paraphrase, visual_qa, sessions, analytics
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(summarize.router, prefix="/summarize", tags=["summarization"])
api_router.include_router(flashcards.router, prefix="/flashcards", tags=["flashcards"])
api_router.include_router(quiz.router, prefix="/quiz", tags=["quiz"])
api_router.include_router(keywords.router, prefix="/keywords", tags=["keywords"])
api_router.include_router(paraphrase.router, prefix="/paraphrase", tags=["paraphrase"])
api_router.include_router(visual_qa.router, prefix="/visual-qa", tags=["visual-qa"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
