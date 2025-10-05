from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from src.models import FantasyTeam, FantasyTeamPlayer, Player, User
import logging

logger = logging.getLogger(__name__)


class FantasyTeamService:
    """Service for managing fantasy teams and player selections."""
    
    @staticmethod
    def create_fantasy_team(db: Session, user_id: int, team_name: str) -> FantasyTeam:
        # Check if user already has a team with this name
        existing_team = db.query(FantasyTeam).filter(
            FantasyTeam.user_id == user_id,
            FantasyTeam.name == team_name
        ).first()
        
        if existing_team:
            raise ValueError(f"You already have a team named '{team_name}'")
        
        # Create new fantasy team
        fantasy_team = FantasyTeam(
            user_id=user_id,
            name=team_name,
            total_points=0.0
        )
        
        db.add(fantasy_team)
        db.commit()
        db.refresh(fantasy_team)
        
        return fantasy_team
    
    @staticmethod
    def get_user_teams(db: Session, user_id: int) -> List[FantasyTeam]:
        return db.query(FantasyTeam).filter(FantasyTeam.user_id == user_id).all()
    
    @staticmethod
    def get_team_with_players(db: Session, team_id: int, user_id: int) -> Optional[Dict]:
        team = db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == user_id
        ).first()
        
        if not team:
            return None
        
        # Get team players with their details
        team_players = db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == team_id
        ).all()
        
        players_data = []
        for team_player in team_players:
            player = db.query(Player).filter(Player.id == team_player.player_id).first()
            if player:
                players_data.append({
                    'id': player.id,
                    'name': player.name,
                    'team': player.team,
                    'position': player.position,
                    'is_captain': team_player.is_captain,
                    'is_vice_captain': team_player.is_vice_captain,
                    'position_in_team': team_player.position_in_team
                })
        
        return {
            'team': team,
            'players': players_data,
            'player_count': len(players_data)
        }
    
    @staticmethod
    def add_player_to_team(db: Session, team_id: int, player_id: int, user_id: int) -> FantasyTeamPlayer:
        # Verify team ownership
        team = db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == user_id
        ).first()
        
        if not team:
            raise ValueError("Team not found or access denied")
        
        # Check if player exists
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            raise ValueError("Player not found")
        
        # Check if player is already in team
        existing = db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == team_id,
            FantasyTeamPlayer.player_id == player_id
        ).first()
        
        if existing:
            raise ValueError("Player is already in your team")
        
        # Check team size limit
        current_players = db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == team_id
        ).count()
        
        if current_players >= 11:
            raise ValueError("Team is full (maximum 11 players)")
        
        # Add player to team
        team_player = FantasyTeamPlayer(
            fantasy_team_id=team_id,
            player_id=player_id,
            position_in_team=player.position,  # Use player's actual position
            is_captain=False,
            is_vice_captain=False
        )
        
        db.add(team_player)
        db.commit()
        db.refresh(team_player)
        
        return team_player
    
    @staticmethod
    def remove_player_from_team(db: Session, team_id: int, player_id: int, user_id: int) -> bool:
        # Verify team ownership
        team = db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == user_id
        ).first()
        
        if not team:
            raise ValueError("Team not found or access denied")
        
        # Find and remove team player
        team_player = db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == team_id,
            FantasyTeamPlayer.player_id == player_id
        ).first()
        
        if not team_player:
            raise ValueError("Player not found in team")
        
        db.delete(team_player)
        db.commit()
        
        return True
    
    @staticmethod
    def set_captain(db: Session, team_id: int, player_id: int, user_id: int, is_vice: bool = False) -> bool:
        # Verify team ownership
        team = db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == user_id
        ).first()
        
        if not team:
            raise ValueError("Team not found or access denied")
        
        # Find the player in team
        team_player = db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == team_id,
            FantasyTeamPlayer.player_id == player_id
        ).first()
        
        if not team_player:
            raise ValueError("Player not found in team")
        
        if is_vice:
            # Clear existing vice-captain
            db.query(FantasyTeamPlayer).filter(
                FantasyTeamPlayer.fantasy_team_id == team_id
            ).update({FantasyTeamPlayer.is_vice_captain: False})
            
            # Set new vice-captain
            team_player.is_vice_captain = True
        else:
            # Clear existing captain
            db.query(FantasyTeamPlayer).filter(
                FantasyTeamPlayer.fantasy_team_id == team_id
            ).update({FantasyTeamPlayer.is_captain: False})
            
            # Set new captain
            team_player.is_captain = True
        
        db.commit()
        return True
    
    @staticmethod
    def validate_team_formation(db: Session, team_id: int) -> Dict:
        """Validate team formation according to LaLiga fantasy rules."""
        team_players = db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == team_id
        ).all()
        
        # Count players by position
        position_counts = {'GK': 0, 'DEF': 0, 'MID': 0, 'FWD': 0}
        
        for team_player in team_players:
            position = team_player.position_in_team
            if position in position_counts:
                position_counts[position] += 1
        
        # LaLiga formation requirements
        requirements = {
            'GK': {'min': 1, 'max': 1},    # Exactly 1 goalkeeper
            'DEF': {'min': 3, 'max': 5},   # 3-5 defenders
            'MID': {'min': 2, 'max': 5},   # 2-5 midfielders
            'FWD': {'min': 1, 'max': 3}    # 1-3 forwards
        }
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'position_counts': position_counts,
            'requirements': requirements,
            'total_players': sum(position_counts.values())
        }
        
        # Check total players
        if validation_result['total_players'] != 11:
            validation_result['is_valid'] = False
            if validation_result['total_players'] < 11:
                validation_result['errors'].append(f"Team needs {11 - validation_result['total_players']} more players")
            else:
                validation_result['errors'].append(f"Team has too many players ({validation_result['total_players']}/11)")
        
        # Check position requirements
        for position, req in requirements.items():
            count = position_counts[position]
            if count < req['min']:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"Need at least {req['min']} {position}, found {count}")
            elif count > req['max']:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"Maximum {req['max']} {position} allowed, found {count}")
        
        # Check for captain
        has_captain = any(tp.is_captain for tp in team_players)
        if not has_captain and validation_result['total_players'] > 0:
            validation_result['warnings'].append("No captain selected")
        
        return validation_result


# Global service instance
fantasy_team_service = FantasyTeamService()
