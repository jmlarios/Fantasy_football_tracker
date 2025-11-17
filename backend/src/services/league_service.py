from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from src.models import (
    FantasyLeague,
    User,
    FantasyLeagueParticipant,
    LeagueTeam,
)
import logging
import secrets
import string
from datetime import datetime, timezone

from src.services.league.team_factory import TeamFactory
from src.services.league.roster_generator import RosterGenerator
from src.services.league.membership import LeagueMembershipService

logger = logging.getLogger(__name__)

class LeagueService:
    """Service for managing fantasy leagues and participants."""
    
    def __init__(
        self,
        team_factory: Optional[TeamFactory] = None,
        roster_generator: Optional[RosterGenerator] = None,
        membership_service: Optional[LeagueMembershipService] = None
    ) -> None:
        self._team_factory = team_factory or TeamFactory(logger)
        self._roster_generator = roster_generator or RosterGenerator(logger=logger)
        self._membership = membership_service or LeagueMembershipService(logger)
        self._logger = logger
    
    @staticmethod
    def generate_join_code() -> str:
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    
    def _get_league(self, db: Session, league_id: int) -> FantasyLeague:
        league = db.query(FantasyLeague).filter(FantasyLeague.id == league_id).first()
        if not league:
            raise ValueError("League not found")
        return league
    
    def create_league(self, db: Session, user_id: int, name: str, description: Optional[str] = None,
                     is_private: bool = False, max_participants: int = 20, team_name: Optional[str] = None) -> FantasyLeague:
        
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
                join_code = self.generate_join_code()
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
        
        # Automatically add creator as participant with custom team name
        self.join_league_by_id(db, league.id, user_id, team_name)
        
        return league
    
    def join_league_by_code(self, db: Session, join_code: str, user_id: int, team_name: Optional[str] = None) -> Dict:
        """Join a league using a join code with optional custom team name."""
        
        # Find league by join code
        league = db.query(FantasyLeague).filter(
            FantasyLeague.join_code == join_code.upper()
        ).first()
        
        if not league:
            raise ValueError("Invalid join code")
        
        return self.join_league_by_id(db, league.id, user_id, team_name)
    
    def join_league_by_id(self, db: Session, league_id: int, user_id: int, team_name: Optional[str] = None) -> Dict:
        """Join a league by league ID with optional custom team name."""

        league = self._get_league(db, league_id)
        current_participants = self._membership.ensure_user_can_join(
            db, league_id, user_id, league.max_participants
        )

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        default_team_name = team_name if team_name else f"{user.name}'s Team"
        user_team = self._team_factory.create_user_team(db, user_id, default_team_name)

        league_team = self._team_factory.create_league_team(
            db,
            league_id,
            user_team.id,
            team_name if team_name else user_team.name
        )

        self._roster_generator.generate_initial_squad(
            db,
            league_team_id=league_team.id,
            league_id=league_id,
            fantasy_team_id=user_team.id
        )

        self._team_factory.create_participant(
            db,
            league_id,
            user_id,
            user_team.id,
            league_team.id
        )

        db.commit()

        return {
            'league_id': league_id,
            'league_name': league.name,
            'team_id': user_team.id,
            'team_name': league_team.team_name,
            'participants': current_participants + 1
        }
    
    def leave_league(self, db: Session, league_id: int, user_id: int) -> bool:
        """Leave a league."""

        league = self._get_league(db, league_id)
        participant = self._membership.remove_participant(db, league_id, user_id)

        if not participant:
            raise ValueError("You are not a member of this league")

        self._membership.transfer_ownership_if_needed(db, league, user_id)
        db.commit()
        return True
    
    def get_user_leagues(self, db: Session, user_id: int) -> List[Dict]:
        """Get all leagues a user is participating in."""
        
        participants = db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.user_id == user_id
        ).all()
        
        leagues = []
        for participant in participants:
            league = participant.league
            participant_count = self._membership.count_participants(db, league.id)
            
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
    
    def get_public_leagues(self, db: Session, skip: int = 0, limit: int = 20) -> List[Dict]:
        """Get public leagues that users can join."""
        
        leagues = db.query(FantasyLeague).filter(
            FantasyLeague.is_private == False
        ).offset(skip).limit(limit).all()
        
        public_leagues = []
        for league in leagues:
            participant_count = self._membership.count_participants(db, league.id)
            
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
    
    def get_league_leaderboard(self, db: Session, league_id: int, user_id: int) -> Dict:
        """Get league leaderboard with team rankings."""
        
        # Verify user is in league
        participant = db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.league_id == league_id,
            FantasyLeagueParticipant.user_id == user_id
        ).first()
        
        if not participant:
            raise ValueError("You are not a member of this league")
        
        # Get league info
        league = self._get_league(db, league_id)
        
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
    
    def update_league(self, db: Session, league_id: int, user_id: int, 
                     name: Optional[str] = None, description: Optional[str] = None,
                     max_participants: Optional[int] = None) -> FantasyLeague:
        """Update league settings (creator only)."""
        
        league = self._get_league(db, league_id)
        
        if league.creator_id != user_id:
            raise ValueError("Only league creator can update settings")
        
        # Update fields
        if name is not None:
            league.name = name
        if description is not None:
            league.description = description
        if max_participants is not None:
            current_participants = self._membership.count_participants(db, league_id)
            
            if max_participants < current_participants:
                raise ValueError(f"Cannot reduce max participants below current count ({current_participants})")
            
            league.max_participants = max_participants
        
        db.commit()
        db.refresh(league)
        
        return league
    
    def delete_league(self, db: Session, league_id: int, user_id: int) -> bool:
        """Delete a league (creator only)."""
        
        league = self._get_league(db, league_id)
        
        if league.creator_id != user_id:
            raise ValueError("Only league creator can delete the league")
        
        # Delete all participants first (cascading)
        db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.league_id == league_id
        ).delete()
        
        # Delete the league
        db.delete(league)
        db.commit()
        
        return True
    
    def update_league_team_name(self, db: Session, league_id: int, user_id: int, new_team_name: str) -> Dict:
        """Update the team name for a specific league."""
        
        # Verify user is in the league
        participant = db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.league_id == league_id,
            FantasyLeagueParticipant.user_id == user_id
        ).first()
        
        if not participant:
            raise ValueError("You are not a member of this league")
        
        # Get the league team entry
        league_team = db.query(LeagueTeam).filter(
            LeagueTeam.league_id == league_id,
            LeagueTeam.fantasy_team_id == participant.fantasy_team_id
        ).first()
        
        if not league_team:
            raise ValueError("League team not found")
        
        # Update the team name
        league_team.team_name = new_team_name
        db.commit()
        db.refresh(league_team)
        
        return {
            'league_id': league_id,
            'team_id': participant.fantasy_team_id,
            'team_name': new_team_name
        }


# Global service instance
league_service = LeagueService()
