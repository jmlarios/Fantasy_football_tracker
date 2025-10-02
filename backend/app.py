import sys
import os
from pathlib import Path
from typing import List, Optional, Dict
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
from src.models import User, Player, FantasyTeam, FantasyTeamPlayer, Matchday, FantasyLeagueParticipant
from src.services.auth import auth_service
from src.services import transfer_service
from src.services.league_service import league_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Session functions
def get_session_secret() -> str:
    return os.getenv("SESSION_SECRET_KEY", "your-super-secret-session-key-change-this-in-production")

def require_authentication(request: Request, db: Session = Depends(get_db)) -> User:
    """Require user authentication."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    user = auth_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )
    return user

# Create FastAPI app
app = FastAPI(
    title=app_config.APP_NAME,
    version=app_config.VERSION,
    description="LaLiga Fantasy Football Tracker",
    debug=app_config.DEBUG
)

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=get_session_secret())

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
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

class AuthResponse(BaseModel):
    message: str
    user: UserResponse

class PlayerResponse(BaseModel):
    id: int
    name: str
    team: str
    position: str
    goals: int
    assists: int
    price: float
    is_active: bool
    
    class Config:
        from_attributes = True

class FantasyTeamCreate(BaseModel):
    name: str

class FantasyTeamResponse(BaseModel):
    id: int
    name: str
    total_points: float
    max_players: int
    total_budget: float
    
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
    price: Optional[float] = None

class FantasyTeamDetailResponse(BaseModel):
    team: FantasyTeamResponse
    players: List[TeamPlayerResponse]
    player_count: int

class AddPlayerRequest(BaseModel):
    player_id: int

class SetCaptainRequest(BaseModel):
    player_id: int
    is_vice: bool = False

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
    time_until_deadline: Optional[str] = None

class TransferRequest(BaseModel):
    player_in_id: int
    player_out_id: int

class TransferStatusResponse(BaseModel):
    available_budget: float
    used_budget: float
    remaining_transfers: int
    status: str

class TransferValidationResponse(BaseModel):
    valid: bool
    message: str

class LeagueCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    is_private: bool = False
    max_participants: int = 20

class LeagueJoinRequest(BaseModel):
    join_code: str

class LeagueUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_participants: Optional[int] = None

class LeagueResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_private: bool
    is_creator: bool
    participants: int
    max_participants: int
    created_at: str
    join_code: Optional[str] = None

class LeagueJoinResponse(BaseModel):
    league_id: int
    league_name: str
    team_id: int
    team_name: str
    participants: int

class LeaderboardEntry(BaseModel):
    user_id: int
    user_name: str
    team_id: int
    team_name: str
    total_points: float
    rank: int
    is_current_user: bool

class LeaderboardResponse(BaseModel):
    league: Dict
    leaderboard: List[LeaderboardEntry]
    user_rank: Optional[int]

# Basic fantasy team service
class BasicFantasyTeamService:
    @staticmethod
    def create_fantasy_team(db: Session, user_id: int, team_name: str):
        existing_team = db.query(FantasyTeam).filter(
            FantasyTeam.user_id == user_id,
            FantasyTeam.name == team_name
        ).first()
        
        if existing_team:
            raise ValueError("Team name already exists")
        
        team = FantasyTeam(
            user_id=user_id,
            name=team_name,
            total_points=0.0,
            total_budget=100000000.0,
            max_players=15
        )
        db.add(team)
        db.commit()
        db.refresh(team)
        return team
    
    @staticmethod
    def get_user_teams(db: Session, user_id: int):
        return db.query(FantasyTeam).filter(FantasyTeam.user_id == user_id).all()
    
    @staticmethod
    def get_team_with_players(db: Session, team_id: int, user_id: int):
        team = db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == user_id
        ).first()
        
        if not team:
            return None
        
        team_players = db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == team_id
        ).all()
        
        players_data = []
        for tp in team_players:
            player = db.query(Player).filter(Player.id == tp.player_id).first()
            if player:
                players_data.append({
                    'id': player.id,
                    'name': player.name,
                    'team': player.team,
                    'position': player.position,
                    'is_captain': tp.is_captain,
                    'is_vice_captain': tp.is_vice_captain,
                    'position_in_team': tp.position_in_team,
                    'price': player.price
                })
        
        return {
            'team': team,
            'players': players_data,
            'player_count': len(players_data)
        }
    
    @staticmethod
    def add_player_to_team(db: Session, team_id: int, player_id: int, user_id: int):
        """Add a player to a fantasy team."""
        # Verify team ownership
        team = db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == user_id
        ).first()
        
        if not team:
            raise ValueError("Team not found")
        
        # Check if player exists
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            raise ValueError("Player not found")
        
        # Check if player already in team
        existing = db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == team_id,
            FantasyTeamPlayer.player_id == player_id
        ).first()
        
        if existing:
            raise ValueError("Player already in team")
        
        # Check team size limit
        current_count = db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == team_id
        ).count()
        
        if current_count >= team.max_players:
            raise ValueError(f"Team is full (max {team.max_players} players)")
        
        # Add player to team
        team_player = FantasyTeamPlayer(
            fantasy_team_id=team_id,
            player_id=player_id,
            position_in_team=player.position,
            is_captain=False,
            is_vice_captain=False
        )
        
        db.add(team_player)
        db.commit()
        
        logger.info(f"Added player {player.name} to team {team.name}")
    
    @staticmethod
    def remove_player_from_team(db: Session, team_id: int, player_id: int, user_id: int):
        """Remove a player from a fantasy team."""
        # Verify team ownership
        team = db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == user_id
        ).first()
        
        if not team:
            raise ValueError("Team not found")
        
        # Find and remove player
        team_player = db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == team_id,
            FantasyTeamPlayer.player_id == player_id
        ).first()
        
        if not team_player:
            raise ValueError("Player not in team")
        
        db.delete(team_player)
        db.commit()
        
        logger.info(f"Removed player {player_id} from team {team.name}")
    
    @staticmethod
    def set_captain(db: Session, team_id: int, player_id: int, user_id: int, is_vice: bool = False):
        """Set a player as captain or vice-captain."""
        # Verify team ownership
        team = db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == user_id
        ).first()
        
        if not team:
            raise ValueError("Team not found")
        
        # Check if player is in team
        team_player = db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == team_id,
            FantasyTeamPlayer.player_id == player_id
        ).first()
        
        if not team_player:
            raise ValueError("Player not in team")
        
        if is_vice:
            # Clear current vice-captain
            db.query(FantasyTeamPlayer).filter(
                FantasyTeamPlayer.fantasy_team_id == team_id,
                FantasyTeamPlayer.is_vice_captain == True
            ).update({'is_vice_captain': False})
            
            # Set new vice-captain
            team_player.is_vice_captain = True
            team_player.is_captain = False
        else:
            # Clear current captain and vice-captain
            db.query(FantasyTeamPlayer).filter(
                FantasyTeamPlayer.fantasy_team_id == team_id
            ).update({'is_captain': False, 'is_vice_captain': False})
            
            # Set new captain
            team_player.is_captain = True
            team_player.is_vice_captain = False
        
        db.commit()
        
        role = "vice-captain" if is_vice else "captain"
        logger.info(f"Set player {player_id} as {role} for team {team.name}")

fantasy_team_service = BasicFantasyTeamService()

# Endpoints
@app.get("/")
async def root():
    return {
        "message": "Welcome to LaLiga Fantasy Football Tracker API!",
        "version": app_config.VERSION,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    db_connected = test_database_connection()
    return {
        "status": "healthy" if db_connected else "unhealthy",
        "database_connected": db_connected
    }

@app.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: Request, user_data: UserRegister, db: Session = Depends(get_db)):
    try:
        user = auth_service.create_user(
            db=db,
            name=user_data.name,
            email=user_data.email,
            password=user_data.password
        )
        
        request.session["user_id"] = user.id
        logger.info(f"User registered: {user.email}")
        
        return AuthResponse(
            message="User registered successfully",
            user=UserResponse.model_validate(user)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed")

@app.post("/auth/login", response_model=AuthResponse)
async def login(request: Request, login_data: UserLogin, db: Session = Depends(get_db)):
    try:
        logger.info(f"Login attempt for: {login_data.email}")
        
        user = auth_service.authenticate_user(
            db=db,
            email=login_data.email,
            password=login_data.password
        )
        
        if not user:
            logger.warning(f"Failed login for: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        request.session["user_id"] = user.id
        logger.info(f"User logged in: {user.email}")
        
        return AuthResponse(
            message="Login successful",
            user=UserResponse.model_validate(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")

@app.post("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Logout successful"}

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(require_authentication)):
    return UserResponse.model_validate(current_user)

@app.get("/players", response_model=List[PlayerResponse])
async def get_players(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        players = db.query(Player).filter(Player.is_active == True).offset(skip).limit(limit).all()
        return players
    except Exception as e:
        logger.error(f"Error fetching players: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch players")

@app.get("/players/search")
async def search_players(
    q: Optional[str] = None,
    team: Optional[str] = None,
    position: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to search players")

@app.get("/teams")
async def get_laliga_teams(db: Session = Depends(get_db)):
    try:
        teams = db.query(Player.team).distinct().order_by(Player.team).all()
        return [{"name": team[0]} for team in teams if team[0]]
    except Exception as e:
        logger.error(f"Error fetching teams: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch teams")

@app.post("/fantasy-teams", response_model=FantasyTeamResponse, status_code=status.HTTP_201_CREATED)
async def create_fantasy_team(
    team_data: FantasyTeamCreate,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    try:
        team = fantasy_team_service.create_fantasy_team(
            db=db,
            user_id=current_user.id,
            team_name=team_data.name
        )
        return FantasyTeamResponse.model_validate(team)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating fantasy team: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create fantasy team")

@app.get("/fantasy-teams", response_model=List[FantasyTeamResponse])
async def get_user_fantasy_teams(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    try:
        teams = fantasy_team_service.get_user_teams(db=db, user_id=current_user.id)
        return [FantasyTeamResponse.model_validate(team) for team in teams]
    except Exception as e:
        logger.error(f"Error fetching fantasy teams: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch fantasy teams")

@app.get("/fantasy-teams/{team_id}", response_model=FantasyTeamDetailResponse)
async def get_fantasy_team_detail(
    team_id: int,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    try:
        team_data = fantasy_team_service.get_team_with_players(
            db=db,
            team_id=team_id,
            user_id=current_user.id
        )
        
        if not team_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fantasy team not found")
        
        return FantasyTeamDetailResponse(
            team=FantasyTeamResponse.model_validate(team_data['team']),
            players=[TeamPlayerResponse(**player) for player in team_data['players']],
            player_count=team_data['player_count']
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching fantasy team detail: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch fantasy team details")

@app.post("/fantasy-teams/{team_id}/players")
async def add_player_to_team(
    team_id: int,
    player_data: AddPlayerRequest,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    try:
        fantasy_team_service.add_player_to_team(
            db=db,
            team_id=team_id,
            player_id=player_data.player_id,
            user_id=current_user.id
        )
        return {"message": "Player added to team successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding player to team: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add player to team")

@app.delete("/fantasy-teams/{team_id}/players/{player_id}")
async def remove_player_from_team(
    team_id: int,
    player_id: int,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    try:
        fantasy_team_service.remove_player_from_team(
            db=db,
            team_id=team_id,
            player_id=player_id,
            user_id=current_user.id
        )
        return {"message": "Player removed from team successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error removing player from team: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to remove player from team")

@app.post("/fantasy-teams/{team_id}/captain")
async def set_team_captain(
    team_id: int,
    captain_data: SetCaptainRequest,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error setting captain: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to set captain")

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

# Transfer endpoints
@app.get("/fantasy-teams/{team_id}/transfer-status", response_model=TransferStatusResponse)
async def get_transfer_status(
    team_id: int,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Get transfer status and budget information for a team."""
    try:
        status = transfer_service.get_transfer_status(db, team_id, current_user.id)
        return TransferStatusResponse(**status)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting transfer status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get transfer status"
        )

@app.post("/fantasy-teams/{team_id}/validate-transfer", response_model=TransferValidationResponse)
async def validate_transfer(
    team_id: int,
    transfer_data: TransferRequest,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Validate a proposed transfer without executing it."""
    try:
        validation = transfer_service.validate_transfer(
            db, team_id, transfer_data.player_in_id, 
            transfer_data.player_out_id, current_user.id
        )
        return TransferValidationResponse(**validation)
        
    except Exception as e:
        logger.error(f"Error validating transfer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate transfer"
        )

@app.post("/fantasy-teams/{team_id}/execute-transfer")
async def execute_transfer(
    team_id: int,
    transfer_data: TransferRequest,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Execute a player transfer."""
    try:
        result = transfer_service.execute_transfer(
            db, team_id, transfer_data.player_in_id, 
            transfer_data.player_out_id, current_user.id
        )
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error executing transfer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute transfer"
        )

@app.get("/fantasy-teams/{team_id}/transfer-history")
async def get_transfer_history(
    team_id: int,
    limit: int = 50,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Get transfer history for a team."""
    try:
        history = transfer_service.get_transfer_history(db, team_id, current_user.id, limit)
        return {"transfers": history}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting transfer history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get transfer history"
        )

# League Management Endpoints
@app.post("/leagues", response_model=LeagueResponse, status_code=status.HTTP_201_CREATED)
async def create_league(
    league_data: LeagueCreateRequest,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Create a new fantasy league."""
    try:
        league = league_service.create_league(
            db=db,
            user_id=current_user.id,
            name=league_data.name,
            description=league_data.description,
            is_private=league_data.is_private,
            max_participants=league_data.max_participants
        )
        
        return LeagueResponse(
            id=league.id,
            name=league.name,
            description=league.description,
            is_private=league.is_private,
            is_creator=True,
            participants=1,  # Creator is automatically added
            max_participants=league.max_participants,
            created_at=league.created_at.isoformat(),
            join_code=league.join_code
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating league: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create league")

@app.get("/leagues", response_model=List[LeagueResponse])
async def get_user_leagues(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Get all leagues the current user is participating in."""
    try:
        leagues = league_service.get_user_leagues(db=db, user_id=current_user.id)
        return [LeagueResponse(**league) for league in leagues]
    except Exception as e:
        logger.error(f"Error fetching user leagues: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch leagues")

@app.get("/leagues/public", response_model=List[Dict])
async def get_public_leagues(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get public leagues that users can join."""
    try:
        leagues = league_service.get_public_leagues(db=db, skip=skip, limit=limit)
        return leagues
    except Exception as e:
        logger.error(f"Error fetching public leagues: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch public leagues")

@app.post("/leagues/join", response_model=LeagueJoinResponse)
async def join_league_by_code(
    join_data: LeagueJoinRequest,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Join a league using a join code."""
    try:
        result = league_service.join_league_by_code(
            db=db,
            join_code=join_data.join_code,
            user_id=current_user.id
        )
        return LeagueJoinResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error joining league: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to join league")

@app.post("/leagues/{league_id}/join", response_model=LeagueJoinResponse)
async def join_league_by_id(
    league_id: int,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Join a public league by ID."""
    try:
        result = league_service.join_league_by_id(
            db=db,
            league_id=league_id,
            user_id=current_user.id
        )
        return LeagueJoinResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error joining league: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to join league")

@app.delete("/leagues/{league_id}/leave")
async def leave_league(
    league_id: int,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Leave a league."""
    try:
        league_service.leave_league(db=db, league_id=league_id, user_id=current_user.id)
        return {"message": "Successfully left the league"}
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error leaving league: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to leave league")

@app.get("/leagues/{league_id}/leaderboard", response_model=LeaderboardResponse)
async def get_league_leaderboard(
    league_id: int,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Get league leaderboard."""
    try:
        leaderboard = league_service.get_league_leaderboard(
            db=db,
            league_id=league_id,
            user_id=current_user.id
        )
        return LeaderboardResponse(**leaderboard)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching leaderboard: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch leaderboard")

@app.put("/leagues/{league_id}", response_model=LeagueResponse)
async def update_league(
    league_id: int,
    update_data: LeagueUpdateRequest,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Update league settings (creator only)."""
    try:
        league = league_service.update_league(
            db=db,
            league_id=league_id,
            user_id=current_user.id,
            name=update_data.name,
            description=update_data.description,
            max_participants=update_data.max_participants
        )
        
        # Get participant count for response
        participant_count = db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.league_id == league_id
        ).count()
        
        return LeagueResponse(
            id=league.id,
            name=league.name,
            description=league.description,
            is_private=league.is_private,
            is_creator=True,
            participants=participant_count,
            max_participants=league.max_participants,
            created_at=league.created_at.isoformat(),
            join_code=league.join_code
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating league: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update league")

# Run the app
if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Fantasy Football Tracker API...")
    if not test_database_connection():
        logger.error("Failed to connect to database on startup!")
        sys.exit(1)
    
    logger.info(f"Starting server on {app_config.HOST}:{app_config.PORT}")
    uvicorn.run("app:app", host=app_config.HOST, port=app_config.PORT, reload=app_config.DEBUG)
