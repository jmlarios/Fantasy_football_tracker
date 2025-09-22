import sys
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import logging

# Adding src directory to path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

# Importing necessary modules from config and models
from config import get_db, test_database_connection, app_config
from src.models import User, Player, FantasyTeam

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=app_config.APP_NAME,
    version=app_config.VERSION,
    description="Fantasy Football Tracker - Track your fantasy team performance!",
    debug=app_config.DEBUG
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API requests/responses
class UserCreate(BaseModel):
    name: str
    email: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: Optional[str]
    
    class Config:
        from_attributes = True

class PlayerResponse(BaseModel):
    id: int
    name: str
    team: str
    position: str
    goals: int
    assists: int
    
    class Config:
        from_attributes = True

class HealthResponse(BaseModel):
    status: str
    message: str
    database_connected: bool

# Root endpoint
@app.get("/")
async def root():
    """Welcome endpoint."""
    return {
        "message": "Welcome to Fantasy Football Tracker API!",
        "version": app_config.VERSION,
        "docs": "/docs"
    }

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with database connectivity test."""
    db_connected = test_database_connection()
    
    if db_connected:
        return HealthResponse(
            status="healthy",
            message="API is running and database is connected",
            database_connected=True
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "message": "Database connection failed",
                "database_connected": False
            }
        )

# User endpoints
@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    try:
        # Check if email already exists
        if user.email and db.query(User).filter(User.email == user.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        db_user = User(name=user.name, email=user.email)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"Created user: {user.name}")
        return db_user
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@app.get("/users", response_model=List[UserResponse])
async def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all users with pagination."""
    try:
        users = db.query(User).offset(skip).limit(limit).all()
        return users
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

# Player endpoints
@app.get("/players", response_model=List[PlayerResponse])
async def get_players(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all players with pagination."""
    try:
        players = db.query(Player).offset(skip).limit(limit).all()
        return players
    except Exception as e:
        logger.error(f"Error fetching players: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch players"
        )

@app.get("/players/{player_id}", response_model=PlayerResponse)
async def get_player(player_id: int, db: Session = Depends(get_db)):
    """Get a specific player by ID."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    return player

# Database info endpoint (for testing)
@app.get("/database/info")
async def database_info(db: Session = Depends(get_db)):
    """Get database information and table counts."""
    try:
        info = {
            "users_count": db.query(User).count(),
            "players_count": db.query(Player).count(),
            "fantasy_teams_count": db.query(FantasyTeam).count(),
            "database_url": "postgresql://fantasy:***@db:5432/tracker"  # Hide password
        }
        return info
    except Exception as e:
        logger.error(f"Error fetching database info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch database information"
        )

# Run the app
if __name__ == "__main__":
    import uvicorn
    
    # Test database connection on startup
    logger.info("Starting Fantasy Football Tracker API...")
    if not test_database_connection():
        logger.error("Failed to connect to database on startup!")
        sys.exit(1)
    
    logger.info(f"Starting server on {app_config.HOST}:{app_config.PORT}")
    uvicorn.run(
        "app:app",
        host=app_config.HOST,
        port=app_config.PORT,
        reload=app_config.DEBUG
    )
