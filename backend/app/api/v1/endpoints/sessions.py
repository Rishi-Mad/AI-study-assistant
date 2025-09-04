"""
Session management API endpoints.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.user import UserSession
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


class SessionCreateRequest(BaseModel):
    """Request model for creating a session."""
    user_id: Optional[str] = Field(None, description="Optional user ID")


class SessionResponse(BaseModel):
    """Response model for session operations."""
    session_id: str = Field(..., description="Session ID")
    created_at: datetime = Field(..., description="Session creation timestamp")
    user_id: Optional[str] = Field(None, description="Associated user ID")


@router.post("/create", response_model=SessionResponse)
async def create_session(
    request_data: SessionCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new study session.
    
    - **user_id**: Optional user ID to associate with the session
    """
    try:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Create session in database
        session = UserSession(
            id=session_id,
            user_id=request_data.user_id,
            created_at=now,
            last_activity=now,
            session_data="{}",
            is_active=True
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return SessionResponse(
            session_id=session_id,
            created_at=now,
            user_id=request_data.user_id
        )
        
    except Exception as e:
        logger.error(f"Session creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get session information.
    
    - **session_id**: Session ID to retrieve
    """
    try:
        session = db.query(UserSession).filter(
            UserSession.id == session_id,
            UserSession.is_active == True
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            session_id=session.id,
            created_at=session.created_at,
            user_id=session.user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session")


@router.delete("/{session_id}")
async def end_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    End a study session.
    
    - **session_id**: Session ID to end
    """
    try:
        session = db.query(UserSession).filter(
            UserSession.id == session_id,
            UserSession.is_active == True
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.is_active = False
        db.commit()
        
        return {"message": "Session ended successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session ending error: {e}")
        raise HTTPException(status_code=500, detail="Failed to end session")
