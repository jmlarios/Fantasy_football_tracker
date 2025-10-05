import bcrypt
import os
from typing import Optional
from sqlalchemy.orm import Session
from src.models import User
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service for user management and password handling."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    def create_user(db: Session, name: str, email: str, password: str) -> User:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("Email already registered")
        
        # Hash password
        password_hash = AuthService.hash_password(password)
        
        # Create user
        user = User(
            name=name,
            email=email,
            password_hash=password_hash
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        user = db.query(User).filter(User.email == email, User.is_active == True).first()
        
        if not user:
            return None
        
        if not AuthService.verify_password(password, user.password_hash):
            return None
        
        return user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id, User.is_active == True).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email, User.is_active == True).first()


# Global auth service instance
auth_service = AuthService()
