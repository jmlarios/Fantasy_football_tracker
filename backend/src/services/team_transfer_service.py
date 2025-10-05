from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from src.models import (
    FantasyTeam, FantasyTeamPlayer, Player, Matchday, 
    TransferHistory, User
)

logger = logging.getLogger(__name__)


class TransferService:
    """Service for handling player transfers with budget and penalty management."""
    
    # Transfer rules configuration
    TRANSFER_RULES = {
        'max_free_transfers_per_matchday': 2,  # Default free transfers
        'penalty_points_per_extra_transfer': -4,  # Points deducted for each extra transfer
        'min_team_size': 11,  # Minimum players in team
        'max_team_size': 14,  # Maximum players in team
        'position_limits': {
            'GK': {'min': 1, 'max': 2},
            'DEF': {'min': 3, 'max': 5},
            'MID': {'min': 2, 'max': 5},
            'FWD': {'min': 1, 'max': 3}
        }
    }
    
    @staticmethod
    def can_make_transfer(db: Session, team_id: int, user_id: int) -> Dict:
        """
        Check if user can make transfers right now.
        
        Returns:
            Dict with can_transfer bool and reasons
        """
        # Verify team ownership
        team = db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == user_id
        ).first()
        
        if not team:
            return {
                'can_transfer': False,
                'reason': 'Team not found or access denied'
            }
        
        # Check if transfers are open (no active matchday)
        current_matchday = db.query(Matchday).filter(
            Matchday.is_active == True
        ).first()
        
        if current_matchday and current_matchday.is_transfer_locked:
            return {
                'can_transfer': False,
                'reason': 'Transfers are locked during active matchday',
                'next_transfer_window': current_matchday.end_date.isoformat()
            }
        
        return {
            'can_transfer': True,
            'reason': 'Transfers are open'
        }
    
    @staticmethod
    def get_transfer_status(db: Session, team_id: int, user_id: int) -> Dict:
        """
        Get comprehensive transfer status for a team.
        
        Returns:
            Dict with transfer allowances, budget, penalties, etc.
        """
        team = db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == user_id
        ).first()
        
        if not team:
            raise ValueError("Team not found")
        
        # Get current or next matchday
        next_matchday = db.query(Matchday).filter(
            Matchday.is_finished == False
        ).order_by(Matchday.start_date.asc()).first()
        
        if not next_matchday:
            return {
                'can_transfer': False,
                'reason': 'No upcoming matchday found'
            }
        
        # Count transfers made for current matchday
        transfers_made = db.query(TransferHistory).filter(
            TransferHistory.fantasy_team_id == team_id,
            TransferHistory.matchday_id == next_matchday.id
        ).count()
        
        free_transfers_available = max(0, next_matchday.free_transfers - transfers_made)
        
        return {
            'team_id': team_id,
            'matchday_number': next_matchday.matchday_number,
            'total_budget': team.total_budget,
            'budget_used': team.current_budget_used,
            'remaining_budget': team.remaining_budget,
            'free_transfers_available': free_transfers_available,
            'transfers_made_this_matchday': transfers_made,
            'penalty_per_extra_transfer': TransferService.TRANSFER_RULES['penalty_points_per_extra_transfer'],
            'transfer_deadline': next_matchday.deadline.isoformat(),
            'transfers_locked': next_matchday.is_transfer_locked
        }
    
    @staticmethod
    def validate_transfer(db: Session, team_id: int, player_in_id: Optional[int], 
                         player_out_id: Optional[int], user_id: int) -> Dict:
        """
        Validate a proposed transfer before execution.
        
        Args:
            team_id: Fantasy team ID
            player_in_id: Player to add (None for selling only)
            player_out_id: Player to remove (None for buying only)
            user_id: User making the transfer
            
        Returns:
            Dict with validation results
        """
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'cost_breakdown': {}
        }
        
        # Get team
        team = db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == user_id
        ).first()
        
        if not team:
            validation['is_valid'] = False
            validation['errors'].append("Team not found or access denied")
            return validation
        
        # Check transfer window
        transfer_check = TransferService.can_make_transfer(db, team_id, user_id)
        if not transfer_check['can_transfer']:
            validation['is_valid'] = False
            validation['errors'].append(transfer_check['reason'])
            return validation
        
        # Get players
        player_in = None
        player_out = None
        
        if player_in_id:
            player_in = db.query(Player).filter(Player.id == player_in_id).first()
            if not player_in:
                validation['is_valid'] = False
                validation['errors'].append(f"Player to buy (ID: {player_in_id}) not found")
        
        if player_out_id:
            player_out = db.query(Player).filter(Player.id == player_out_id).first()
            if not player_out:
                validation['is_valid'] = False
                validation['errors'].append(f"Player to sell (ID: {player_out_id}) not found")
            
            # Check if player is actually in the team
            team_player = db.query(FantasyTeamPlayer).filter(
                FantasyTeamPlayer.fantasy_team_id == team_id,
                FantasyTeamPlayer.player_id == player_out_id
            ).first()
            
            if not team_player:
                validation['is_valid'] = False
                validation['errors'].append("Player to sell is not in your team")
        
        if not validation['is_valid']:
            return validation
        
        # Calculate cost
        player_in_cost = player_in.price if player_in else 0.0
        player_out_value = player_out.price if player_out else 0.0
        net_cost = player_in_cost - player_out_value
        
        validation['cost_breakdown'] = {
            'player_in_cost': player_in_cost,
            'player_out_value': player_out_value,
            'net_cost': net_cost,
            'current_budget': team.remaining_budget
        }
        
        # Check budget
        if net_cost > team.remaining_budget:
            validation['is_valid'] = False
            validation['errors'].append(f"Insufficient budget. Need {net_cost:,.0f}, have {team.remaining_budget:,.0f}")
        
        # Check team size limits
        current_team_size = len(team.team_players)
        
        if player_in and player_out:
            # Swap - no size change
            pass
        elif player_in and not player_out:
            # Buying only
            if current_team_size >= TransferService.TRANSFER_RULES['max_team_size']:
                validation['is_valid'] = False
                validation['errors'].append(f"Team is full ({current_team_size}/{TransferService.TRANSFER_RULES['max_team_size']})")
        elif player_out and not player_in:
            # Selling only
            if current_team_size <= TransferService.TRANSFER_RULES['min_team_size']:
                validation['is_valid'] = False
                validation['errors'].append(f"Team too small ({current_team_size}/{TransferService.TRANSFER_RULES['min_team_size']})")
        
        # Check position limits if buying
        if player_in:
            position_counts = TransferService._count_team_positions(team.team_players)
            
            # Adjust for transfer
            if player_out:
                position_counts[player_out.position] -= 1
            position_counts[player_in.position] += 1
            
            limits = TransferService.TRANSFER_RULES['position_limits']
            for position, count in position_counts.items():
                if position in limits:
                    if count > limits[position]['max']:
                        validation['is_valid'] = False
                        validation['errors'].append(f"Too many {position} players ({count}/{limits[position]['max']})")
                    elif count < limits[position]['min']:
                        validation['warnings'].append(f"Few {position} players ({count}/{limits[position]['min']})")
        
        return validation
    
    @staticmethod
    def execute_transfer(db: Session, team_id: int, player_in_id: Optional[int], 
                        player_out_id: Optional[int], user_id: int) -> Dict:
        """
        Execute a validated transfer.
        
        Returns:
            Dict with transfer results
        """
        # Validate first
        validation = TransferService.validate_transfer(db, team_id, player_in_id, player_out_id, user_id)
        if not validation['is_valid']:
            raise ValueError(f"Transfer validation failed: {', '.join(validation['errors'])}")
        
        team = db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == user_id
        ).first()
        
        # Get current matchday
        current_matchday = db.query(Matchday).filter(
            Matchday.is_finished == False
        ).order_by(Matchday.start_date.asc()).first()
        
        # Count existing transfers
        transfers_made = db.query(TransferHistory).filter(
            TransferHistory.fantasy_team_id == team_id,
            TransferHistory.matchday_id == current_matchday.id
        ).count()
        
        # Calculate penalty
        free_transfers_available = max(0, current_matchday.free_transfers - transfers_made)
        is_free_transfer = free_transfers_available > 0
        penalty_points = 0.0 if is_free_transfer else TransferService.TRANSFER_RULES['penalty_points_per_extra_transfer']
        
        try:
            # Remove player from team
            if player_out_id:
                db.query(FantasyTeamPlayer).filter(
                    FantasyTeamPlayer.fantasy_team_id == team_id,
                    FantasyTeamPlayer.player_id == player_out_id
                ).delete()
            
            # Add player to team
            if player_in_id:
                player_in = db.query(Player).filter(Player.id == player_in_id).first()
                
                new_team_player = FantasyTeamPlayer(
                    fantasy_team_id=team_id,
                    player_id=player_in_id,
                    position_in_team=player_in.position,
                    is_captain=False,
                    is_vice_captain=False,
                    added_for_matchday=current_matchday.matchday_number
                )
                db.add(new_team_player)
            
            # Record transfer history
            transfer_record = TransferHistory(
                fantasy_team_id=team_id,
                matchday_id=current_matchday.id,
                player_in_id=player_in_id,
                player_out_id=player_out_id,
                transfer_cost=validation['cost_breakdown']['net_cost'],
                penalty_points=penalty_points,
                is_free_transfer=is_free_transfer
            )
            db.add(transfer_record)
            
            # Apply penalty to team points if needed
            if penalty_points < 0:
                team.total_points += penalty_points  # penalty_points is negative
            
            db.commit()
            
            logger.info(f"Transfer executed: Team {team_id}, In: {player_in_id}, Out: {player_out_id}, Penalty: {penalty_points}")
            
            return {
                'success': True,
                'transfer_id': transfer_record.id,
                'penalty_points': penalty_points,
                'is_free_transfer': is_free_transfer,
                'remaining_budget': team.remaining_budget,
                'message': 'Transfer completed successfully'
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Transfer execution failed: {e}")
            raise
    
    @staticmethod
    def get_transfer_history(db: Session, team_id: int, user_id: int, 
                           limit: int = 50) -> List[Dict]:
        """Get transfer history for a team."""
        team = db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == user_id
        ).first()
        
        if not team:
            raise ValueError("Team not found")
        
        transfers = db.query(TransferHistory).filter(
            TransferHistory.fantasy_team_id == team_id
        ).order_by(TransferHistory.created_at.desc()).limit(limit).all()
        
        history = []
        for transfer in transfers:
            history.append({
                'id': transfer.id,
                'matchday_number': transfer.matchday.matchday_number if transfer.matchday else None,
                'player_in': {
                    'id': transfer.player_in.id,
                    'name': transfer.player_in.name,
                    'team': transfer.player_in.team,
                    'position': transfer.player_in.position,
                    'price': transfer.player_in.price
                } if transfer.player_in else None,
                'player_out': {
                    'id': transfer.player_out.id,
                    'name': transfer.player_out.name,
                    'team': transfer.player_out.team,
                    'position': transfer.player_out.position,
                    'price': transfer.player_out.price
                } if transfer.player_out else None,
                'transfer_cost': transfer.transfer_cost,
                'penalty_points': transfer.penalty_points,
                'is_free_transfer': transfer.is_free_transfer,
                'created_at': transfer.created_at.isoformat()
            })
        
        return history
    
    @staticmethod
    def _count_team_positions(team_players: List[FantasyTeamPlayer]) -> Dict[str, int]:
        counts = {'GK': 0, 'DEF': 0, 'MID': 0, 'FWD': 0}
        for tp in team_players:
            if tp.player and tp.player.position in counts:
                counts[tp.player.position] += 1
        return counts


# Global service instance
transfer_service = TransferService()
