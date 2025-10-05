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
from src.models import User, Player, FantasyTeam, FantasyTeamPlayer, Matchday, FantasyLeagueParticipant, FantasyLeague, LeagueTeam
from src.services.auth import auth_service
from src.services import team_transfer_service
from src.services.league_service import league_service
from src.services.league_transfer_service import FreeAgentTransferService, UserTransferService
from src.services.matchday_status_service import MatchdayStatusService

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

# Startup event: Auto-update matchday statuses based on dates
@app.on_event("startup")
async def startup_event():
    """
    Run on application startup.
    Automatically updates matchday statuses based on their start/end dates.
    """
    db = next(get_db())
    try:
        matchday_service = MatchdayStatusService()
        result = matchday_service.update_matchday_status(db)
    except Exception as e:
        logger.error(f"✗ Failed to auto-update matchday statuses on startup: {e}")
    finally:
        db.close()

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
    player_count: int = 0  # Number of players currently in the team
    
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
    team_name: Optional[str] = None  # Team name for the creator's team in this league

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

# Transfer-related models
class FreeAgentTransferRequest(BaseModel):
    player_in_id: int
    player_out_id: Optional[int] = None

class CreateTransferOfferRequest(BaseModel):
    to_team_id: int
    player_id: int
    offer_type: str  # 'money' or 'player_exchange'
    money_offered: Optional[float] = 0.0
    player_offered_id: Optional[int] = None
    player_out_id: Optional[int] = None  # For money offers: player buyer wants to drop

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
            total_budget=150000000.0,
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
        
        # Calculate total points from league teams instead of fantasy_teams.total_points
        league_teams = db.query(LeagueTeam).filter(
            LeagueTeam.fantasy_team_id == team_id
        ).all()
        total_league_points = sum(lt.league_points for lt in league_teams)
        
        # Create a modified team dict with correct points
        team_dict = {
            'id': team.id,
            'name': team.name,
            'total_points': total_league_points,  # Use league points sum
            'max_players': team.max_players,
            'total_budget': team.total_budget
        }
        
        return {
            'team': team_dict,
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
        
        request.session["user_id"] = user.id
        
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
        team_responses = []
        for team in teams:
            # Count players in this team
            player_count = db.query(FantasyTeamPlayer).filter(
                FantasyTeamPlayer.fantasy_team_id == team.id
            ).count()
            
            # Get league points from league_teams table (sum across all leagues)
            league_teams = db.query(LeagueTeam).filter(
                LeagueTeam.fantasy_team_id == team.id
            ).all()
            total_league_points = sum(lt.league_points for lt in league_teams)
            
            team_dict = {
                'id': team.id,
                'name': team.name,
                'total_points': total_league_points,  # Use league points instead
                'max_players': team.max_players,
                'total_budget': team.total_budget,
                'player_count': player_count
            }
            team_responses.append(FantasyTeamResponse(**team_dict))
        
        return team_responses
    except Exception as e:
        logger.error(f"Error fetching fantasy teams: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch fantasy teams")


@app.get("/fantasy-teams/{team_id}/leagues")
async def get_fantasy_team_leagues(
    team_id: int,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Get all leagues this fantasy team is participating in."""
    try:
        # Verify team ownership
        team = db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == current_user.id
        ).first()
        
        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fantasy team not found")
        
        # Get all leagues this team is in
        league_teams = db.query(LeagueTeam).filter(
            LeagueTeam.fantasy_team_id == team_id
        ).all()
        
        leagues = []
        for lt in league_teams:
            league = db.query(FantasyLeague).filter(FantasyLeague.id == lt.league_id).first()
            if league:
                leagues.append({
                    'league_id': league.id,
                    'league_name': league.name,
                    'league_team_id': lt.id
                })
        
        return {'leagues': leagues}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching fantasy team leagues: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch leagues")

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

@app.put("/fantasy-teams/{team_id}")
async def update_fantasy_team(
    team_id: int,
    update_data: dict,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Update fantasy team name."""
    try:
        # Verify team ownership
        team = db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == current_user.id
        ).first()
        
        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fantasy team not found")
        
        # Update team name if provided
        if 'name' in update_data and update_data['name']:
            team.name = update_data['name']
            db.commit()
            db.refresh(team)
            
        return {"message": "Team updated successfully", "team": {"id": team.id, "name": team.name}}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating fantasy team: {e}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update team")

@app.delete("/fantasy-teams/{team_id}")
async def delete_fantasy_team(
    team_id: int,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Delete a fantasy team if it's not part of any league."""
    try:
        # Verify team ownership
        team = db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == current_user.id
        ).first()
        
        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fantasy team not found")
        
        # Check if team is in any league
        league_participation = db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.fantasy_team_id == team_id
        ).first()
        
        if league_participation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Cannot delete team that is participating in a league. Please leave the league first."
            )
        
        # Delete any orphaned LeagueTeam entries (teams not actively in a league)
        db.query(LeagueTeam).filter(LeagueTeam.fantasy_team_id == team_id).delete()
        
        # Delete the team (cascade will delete related FantasyTeamPlayer and TransferHistory records)
        db.delete(team)
        db.commit()
        
        return {"message": "Team deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting fantasy team: {e}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete team")

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
        # Use the MatchdayStatusService to get current matchday
        matchday_service = MatchdayStatusService()
        current_matchday = matchday_service.get_current_matchday(db)
        
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

@app.post("/matchdays/status/update")
async def update_matchday_statuses(db: Session = Depends(get_db)):
    """
    Manually trigger matchday status update.
    Updates all matchday statuses based on their start_date and end_date.
    Activates matchdays within their date range, deactivates those outside.
    """
    try:
        matchday_service = MatchdayStatusService()
        result = matchday_service.update_matchday_status(db)
        
        return {
            "success": result['success'],
            "message": result['message'],
            "active_matchday": result.get('active_matchday'),
            "changes_made": result.get('changes_made', 0),
            "total_matchdays": result.get('total_matchdays', 0),
            "details": result
        }
        
    except Exception as e:
        logger.error(f"Error updating matchday statuses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update matchday statuses: {str(e)}"
        )

@app.get("/matchdays/status/info")
async def get_matchday_status_info(db: Session = Depends(get_db)):
    """
    Get detailed information about the current matchday and transfer lock status.
    Returns comprehensive status including active matchday, transfer lock state, and timing information.
    """
    try:
        matchday_service = MatchdayStatusService()
        info = matchday_service.get_matchday_info(db)
        
        return info
        
    except Exception as e:
        logger.error(f"Error getting matchday status info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get matchday status info: {str(e)}"
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
        status = team_transfer_service.get_transfer_status(db, team_id, current_user.id)
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
        validation = team_transfer_service.validate_transfer(
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
        result = team_transfer_service.execute_transfer(
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
        history = team_transfer_service.get_transfer_history(db, team_id, current_user.id, limit)
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
            max_participants=league_data.max_participants,
            team_name=league_data.team_name
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
        # Extract team_name from join_data if it exists (need to update LeagueJoinRequest model)
        team_name = getattr(join_data, 'team_name', None)
        result = league_service.join_league_by_code(
            db=db,
            join_code=join_data.join_code,
            user_id=current_user.id,
            team_name=team_name
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
    team_name: Optional[str] = None,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Join a public league by ID with optional custom team name."""
    try:
        result = league_service.join_league_by_id(
            db=db,
            league_id=league_id,
            user_id=current_user.id,
            team_name=team_name
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

@app.get("/leagues/{league_id}/my-team")
async def get_my_league_team(
    league_id: int,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Get the current user's league-specific team details including players and points."""
    try:
        from src.models import LeagueTeam, LeagueTeamPlayer, Player
        
        # Find the user's participation in this league
        participant = db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.league_id == league_id,
            FantasyLeagueParticipant.user_id == current_user.id
        ).first()
        
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not a member of this league"
            )
        
        if not participant.league_team_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No league team found"
            )
        
        # Get league team
        league_team = db.query(LeagueTeam).filter(
            LeagueTeam.id == participant.league_team_id
        ).first()
        
        if not league_team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="League team not found"
            )
        
        # Get league team players
        league_team_players = db.query(LeagueTeamPlayer).filter(
            LeagueTeamPlayer.league_team_id == league_team.id
        ).all()
        
        players_data = []
        for ltp in league_team_players:
            player = db.query(Player).filter(Player.id == ltp.player_id).first()
            if player:
                players_data.append({
                    'id': player.id,
                    'name': player.name,
                    'team': player.team,
                    'position': player.position,
                    'price': player.price,
                    'is_captain': ltp.is_captain,
                    'is_vice_captain': ltp.is_vice_captain,
                    'position_in_team': ltp.position_in_team
                })
        
        # Get league info
        league = db.query(FantasyLeague).filter(FantasyLeague.id == league_id).first()
        league_name = league.name if league else "Unknown League"
        
        return {
            'league_team_id': league_team.id,
            'league_id': league_team.league_id,
            'league_name': league_name,
            'team_name': league_team.team_name,
            'fantasy_team_id': league_team.fantasy_team_id,
            'league_points': league_team.league_points,
            'league_rank': league_team.league_rank,
            'total_budget': league_team.total_budget,
            'budget_used': league_team.current_budget_used,
            'remaining_budget': league_team.remaining_budget,
            'players': players_data,
            'player_count': len(players_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching league team: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch league team"
        )

@app.patch("/leagues/{league_id}/my-team")
async def update_my_league_team_name(
    league_id: int,
    team_name: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Update the team name for the current user's league-specific team."""
    try:
        result = league_service.update_league_team_name(
            db=db,
            league_id=league_id,
            user_id=current_user.id,
            new_team_name=team_name
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating league team name: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update team name")

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

@app.delete("/leagues/{league_id}")
async def delete_league(
    league_id: int,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Delete a league (creator only)."""
    try:
        league_service.delete_league(db=db, league_id=league_id, user_id=current_user.id)
        return {"message": "League deleted successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting league: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete league")

# ============= TRANSFER ENDPOINTS =============

@app.get("/leagues/{league_id}/players/available")
async def get_available_players(
    league_id: int,
    position: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Get available free agent players for a league."""
    try:
        players = FreeAgentTransferService.get_available_players(
            db=db,
            league_id=league_id,
            position=position,
            search=search,
            min_price=min_price,
            max_price=max_price
        )
        return {'players': players}
        
    except Exception as e:
        logger.error(f"Error fetching available players: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch available players"
        )

@app.post("/leagues/{league_id}/teams/{team_id}/transfers/free-agent")
async def execute_free_agent_transfer(
    league_id: int,
    team_id: int,
    request: FreeAgentTransferRequest,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Execute a free agent transfer."""
    try:
        # Get league team and verify ownership
        league_team = db.query(LeagueTeam).filter(
            LeagueTeam.id == team_id,
            LeagueTeam.league_id == league_id
        ).first()
        
        if not league_team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Verify user owns this team
        if league_team.fantasy_team.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't own this team"
            )
        
        # Validate the transfer
        validation = FreeAgentTransferService.validate_free_transfer(
            db=db,
            league_id=league_id,
            team_id=team_id,
            player_in_id=request.player_in_id,
            player_out_id=request.player_out_id
        )
        
        if not validation['is_valid']:
            return {
                'success': False,
                'errors': validation.get('errors', [])
            }
        
        # Execute the transfer
        result = FreeAgentTransferService.execute_free_transfer(
            db=db,
            league_id=league_id,
            team_id=team_id,
            player_in_id=request.player_in_id,
            player_out_id=request.player_out_id,
            user_id=current_user.id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing free agent transfer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/leagues/{league_id}/transfers/offers")
async def create_transfer_offer(
    league_id: int,
    request: CreateTransferOfferRequest,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Create a user-to-user transfer offer."""
    try:
        # Get the user's team in this league
        participant = db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.league_id == league_id,
            FantasyLeagueParticipant.user_id == current_user.id
        ).first()
        
        if not participant or not participant.league_team_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not a member of this league"
            )
        
        result = UserTransferService.create_offer(
            db=db,
            league_id=league_id,
            from_team_id=participant.league_team_id,
            to_team_id=request.to_team_id,
            player_id=request.player_id,
            offer_type=request.offer_type,
            money_offered=request.money_offered or 0.0,
            player_offered_id=request.player_offered_id,
            player_out_id=request.player_out_id,
            user_id=current_user.id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating transfer offer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/leagues/{league_id}/teams/{team_id}/transfers/offers")
async def get_transfer_offers(
    league_id: int,
    team_id: int,
    direction: str = 'received',  # 'received' or 'sent'
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Get transfer offers for a team (received or sent)."""
    try:
        # Verify team ownership
        league_team = db.query(LeagueTeam).filter(
            LeagueTeam.id == team_id,
            LeagueTeam.league_id == league_id
        ).first()
        
        if not league_team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        if league_team.fantasy_team.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't own this team"
            )
        
        offers = UserTransferService.get_team_offers(
            db=db,
            league_id=league_id,
            team_id=team_id,
            offer_direction=direction
        )
        
        return {'offers': offers}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transfer offers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch transfer offers"
        )

@app.put("/leagues/{league_id}/transfers/offers/{offer_id}/accept")
async def accept_transfer_offer(
    league_id: int,
    offer_id: int,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Accept a transfer offer."""
    try:
        result = UserTransferService.accept_offer(
            db=db,
            offer_id=offer_id,
            league_id=league_id,
            user_id=current_user.id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting transfer offer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.put("/leagues/{league_id}/transfers/offers/{offer_id}/reject")
async def reject_transfer_offer(
    league_id: int,
    offer_id: int,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Reject a transfer offer."""
    try:
        result = UserTransferService.reject_offer(
            db=db,
            offer_id=offer_id,
            league_id=league_id,
            user_id=current_user.id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting transfer offer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.delete("/leagues/{league_id}/transfers/offers/{offer_id}")
async def cancel_transfer_offer(
    league_id: int,
    offer_id: int,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Cancel a transfer offer (by the offering team)."""
    try:
        result = UserTransferService.cancel_offer(
            db=db,
            offer_id=offer_id,
            league_id=league_id,
            user_id=current_user.id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling transfer offer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/leagues/{league_id}/teams")
async def get_league_teams(
    league_id: int,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Get all teams in a league with their players."""
    try:
        from src.models import LeagueTeam, LeagueTeamPlayer, Player
        
        # Verify user is in the league
        participant = db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.league_id == league_id,
            FantasyLeagueParticipant.user_id == current_user.id
        ).first()
        
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this league"
            )
        
        # Get all teams in the league
        league_teams = db.query(LeagueTeam).filter(
            LeagueTeam.league_id == league_id
        ).all()
        
        teams_data = []
        for team in league_teams:
            # Get team players
            team_players = db.query(LeagueTeamPlayer).filter(
                LeagueTeamPlayer.league_team_id == team.id
            ).all()
            
            players_data = []
            for ltp in team_players:
                player = db.query(Player).filter(Player.id == ltp.player_id).first()
                if player:
                    players_data.append({
                        'id': player.id,
                        'name': player.name,
                        'team': player.team,
                        'position': player.position,
                        'price': player.price
                    })
            
            teams_data.append({
                'id': team.id,
                'team_name': team.team_name or team.fantasy_team.name,
                'user_name': team.fantasy_team.user.name,
                'user_id': team.fantasy_team.user_id,
                'league_points': team.league_points,
                'league_rank': team.league_rank,
                'is_current_user': team.fantasy_team.user_id == current_user.id,
                'players': players_data
            })
        
        # Sort by rank
        teams_data.sort(key=lambda x: x['league_rank'] if x['league_rank'] else 999)
        
        return {'teams': teams_data}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching league teams: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch league teams"
        )

# Run the app
if __name__ == "__main__":
    import uvicorn
    
    if not test_database_connection():
        logger.error("Failed to connect to database on startup!")
        sys.exit(1)
    
    uvicorn.run("app:app", host=app_config.HOST, port=app_config.PORT, reload=app_config.DEBUG)
