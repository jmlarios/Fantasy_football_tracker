import os
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from src.services.auth import auth_service
from src.models import User
from config import get_db
import logging

logger = logging.getLogger(__name__)


def get_session_secret() -> str:
    """Get session secret key from environment."""
    secret = os.getenv("SESSION_SECRET_KEY")
    if not secret:
        raise ValueError("SESSION_SECRET_KEY environment variable not set")
    return secret


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """
    Get current authenticated user from session.
    Returns None if not authenticated (for optional authentication).
    """
    # Check for user_id in session
    user_id = request.session.get("user_id")
    
    if not user_id:
        return None
    
    # Use the auth service to get user (avoiding duplication)
    user = auth_service.get_user_by_id(db, user_id)
    if not user:
        # Clear invalid session
        request.session.pop("user_id", None)
        return None
    
    return user


def require_authentication(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Dependency that requires user to be authenticated.
    Raises HTTPException if not authenticated.
    """
    user = get_current_user(request, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return user


def create_user_session(request: Request, user: User) -> None:
    """Create a user session."""
    request.session["user_id"] = user.id
    logger.info(f"Session created for user: {user.email}")


def destroy_user_session(request: Request) -> None:
    """Destroy user session."""
    request.session.pop("user_id", None)
    logger.info("Session destroyed")
    request.session.pop("user_id", None)
    logger.info("Session destroyed")
