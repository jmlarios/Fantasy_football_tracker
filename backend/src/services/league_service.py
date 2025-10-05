from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from src.models import (
    FantasyLeague, FantasyTeam, User, FantasyLeagueParticipant, LeagueTeam,
    LeagueTeamPlayer, Player, FantasyTeamPlayer
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
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    
    @staticmethod
    def auto_generate_squad(db: Session, league_team_id: int, league_id: int, fantasy_team_id: int) -> None:
        """
        Automatically generate a valid starting squad for a league team.
        Squad composition: 1 GK, 4 DEF, 4 MID, 2 FWD (11 total players)
        Players are assigned for free (don't affect budget).
        """
        squad_requirements = {
            'GK': 1,
            'DEF': 4,
            'MID': 4,
            'FWD': 2
        }
        
        players_added = []
        
        for position, count in squad_requirements.items():
            # Get available players for this position that aren't already in this league
            # Use random ordering instead of price-based selection
            available_players = db.query(Player).filter(
                Player.position == position,
                Player.is_active == True,
                ~Player.id.in_(
                    db.query(LeagueTeamPlayer.player_id).filter(
                        LeagueTeamPlayer.league_id == league_id
                    )
                )
            ).order_by(func.random()).limit(count).all()  # Random selection
            
            if len(available_players) < count:
                logger.warning(f"Not enough {position} players available")
                continue
            
            # Add randomly selected players
            for player in available_players:
                
                # Add player to league team (league-specific)
                league_team_player = LeagueTeamPlayer(
                    league_team_id=league_team_id,
                    player_id=player.id,
                    league_id=league_id,
                    position_in_team=position,
                    is_captain=False,
                    is_vice_captain=False
                )
                db.add(league_team_player)
                
                # ALSO add player to the general FantasyTeam (so it shows in "My Teams")
                fantasy_team_player = FantasyTeamPlayer(
                    fantasy_team_id=fantasy_team_id,
                    player_id=player.id,
                    position_in_team=position,
                    is_captain=False,
                    is_vice_captain=False
                )
                db.add(fantasy_team_player)
                
                players_added.append(f"{player.name} ({position})")
        
        db.flush()
    
    @staticmethod
    def create_league(db: Session, user_id: int, name: str, description: Optional[str] = None,
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
        
        # Automatically add creator as participant with custom team name
        LeagueService.join_league_by_id(db, league.id, user_id, team_name)
        
        return league
    
    @staticmethod
    def join_league_by_code(db: Session, join_code: str, user_id: int, team_name: Optional[str] = None) -> Dict:
        """Join a league using a join code with optional custom team name."""
        
        # Find league by join code
        league = db.query(FantasyLeague).filter(
            FantasyLeague.join_code == join_code.upper()
        ).first()
        
        if not league:
            raise ValueError("Invalid join code")
        
        return LeagueService.join_league_by_id(db, league.id, user_id, team_name)
    
    @staticmethod
    def join_league_by_id(db: Session, league_id: int, user_id: int, team_name: Optional[str] = None) -> Dict:
        """Join a league by league ID with optional custom team name."""
        
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
        
        # Always create a new fantasy team for each league
        user = db.query(User).filter(User.id == user_id).first()
        default_team_name = team_name if team_name else f"{user.name}'s Team"
        
        user_team = FantasyTeam(
            user_id=user_id,
            name=default_team_name
        )
        db.add(user_team)
        db.flush()
        
        # Create league-specific team entry
        league_team = LeagueTeam(
            league_id=league_id,
            fantasy_team_id=user_team.id,
            team_name=team_name if team_name else user_team.name
        )
        db.add(league_team)
        db.flush()  # Flush to get the league_team.id
        
        # Auto-generate a squad for this league team (11 players, free of charge)
        LeagueService.auto_generate_squad(db, league_team.id, league_id, user_team.id)
        
        # Add participant with league_team_id
        participant = FantasyLeagueParticipant(
            league_id=league_id,
            user_id=user_id,
            fantasy_team_id=user_team.id,
            league_team_id=league_team.id
        )
        
        db.add(participant)
        db.commit()
        
        return {
            'league_id': league_id,
            'league_name': league.name,
            'team_id': user_team.id,
            'team_name': league_team.team_name,
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
        
        return league
    
    @staticmethod
    def delete_league(db: Session, league_id: int, user_id: int) -> bool:
        """Delete a league (creator only)."""
        
        league = db.query(FantasyLeague).filter(FantasyLeague.id == league_id).first()
        if not league:
            raise ValueError("League not found")
        
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
    
    @staticmethod
    def update_league_team_name(db: Session, league_id: int, user_id: int, new_team_name: str) -> Dict:
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
