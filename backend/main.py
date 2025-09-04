"""
AI Study Assistant - FastAPI Backend
A comprehensive study assistant with AI-powered features for learning and retention.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.core.database import init_db, get_db
from app.api.v1.api import api_router
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting AI Study Assistant API...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized successfully")
    
    # Load AI models
    from app.services.model_manager import ModelManager
    model_manager = ModelManager()
    await model_manager.load_models()
    app.state.model_manager = model_manager
    logger.info("AI models loaded successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Study Assistant API...")
    if hasattr(app.state, 'model_manager'):
        await app.state.model_manager.cleanup()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="AI Study Assistant API",
    description="A comprehensive AI-powered study assistant with summarization, flashcards, quizzes, and adaptive learning",
    version="2.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with API information."""
    return {
        "message": "AI Study Assistant API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs" if settings.ENVIRONMENT != "production" else "disabled",
        "features": [
            "Text Summarization",
            "Flashcard Generation", 
            "Quiz Creation",
            "Keyword Extraction",
            "Text Paraphrasing",
            "Visual Question Answering",
            "Adaptive Learning",
            "Performance Analytics"
        ]
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "connected"
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler for unexpected errors."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "path": str(request.url)
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )
