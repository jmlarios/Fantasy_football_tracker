"""
Fantasy Football Tracker Models

This module contains all the database models for the fantasy football tracker application.
"""

from datetime import datetime
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
    email: Mapped[Optional[str]] = Column(String(255), unique=True, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    fantasy_teams: Mapped[List["FantasyTeam"]] = relationship("FantasyTeam", back_populates="user")

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
    
    # Team composition (could be extended to support formations)
    max_players: Mapped[int] = Column(Integer, default=11)  # Standard team size
    
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="fantasy_teams")
    team_players: Mapped[List["FantasyTeamPlayer"]] = relationship("FantasyTeamPlayer", back_populates="fantasy_team")

    def __repr__(self):
        return f"<FantasyTeam(id={self.id}, name='{self.name}', user_id={self.user_id}, points={self.total_points})>"


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
    
    added_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())

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
    season: Mapped[str] = Column(String(20), nullable=False)  # e.g., "2024-25"
    competition: Mapped[str] = Column(String(100), nullable=False)  # e.g., "Premier League", "Champions League"
    
    # Match result
    home_score: Mapped[Optional[int]] = Column(Integer, nullable=True)
    away_score: Mapped[Optional[int]] = Column(Integer, nullable=True)
    is_finished: Mapped[bool] = Column(Boolean, default=False)
    
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
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
    Optional: for future expansion to support leagues/competitions.
    """
    __tablename__ = 'fantasy_leagues'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(100), nullable=False)
    description: Mapped[Optional[str]] = Column(Text, nullable=True)
    is_private: Mapped[bool] = Column(Boolean, default=False)
    join_code: Mapped[Optional[str]] = Column(String(20), unique=True, nullable=True)
    
    # League settings
    max_participants: Mapped[int] = Column(Integer, default=20)
    start_date: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[Optional[datetime]] = Column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<FantasyLeague(id={self.id}, name='{self.name}', participants={self.max_participants})>"
