import sys
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import logging

# Adding src directory to path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

# Importing necessary modules
from config import get_db, test_database_connection, app_config
from src.models import User, Player, FantasyTeam, Matchday
from src.services.auth import auth_service
from src.services.fantasy_team import fantasy_team_service
from src.middleware.session import (
    get_current_user, 
    require_authentication, 
    create_user_session, 
    destroy_user_session,
    get_session_secret
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=app_config.APP_NAME,
    version=app_config.VERSION,
    description="LaLiga Fantasy Football Tracker - Track your LaLiga fantasy team performance!",
    debug=app_config.DEBUG
)

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=get_session_secret())

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API requests/responses
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    
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

# New fantasy team models
class FantasyTeamCreate(BaseModel):
    name: str

class FantasyTeamResponse(BaseModel):
    id: int
    name: str
    total_points: float
    max_players: int
    
    class Config:
        from_attributes = True

class TeamPlayerResponse(BaseModel):
    id: int
    name: str
    team: str
    position: str
    is_captain: bool
    is_vice_captain: bool
    position_in_team: str

class FantasyTeamDetailResponse(BaseModel):
    team: FantasyTeamResponse
    players: List[TeamPlayerResponse]
    player_count: int

class AddPlayerRequest(BaseModel):
    player_id: int

class SetCaptainRequest(BaseModel):
    player_id: int
    is_vice: bool = False

class HealthResponse(BaseModel):
    status: str
    message: str
    database_connected: bool

class AuthResponse(BaseModel):
    message: str
    user: UserResponse

class MatchdayResponse(BaseModel):
    id: int
    matchday_number: int
    season: str
    start_date: str
    end_date: str
    deadline: str
    is_active: bool
    is_finished: bool
    points_calculated: bool
    is_transfer_locked: bool
    time_until_deadline: Optional[str]
    
    class Config:
        from_attributes = True

# Root endpoint
@app.get("/")
async def root():
    """Welcome endpoint."""
    return {
        "message": "Welcome to LaLiga Fantasy Football Tracker API!",
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

# Authentication endpoints
@app.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: Request, user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    try:
        # Use auth service to create user (no duplication)
        user = auth_service.create_user(
            db=db,
            name=user_data.name,
            email=user_data.email,
            password=user_data.password
        )
        
        # Create session using session middleware
        create_user_session(request, user)
        
        return AuthResponse(
            message="User registered successfully",
            user=UserResponse.model_validate(user)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@app.post("/auth/login", response_model=AuthResponse)
async def login(request: Request, login_data: UserLogin, db: Session = Depends(get_db)):
    """Login user."""
    # Use auth service to authenticate (no duplication)
    user = auth_service.authenticate_user(
        db=db,
        email=login_data.email,
        password=login_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create session using session middleware
    create_user_session(request, user)
    
    return AuthResponse(
        message="Login successful",
        user=UserResponse.model_validate(user)
    )

@app.post("/auth/logout")
async def logout(request: Request):
    """Logout user."""
    destroy_user_session(request)
    return {"message": "Logout successful"}

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(require_authentication)):
    """Get current user information."""
    return UserResponse.model_validate(current_user)

# User endpoints (updated to require authentication for modifications)
@app.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authentication)
):
    """Get all users (authenticated users only)."""
    try:
        users = db.query(User).offset(skip).limit(limit).all()
        return [UserResponse.model_validate(user) for user in users]
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authentication)
):
    """Get a specific user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.model_validate(user)

# Player endpoints (public access for viewing)
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

# Fantasy Team endpoints
@app.post("/fantasy-teams", response_model=FantasyTeamResponse, status_code=status.HTTP_201_CREATED)
async def create_fantasy_team(
    team_data: FantasyTeamCreate,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Create a new fantasy team."""
    try:
        team = fantasy_team_service.create_fantasy_team(
            db=db,
            user_id=current_user.id,
            team_name=team_data.name
        )
        return FantasyTeamResponse.model_validate(team)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating fantasy team: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create fantasy team"
        )

@app.get("/fantasy-teams", response_model=List[FantasyTeamResponse])
async def get_user_fantasy_teams(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Get all fantasy teams for the current user."""
    try:
        teams = fantasy_team_service.get_user_teams(db=db, user_id=current_user.id)
        return [FantasyTeamResponse.model_validate(team) for team in teams]
    except Exception as e:
        logger.error(f"Error fetching fantasy teams: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch fantasy teams"
        )

@app.get("/fantasy-teams/{team_id}", response_model=FantasyTeamDetailResponse)
async def get_fantasy_team_detail(
    team_id: int,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Get detailed fantasy team information including players."""
    try:
        team_data = fantasy_team_service.get_team_with_players(
            db=db,
            team_id=team_id,
            user_id=current_user.id
        )
        
        if not team_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fantasy team not found"
            )
        
        return FantasyTeamDetailResponse(
            team=FantasyTeamResponse.model_validate(team_data['team']),
            players=[TeamPlayerResponse(**player) for player in team_data['players']],
            player_count=team_data['player_count']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching fantasy team detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch fantasy team details"
        )

@app.post("/fantasy-teams/{team_id}/players")
async def add_player_to_team(
    team_id: int,
    player_data: AddPlayerRequest,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Add a player to a fantasy team."""
    try:
        fantasy_team_service.add_player_to_team(
            db=db,
            team_id=team_id,
            player_id=player_data.player_id,
            user_id=current_user.id
        )
        return {"message": "Player added to team successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding player to team: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add player to team"
        )

@app.delete("/fantasy-teams/{team_id}/players/{player_id}")
async def remove_player_from_team(
    team_id: int,
    player_id: int,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Remove a player from a fantasy team."""
    try:
        fantasy_team_service.remove_player_from_team(
            db=db,
            team_id=team_id,
            player_id=player_id,
            user_id=current_user.id
        )
        return {"message": "Player removed from team successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error removing player from team: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove player from team"
        )

@app.post("/fantasy-teams/{team_id}/captain")
async def set_team_captain(
    team_id: int,
    captain_data: SetCaptainRequest,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Set a player as captain or vice-captain."""
    try:
        fantasy_team_service.set_captain(
            db=db,
            team_id=team_id,
            player_id=captain_data.player_id,
            user_id=current_user.id,
            is_vice=captain_data.is_vice
        )
        
        role = "vice-captain" if captain_data.is_vice else "captain"
        return {"message": f"Player set as {role} successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error setting captain: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set captain"
        )

@app.get("/fantasy-teams/{team_id}/validate")
async def validate_team_formation(
    team_id: int,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Validate fantasy team formation."""
    try:
        # Verify team ownership
        team = db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == current_user.id
        ).first()
        
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fantasy team not found"
            )
        
        validation_result = fantasy_team_service.validate_team_formation(db=db, team_id=team_id)
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating team formation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate team formation"
        )

# Enhanced player search endpoint
@app.get("/players/search")
async def search_players(
    q: Optional[str] = None,
    team: Optional[str] = None,
    position: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Search players with filters for team building."""
    try:
        query = db.query(Player).filter(Player.is_active == True)
        
        if q:
            query = query.filter(Player.name.ilike(f"%{q}%"))
        if team:
            query = query.filter(Player.team == team)
        if position:
            query = query.filter(Player.position == position)
        
        players = query.offset(skip).limit(limit).all()
        return players
        
    except Exception as e:
        logger.error(f"Error searching players: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search players"
        )

@app.get("/teams")
async def get_laliga_teams(db: Session = Depends(get_db)):
    """Get all LaLiga teams for team building."""
    try:
        teams = db.query(Player.team).distinct().order_by(Player.team).all()
        return [{"name": team[0]} for team in teams]
    except Exception as e:
        logger.error(f"Error fetching teams: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch teams"
        )

# Matchday endpoints
@app.get("/matchdays", response_model=List[MatchdayResponse])
async def get_all_matchdays(db: Session = Depends(get_db)):
    """Get all matchdays for the current season."""
    try:
        matchdays = db.query(Matchday).order_by(Matchday.matchday_number).all()
        
        response_data = []
        for md in matchdays:
            response_data.append(MatchdayResponse(
                id=md.id,
                matchday_number=md.matchday_number,
                season=md.season,
                start_date=md.start_date.isoformat(),
                end_date=md.end_date.isoformat(),
                deadline=md.deadline.isoformat(),
                is_active=md.is_active,
                is_finished=md.is_finished,
                points_calculated=md.points_calculated,
                is_transfer_locked=md.is_transfer_locked,
                time_until_deadline=md.time_until_deadline
            ))
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error fetching matchdays: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch matchdays"
        )

@app.get("/matchdays/current", response_model=MatchdayResponse)
async def get_current_matchday(db: Session = Depends(get_db)):
    """Get the currently active matchday."""
    try:
        current_matchday = db.query(Matchday).filter(Matchday.is_active == True).first()
        
        if not current_matchday:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active matchday found"
            )
        
        return MatchdayResponse(
            id=current_matchday.id,
            matchday_number=current_matchday.matchday_number,
            season=current_matchday.season,
            start_date=current_matchday.start_date.isoformat(),
            end_date=current_matchday.end_date.isoformat(),
            deadline=current_matchday.deadline.isoformat(),
            is_active=current_matchday.is_active,
            is_finished=current_matchday.is_finished,
            points_calculated=current_matchday.points_calculated,
            is_transfer_locked=current_matchday.is_transfer_locked,
            time_until_deadline=current_matchday.time_until_deadline
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching current matchday: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch current matchday"
        )

@app.get("/matchdays/next", response_model=MatchdayResponse)
async def get_next_matchday(db: Session = Depends(get_db)):
    """Get the next upcoming matchday."""
    try:
        next_matchday = db.query(Matchday).filter(
            Matchday.is_finished == False,
            Matchday.is_active == False
        ).order_by(Matchday.start_date.asc()).first()
        
        if not next_matchday:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No upcoming matchday found"
            )
        
        return MatchdayResponse(
            id=next_matchday.id,
            matchday_number=next_matchday.matchday_number,
            season=next_matchday.season,
            start_date=next_matchday.start_date.isoformat(),
            end_date=next_matchday.end_date.isoformat(),
            deadline=next_matchday.deadline.isoformat(),
            is_active=next_matchday.is_active,
            is_finished=next_matchday.is_finished,
            points_calculated=next_matchday.points_calculated,
            is_transfer_locked=next_matchday.is_transfer_locked,
            time_until_deadline=next_matchday.time_until_deadline
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching next matchday: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch next matchday"
        )

@app.get("/matchdays/{matchday_number}", response_model=MatchdayResponse)
async def get_matchday_by_number(matchday_number: int, db: Session = Depends(get_db)):
    """Get a specific matchday by number."""
    try:
        matchday = db.query(Matchday).filter(Matchday.matchday_number == matchday_number).first()
        
        if not matchday:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Matchday {matchday_number} not found"
            )
        
        return MatchdayResponse(
            id=matchday.id,
            matchday_number=matchday.matchday_number,
            season=matchday.season,
            start_date=matchday.start_date.isoformat(),
            end_date=matchday.end_date.isoformat(),
            deadline=matchday.deadline.isoformat(),
            is_active=matchday.is_active,
            is_finished=matchday.is_finished,
            points_calculated=matchday.points_calculated,
            is_transfer_locked=matchday.is_transfer_locked,
            time_until_deadline=matchday.time_until_deadline
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching matchday {matchday_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch matchday"
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
