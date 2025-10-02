from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """
    User model representing fantasy football players/users.
    """
    __tablename__ = 'users'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(100), nullable=False)
    email: Mapped[str] = Column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = Column(String(255), nullable=False)
    is_active: Mapped[bool] = Column(Boolean, default=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    fantasy_teams: Mapped[List["FantasyTeam"]] = relationship("FantasyTeam", back_populates="user")
    created_leagues: Mapped[List["FantasyLeague"]] = relationship("FantasyLeague", back_populates="creator")
    league_participations: Mapped[List["FantasyLeagueParticipant"]] = relationship("FantasyLeagueParticipant", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"


class Player(Base):
    """
    Player model representing real football players.
    """
    __tablename__ = 'players'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(100), nullable=False)
    team: Mapped[str] = Column(String(100), nullable=False)
    position: Mapped[str] = Column(String(50), nullable=False)  # GK, DEF, MID, FWD
    price: Mapped[float] = Column(Float, nullable=False)
    
    # Real stats (cumulative for the season)
    goals: Mapped[int] = Column(Integer, default=0)
    assists: Mapped[int] = Column(Integer, default=0)
    yellow_cards: Mapped[int] = Column(Integer, default=0)
    red_cards: Mapped[int] = Column(Integer, default=0)
    minutes_played: Mapped[int] = Column(Integer, default=0)
    clean_sheets: Mapped[int] = Column(Integer, default=0)  # For defenders and goalkeepers
    
    # Meta information
    is_active: Mapped[bool] = Column(Boolean, default=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    fantasy_points: Mapped[List["FantasyPoints"]] = relationship("FantasyPoints", back_populates="player")
    match_stats: Mapped[List["MatchPlayerStats"]] = relationship("MatchPlayerStats", back_populates="player")

    def __repr__(self):
        return f"<Player(id={self.id}, name='{self.name}', team='{self.team}', position='{self.position}')>"


class FantasyTeam(Base):
    """
    Fantasy team model representing a user's fantasy football team.
    """
    __tablename__ = 'fantasy_teams'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = Column(Integer, ForeignKey('users.id'), nullable=False)
    name: Mapped[str] = Column(String(100), nullable=False)
    total_points: Mapped[float] = Column(Float, default=0.0)
    total_budget: Mapped[float] = Column(Float, default=100000000.0)
    
    # Team composition (could be extended to support formations)
    max_players: Mapped[int] = Column(Integer, default=14)  # Standard team size
    
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="fantasy_teams")
    team_players: Mapped[List["FantasyTeamPlayer"]] = relationship("FantasyTeamPlayer", back_populates="fantasy_team")
    transfer_history: Mapped[List["TransferHistory"]] = relationship("TransferHistory", back_populates="fantasy_team")
    league_participations: Mapped[List["FantasyLeagueParticipant"]] = relationship("FantasyLeagueParticipant", back_populates="fantasy_team")

    def __repr__(self):
        return f"<FantasyTeam(id={self.id}, name='{self.name}', user_id={self.user_id}, points={self.total_points})>"

    @property
    def current_budget_used(self) -> float:
        """Calculate current budget used by team players."""
        total_cost = 0.0
        for team_player in self.team_players:
            if team_player.player:
                total_cost += team_player.player.price
        return total_cost
    
    @property
    def remaining_budget(self) -> float:
        """Calculate remaining budget."""
        return self.total_budget - self.current_budget_used
    
    def can_afford_transfer(self, player_in_price: float, player_out_price: float = 0.0) -> bool:
        """Check if team can afford a transfer."""
        net_cost = player_in_price - player_out_price
        return self.remaining_budget >= net_cost


class FantasyTeamPlayer(Base):
    """
    Association table between fantasy teams and players.
    This allows tracking which players are in which fantasy teams.
    """
    __tablename__ = 'fantasy_team_players'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    fantasy_team_id: Mapped[int] = Column(Integer, ForeignKey('fantasy_teams.id'), nullable=False)
    player_id: Mapped[int] = Column(Integer, ForeignKey('players.id'), nullable=False)
    
    # Position in fantasy team formation
    position_in_team: Mapped[str] = Column(String(50), nullable=False)  # GK, DEF, MID, FWD
    is_captain: Mapped[bool] = Column(Boolean, default=False)
    is_vice_captain: Mapped[bool] = Column(Boolean, default=False)
    
    # Transfer tracking
    added_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    added_for_matchday: Mapped[Optional[int]] = Column(Integer, nullable=True)  # Which matchday was this player added for
    
    # Relationships
    fantasy_team: Mapped["FantasyTeam"] = relationship("FantasyTeam", back_populates="team_players")
    player: Mapped["Player"] = relationship("Player")

    def __repr__(self):
        return f"<FantasyTeamPlayer(team_id={self.fantasy_team_id}, player_id={self.player_id}, position='{self.position_in_team}')>"


class Match(Base):
    """
    Match/Matchday model representing real football matches.
    """
    __tablename__ = 'matches'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    home_team: Mapped[str] = Column(String(100), nullable=False)
    away_team: Mapped[str] = Column(String(100), nullable=False)
    match_date: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False)
    
    # Match details
    matchday: Mapped[int] = Column(Integer, nullable=False)  # Gameweek number
    matchday_id: Mapped[Optional[int]] = Column(Integer, ForeignKey('matchdays.id'), nullable=True)
    season: Mapped[str] = Column(String(20), nullable=False)  # e.g., "2024-25"
    competition: Mapped[str] = Column(String(100), nullable=False)  # e.g., "Premier League", "Champions League"
    
    # Match result
    home_score: Mapped[Optional[int]] = Column(Integer, nullable=True)
    away_score: Mapped[Optional[int]] = Column(Integer, nullable=True)
    is_finished: Mapped[bool] = Column(Boolean, default=False)
    
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    matchday_info: Mapped[Optional["Matchday"]] = relationship("Matchday", back_populates="matches")
    player_stats: Mapped[List["MatchPlayerStats"]] = relationship("MatchPlayerStats", back_populates="match")
    fantasy_points: Mapped[List["FantasyPoints"]] = relationship("FantasyPoints", back_populates="match")

    def __repr__(self):
        return f"<Match(id={self.id}, {self.home_team} vs {self.away_team}, matchday={self.matchday})>"


class MatchPlayerStats(Base):
    """
    Player statistics for a specific match.
    This tracks individual player performance in each match.
    """
    __tablename__ = 'match_player_stats'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = Column(Integer, ForeignKey('matches.id'), nullable=False)
    player_id: Mapped[int] = Column(Integer, ForeignKey('players.id'), nullable=False)
    
    # Match-specific stats
    minutes_played: Mapped[int] = Column(Integer, default=0)
    goals: Mapped[int] = Column(Integer, default=0)
    assists: Mapped[int] = Column(Integer, default=0)
    yellow_cards: Mapped[int] = Column(Integer, default=0)
    red_cards: Mapped[int] = Column(Integer, default=0)
    
    # Additional stats for fantasy scoring
    saves: Mapped[int] = Column(Integer, default=0)  # For goalkeepers
    clean_sheet: Mapped[bool] = Column(Boolean, default=False)  # For defenders/goalkeepers
    own_goals: Mapped[int] = Column(Integer, default=0)
    penalties_missed: Mapped[int] = Column(Integer, default=0)
    penalties_saved: Mapped[int] = Column(Integer, default=0)  # For goalkeepers
    
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    match: Mapped["Match"] = relationship("Match", back_populates="player_stats")
    player: Mapped["Player"] = relationship("Player", back_populates="match_stats")

    def __repr__(self):
        return f"<MatchPlayerStats(match_id={self.match_id}, player_id={self.player_id}, goals={self.goals}, assists={self.assists})>"


class FantasyPoints(Base):
    """
    Fantasy points model linking player performance to fantasy scoring.
    This calculates and stores fantasy points based on real player performance.
    """
    __tablename__ = 'fantasy_points'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = Column(Integer, ForeignKey('players.id'), nullable=False)
    match_id: Mapped[int] = Column(Integer, ForeignKey('matches.id'), nullable=False)
    
    # Fantasy scoring breakdown
    points_from_goals: Mapped[float] = Column(Float, default=0.0)
    points_from_assists: Mapped[float] = Column(Float, default=0.0)
    points_from_clean_sheet: Mapped[float] = Column(Float, default=0.0)
    points_from_cards: Mapped[float] = Column(Float, default=0.0)  # Usually negative
    points_from_saves: Mapped[float] = Column(Float, default=0.0)
    points_from_minutes: Mapped[float] = Column(Float, default=0.0)
    bonus_points: Mapped[float] = Column(Float, default=0.0)
    penalty_points: Mapped[float] = Column(Float, default=0.0)  # For missed penalties, own goals, etc.
    
    # Total points for this match
    total_points: Mapped[float] = Column(Float, nullable=False)
    
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    player: Mapped["Player"] = relationship("Player", back_populates="fantasy_points")
    match: Mapped["Match"] = relationship("Match", back_populates="fantasy_points")

    def __repr__(self):
        return f"<FantasyPoints(player_id={self.player_id}, match_id={self.match_id}, total_points={self.total_points})>"


class FantasyLeague(Base):
    """
    Fantasy league model for organizing competitions between users.
    """
    __tablename__ = 'fantasy_leagues'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(100), nullable=False)
    description: Mapped[Optional[str]] = Column(Text, nullable=True)
    is_private: Mapped[bool] = Column(Boolean, default=False)
    join_code: Mapped[Optional[str]] = Column(String(20), unique=True, nullable=True)
    
    # League settings
    max_participants: Mapped[int] = Column(Integer, default=20)
    creator_id: Mapped[int] = Column(Integer, ForeignKey('users.id'), nullable=False)
    start_date: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[Optional[datetime]] = Column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="created_leagues")
    participants: Mapped[List["FantasyLeagueParticipant"]] = relationship("FantasyLeagueParticipant", back_populates="league")

    def __repr__(self):
        return f"<FantasyLeague(id={self.id}, name='{self.name}', participants={self.max_participants})>"


class FantasyLeagueParticipant(Base):
    """
    Association table for league participants.
    """
    __tablename__ = 'fantasy_league_participants'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    league_id: Mapped[int] = Column(Integer, ForeignKey('fantasy_leagues.id'), nullable=False)
    user_id: Mapped[int] = Column(Integer, ForeignKey('users.id'), nullable=False)
    fantasy_team_id: Mapped[int] = Column(Integer, ForeignKey('fantasy_teams.id'), nullable=False)
    
    # Participant tracking
    joined_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    league: Mapped["FantasyLeague"] = relationship("FantasyLeague", back_populates="participants")
    user: Mapped["User"] = relationship("User", back_populates="league_participations")
    fantasy_team: Mapped["FantasyTeam"] = relationship("FantasyTeam", back_populates="league_participations")

    def __repr__(self):
        return f"<FantasyLeagueParticipant(league_id={self.league_id}, user_id={self.user_id})>"


class Matchday(Base):
    """
    Matchday model representing a complete matchday period with start/end dates.
    Used for transfer locks and automatic points updates.
    """
    __tablename__ = 'matchdays'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    matchday_number: Mapped[int] = Column(Integer, nullable=False, unique=True)
    season: Mapped[str] = Column(String(20), nullable=False)  # e.g., "2024-2025"
    free_transfers: Mapped[int] = Column(Integer, default=2)
    
    # Matchday period
    start_date: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False)
    deadline: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False)  # Transfer deadline
    
    # Status tracking
    is_active: Mapped[bool] = Column(Boolean, default=False)  # Currently ongoing
    is_finished: Mapped[bool] = Column(Boolean, default=False)  # All matches completed
    points_calculated: Mapped[bool] = Column(Boolean, default=False)  # Points have been processed
    
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    matches: Mapped[List["Match"]] = relationship("Match", back_populates="matchday_info")

    def __repr__(self):
        return f"<Matchday(number={self.matchday_number}, season='{self.season}', active={self.is_active})>"

    @property
    def is_transfer_locked(self) -> bool:
        """Check if transfers are locked for this matchday."""
        now = datetime.now(timezone.utc)
        # Handle both timezone-aware and naive datetimes
        deadline = self.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        return now >= deadline

    @property
    def time_until_deadline(self) -> Optional[str]:
        """Get human-readable time until transfer deadline."""
        if self.is_transfer_locked:
            return "Transfer deadline passed"
        
        now = datetime.now(timezone.utc)
        deadline = self.deadline
        
        # Handle timezone awareness
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        
        delta = deadline - now
        
        if delta.days > 0:
            return f"{delta.days} days, {delta.seconds // 3600} hours"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600} hours, {(delta.seconds % 3600) // 60} minutes"
        else:
            return f"{delta.seconds // 60} minutes"
        

class TransferHistory(Base):
    """
    Track all player transfers for budget and penalty calculations.
    """
    __tablename__ = 'transfer_history'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    fantasy_team_id: Mapped[int] = Column(Integer, ForeignKey('fantasy_teams.id'), nullable=False)
    matchday_id: Mapped[int] = Column(Integer, ForeignKey('matchdays.id'), nullable=False)
    
    # Transfer details
    player_in_id: Mapped[Optional[int]] = Column(Integer, ForeignKey('players.id'), nullable=True)  # Player bought
    player_out_id: Mapped[Optional[int]] = Column(Integer, ForeignKey('players.id'), nullable=True)  # Player sold
    transfer_cost: Mapped[float] = Column(Float, default=0.0)  # Net cost of transfer
    penalty_points: Mapped[float] = Column(Float, default=0.0)  # Points deducted for extra transfers
    is_free_transfer: Mapped[bool] = Column(Boolean, default=True)
    
    # Tracking
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    fantasy_team: Mapped["FantasyTeam"] = relationship("FantasyTeam")
    matchday: Mapped["Matchday"] = relationship("Matchday")
    player_in: Mapped[Optional["Player"]] = relationship("Player", foreign_keys=[player_in_id])
    player_out: Mapped[Optional["Player"]] = relationship("Player", foreign_keys=[player_out_id])

    def __repr__(self):
        return f"<TransferHistory(team_id={self.fantasy_team_id}, matchday={self.matchday_id})>"
