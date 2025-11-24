from typing import List, Optional, Dict
from pydantic import BaseModel, EmailStr


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
    player_count: int = 0

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
    team_name: Optional[str] = None


class LeagueJoinRequest(BaseModel):
    join_code: str
    team_name: Optional[str] = None


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


class FreeAgentTransferRequest(BaseModel):
    player_in_id: int
    player_out_id: Optional[int] = None


class CreateTransferOfferRequest(BaseModel):
    to_team_id: int
    player_id: int
    offer_type: str
    money_offered: Optional[float] = 0.0
    player_offered_id: Optional[int] = None
    player_out_id: Optional[int] = None
