from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from src.models import (
    FantasyLeague, FantasyTeam, User, FantasyLeagueParticipant
)
import logging
import secrets
import string
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class LeagueService:
    """Service for managing fantasy leagues and participants."""
    
    @staticmethod
    def generate_join_code() -> str:
        """Generate a unique 8-character join code."""
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    
    @staticmethod
    def create_league(db: Session, user_id: int, name: str, description: Optional[str] = None,
                     is_private: bool = False, max_participants: int = 20) -> FantasyLeague:
        """Create a new fantasy league."""
        
        # Check if user already has a league with this name
        existing_league = db.query(FantasyLeague).filter(
            FantasyLeague.creator_id == user_id,
            FantasyLeague.name == name
        ).first()
        
        if existing_league:
            raise ValueError("You already have a league with this name")
        
        # Generate join code for private leagues
        join_code = None
        if is_private:
            # Ensure join code is unique
            while True:
                join_code = LeagueService.generate_join_code()
                existing = db.query(FantasyLeague).filter(
                    FantasyLeague.join_code == join_code
                ).first()
                if not existing:
                    break
        
        # Create league
        league = FantasyLeague(
            name=name,
            description=description,
            is_private=is_private,
            join_code=join_code,
            max_participants=max_participants,
            creator_id=user_id,
            start_date=datetime.now(timezone.utc)
        )
        
        db.add(league)
        db.commit()
        db.refresh(league)
        
        # Automatically add creator as participant
        LeagueService.join_league_by_id(db, league.id, user_id)
        
        logger.info(f"Created league '{name}' by user {user_id}")
        return league
    
    @staticmethod
    def join_league_by_code(db: Session, join_code: str, user_id: int) -> Dict:
        """Join a league using a join code."""
        
        # Find league by join code
        league = db.query(FantasyLeague).filter(
            FantasyLeague.join_code == join_code.upper()
        ).first()
        
        if not league:
            raise ValueError("Invalid join code")
        
        return LeagueService.join_league_by_id(db, league.id, user_id)
    
    @staticmethod
    def join_league_by_id(db: Session, league_id: int, user_id: int) -> Dict:
        """Join a league by league ID."""
        
        # Get league
        league = db.query(FantasyLeague).filter(FantasyLeague.id == league_id).first()
        if not league:
            raise ValueError("League not found")
        
        # Check if user already in league
        existing_participant = db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.league_id == league_id,
            FantasyLeagueParticipant.user_id == user_id
        ).first()
        
        if existing_participant:
            raise ValueError("You are already a member of this league")
        
        # Check if league is full
        current_participants = db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.league_id == league_id
        ).count()
        
        if current_participants >= league.max_participants:
            raise ValueError("League is full")
        
        # Get user's active fantasy team
        user_team = db.query(FantasyTeam).filter(
            FantasyTeam.user_id == user_id
        ).first()
        
        if not user_team:
            raise ValueError("You need to create a fantasy team first")
        
        # Add participant
        participant = FantasyLeagueParticipant(
            league_id=league_id,
            user_id=user_id,
            fantasy_team_id=user_team.id
        )
        
        db.add(participant)
        db.commit()
        
        logger.info(f"User {user_id} joined league {league.name}")
        
        return {
            'league_id': league_id,
            'league_name': league.name,
            'team_id': user_team.id,
            'team_name': user_team.name,
            'participants': current_participants + 1
        }
    
    @staticmethod
    def leave_league(db: Session, league_id: int, user_id: int) -> bool:
        """Leave a league."""
        
        # Find participant record
        participant = db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.league_id == league_id,
            FantasyLeagueParticipant.user_id == user_id
        ).first()
        
        if not participant:
            raise ValueError("You are not a member of this league")
        
        # Check if user is the creator
        league = db.query(FantasyLeague).filter(FantasyLeague.id == league_id).first()
        if league and league.creator_id == user_id:
            # If creator leaves, transfer ownership or delete league
            remaining_participants = db.query(FantasyLeagueParticipant).filter(
                FantasyLeagueParticipant.league_id == league_id,
                FantasyLeagueParticipant.user_id != user_id
            ).first()
            
            if remaining_participants:
                # Transfer ownership to next participant
                league.creator_id = remaining_participants.user_id
                db.commit()
            else:
                # Delete empty league
                db.delete(league)
        
        # Remove participant
        db.delete(participant)
        db.commit()
        
        logger.info(f"User {user_id} left league {league_id}")
        return True
    
    @staticmethod
    def get_user_leagues(db: Session, user_id: int) -> List[Dict]:
        """Get all leagues a user is participating in."""
        
        participants = db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.user_id == user_id
        ).all()
        
        leagues = []
        for participant in participants:
            league = participant.league
            participant_count = db.query(FantasyLeagueParticipant).filter(
                FantasyLeagueParticipant.league_id == league.id
            ).count()
            
            leagues.append({
                'id': league.id,
                'name': league.name,
                'description': league.description,
                'is_private': league.is_private,
                'is_creator': league.creator_id == user_id,
                'participants': participant_count,
                'max_participants': league.max_participants,
                'created_at': league.created_at.isoformat(),
                'join_code': league.join_code if league.creator_id == user_id else None
            })
        
        return leagues
    
    @staticmethod
    def get_public_leagues(db: Session, skip: int = 0, limit: int = 20) -> List[Dict]:
        """Get public leagues that users can join."""
        
        leagues = db.query(FantasyLeague).filter(
            FantasyLeague.is_private == False
        ).offset(skip).limit(limit).all()
        
        public_leagues = []
        for league in leagues:
            participant_count = db.query(FantasyLeagueParticipant).filter(
                FantasyLeagueParticipant.league_id == league.id
            ).count()
            
            if participant_count < league.max_participants:  # Only show non-full leagues
                public_leagues.append({
                    'id': league.id,
                    'name': league.name,
                    'description': league.description,
                    'participants': participant_count,
                    'max_participants': league.max_participants,
                    'created_at': league.created_at.isoformat()
                })
        
        return public_leagues
    
    @staticmethod
    def get_league_leaderboard(db: Session, league_id: int, user_id: int) -> Dict:
        """Get league leaderboard with team rankings."""
        
        # Verify user is in league
        participant = db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.league_id == league_id,
            FantasyLeagueParticipant.user_id == user_id
        ).first()
        
        if not participant:
            raise ValueError("You are not a member of this league")
        
        # Get league info
        league = db.query(FantasyLeague).filter(FantasyLeague.id == league_id).first()
        
        # Get all participants with their teams and points
        participants = db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.league_id == league_id
        ).all()
        
        leaderboard = []
        for participant in participants:
            user = participant.user
            team = participant.fantasy_team
            
            leaderboard.append({
                'user_id': user.id,
                'user_name': user.name,
                'team_id': team.id,
                'team_name': team.name,
                'total_points': team.total_points,
                'is_current_user': user.id == user_id
            })
        
        # Sort by points (descending)
        leaderboard.sort(key=lambda x: x['total_points'], reverse=True)
        
        # Add rankings
        for i, entry in enumerate(leaderboard):
            entry['rank'] = i + 1
        
        return {
            'league': {
                'id': league.id,
                'name': league.name,
                'description': league.description,
                'participants': len(leaderboard),
                'max_participants': league.max_participants
            },
            'leaderboard': leaderboard,
            'user_rank': next((entry['rank'] for entry in leaderboard if entry['is_current_user']), None)
        }
    
    @staticmethod
    def update_league(db: Session, league_id: int, user_id: int, 
                     name: Optional[str] = None, description: Optional[str] = None,
                     max_participants: Optional[int] = None) -> FantasyLeague:
        """Update league settings (creator only)."""
        
        league = db.query(FantasyLeague).filter(FantasyLeague.id == league_id).first()
        if not league:
            raise ValueError("League not found")
        
        if league.creator_id != user_id:
            raise ValueError("Only league creator can update settings")
        
        # Update fields
        if name is not None:
            league.name = name
        if description is not None:
            league.description = description
        if max_participants is not None:
            current_participants = db.query(FantasyLeagueParticipant).filter(
                FantasyLeagueParticipant.league_id == league_id
            ).count()
            
            if max_participants < current_participants:
                raise ValueError(f"Cannot reduce max participants below current count ({current_participants})")
            
            league.max_participants = max_participants
        
        db.commit()
        db.refresh(league)
        
        logger.info(f"League {league_id} updated by user {user_id}")
        return league


# Global service instance
league_service = LeagueService()
