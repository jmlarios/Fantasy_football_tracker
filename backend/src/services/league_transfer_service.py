"""
Enhanced Transfer Service for handling free agent and user-to-user transfers.
Includes budget management, offer system, and validation.
"""

from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timezone, timedelta
import logging

from src.models import (
    FantasyTeam, FantasyTeamPlayer, Player, Matchday, 
    TransferHistory, TransferOffer, User, FantasyLeague,
    LeagueTeam, LeagueTeamPlayer
)

logger = logging.getLogger(__name__)


class FreeAgentTransferService:
    """Service for handling free agent transfers (players not owned in league)."""
    
    @staticmethod
    def get_available_players(db: Session, league_id: int, position: Optional[str] = None,
                               search: Optional[str] = None, min_price: Optional[float] = None,
                               max_price: Optional[float] = None) -> List[Dict]:
        """
        Get list of players available for free agent transfer in a league.
        
        Args:
            db: Database session
            league_id: League ID
            position: Filter by position (GK, DEF, MID, FWD)
            search: Search by player name or team
            min_price: Minimum price filter
            max_price: Maximum price filter
            
        Returns:
            List of available players with details
        """
        # Get all players owned in this league
        owned_player_ids = db.query(LeagueTeamPlayer.player_id).filter(
            LeagueTeamPlayer.league_id == league_id
        ).distinct().all()
        owned_ids = [pid[0] for pid in owned_player_ids]
        
        # Query for available players
        query = db.query(Player).filter(
            Player.is_active == True,
            ~Player.id.in_(owned_ids) if owned_ids else True
        )
        
        # Apply filters
        if position:
            query = query.filter(Player.position == position)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Player.name.ilike(search_pattern),
                    Player.team.ilike(search_pattern)
                )
            )
        
        if min_price is not None:
            query = query.filter(Player.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Player.price <= max_price)
        
        players = query.order_by(Player.price.desc()).all()
        
        return [{
            'id': p.id,
            'name': p.name,
            'team': p.team,
            'position': p.position,
            'price': p.price,
            'goals': p.goals,
            'assists': p.assists,
            'total_stats': {
                'goals': p.goals,
                'assists': p.assists,
                'yellow_cards': p.yellow_cards,
                'red_cards': p.red_cards,
                'minutes_played': p.minutes_played,
                'clean_sheets': p.clean_sheets
            }
        } for p in players]
    
    @staticmethod
    def check_player_availability(db: Session, league_id: int, player_id: int) -> Dict:
        """
        Check if a player is available for free agent transfer in a league.
        
        Returns:
            Dict with availability status and details
        """
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return {'available': False, 'reason': 'Player not found'}
        
        # Check if player is owned in this league
        is_owned = db.query(LeagueTeamPlayer).filter(
            LeagueTeamPlayer.league_id == league_id,
            LeagueTeamPlayer.player_id == player_id
        ).first() is not None
        
        if is_owned:
            owner_team = db.query(LeagueTeam).join(
                LeagueTeamPlayer, LeagueTeam.id == LeagueTeamPlayer.league_team_id
            ).filter(
                LeagueTeamPlayer.league_id == league_id,
                LeagueTeamPlayer.player_id == player_id
            ).first()
            
            return {
                'available': False,
                'reason': 'Player already owned in this league',
                'owned_by_team': owner_team.team_name if owner_team else 'Unknown'
            }
        
        return {
            'available': True,
            'player': {
                'id': player.id,
                'name': player.name,
                'team': player.team,
                'position': player.position,
                'price': player.price
            }
        }
    
    @staticmethod
    def validate_free_transfer(db: Session, league_id: int, team_id: int, 
                                player_in_id: int, player_out_id: Optional[int] = None) -> Dict:
        """
        Validate a free agent transfer before execution.
        
        Returns:
            Dict with validation results
        """
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'cost_breakdown': {}
        }
        
        # Get league team
        league_team = db.query(LeagueTeam).filter(
            LeagueTeam.id == team_id,
            LeagueTeam.league_id == league_id
        ).first()
        
        if not league_team:
            validation['is_valid'] = False
            validation['errors'].append("Team not found in this league")
            return validation
        
        # Check current squad size
        squad_size = db.query(LeagueTeamPlayer).filter(
            LeagueTeamPlayer.league_team_id == team_id
        ).count()
        
        # If team has 11 players, must provide player_out_id
        if squad_size >= 11 and not player_out_id:
            validation['is_valid'] = False
            validation['errors'].append("Team has 11 players. You must select a player to drop.")
            return validation
        
        # If team has less than 11 players and player_out_id is provided, warn but allow
        if squad_size < 11 and player_out_id:
            validation['warnings'].append(f"Team only has {squad_size} players. You can add without dropping anyone.")
        
        # Check if transfers are locked
        current_matchday = db.query(Matchday).filter(Matchday.is_active == True).first()
        if current_matchday and current_matchday.is_transfer_locked:
            validation['is_valid'] = False
            validation['errors'].append(f"Transfers locked until {current_matchday.end_date}")
            return validation
        
        # Get player in
        player_in = db.query(Player).filter(Player.id == player_in_id).first()
        if not player_in:
            validation['is_valid'] = False
            validation['errors'].append("Player to buy not found")
            return validation
        
        # Check player availability
        availability = FreeAgentTransferService.check_player_availability(db, league_id, player_in_id)
        if not availability['available']:
            validation['is_valid'] = False
            validation['errors'].append(availability['reason'])
            return validation
        
        # Only validate player_out if provided
        player_out = None
        if player_out_id:
            # Get player out
            player_out = db.query(Player).filter(Player.id == player_out_id).first()
            if not player_out:
                validation['is_valid'] = False
                validation['errors'].append("Player to sell not found")
                return validation
            
            # Check if player_out is in the team
            team_has_player = db.query(LeagueTeamPlayer).filter(
                LeagueTeamPlayer.league_team_id == team_id,
                LeagueTeamPlayer.player_id == player_out_id
            ).first()
            
            if not team_has_player:
                validation['is_valid'] = False
                validation['errors'].append(f"{player_out.name} is not in your team")
                return validation
        
        # Check position consistency (only if player_out exists)
        if player_out and player_in.position != player_out.position:
            validation['warnings'].append(
                f"Position change: {player_out.position} → {player_in.position}"
            )
        
        # Check budget
        player_out_price = player_out.price if player_out else 0
        cost = player_in.price - player_out_price
        if cost > league_team.remaining_budget:
            validation['is_valid'] = False
            validation['errors'].append(
                f"Insufficient budget. Need {cost:.2f}M, have {league_team.remaining_budget:.2f}M"
            )
        
        validation['cost_breakdown'] = {
            'player_in_price': player_in.price,
            'player_out_price': player_out_price,
            'net_cost': cost,
            'current_budget': league_team.remaining_budget,
            'budget_after_transfer': league_team.remaining_budget - cost
        }
        
        return validation
    
    @staticmethod
    def execute_free_transfer(db: Session, league_id: int, team_id: int,
                               player_in_id: int, player_out_id: Optional[int],
                               user_id: int) -> Dict:
        """
        Execute a free agent transfer.
        
        Returns:
            Dict with transfer result
        """
        # Validate first
        validation = FreeAgentTransferService.validate_free_transfer(
            db, league_id, team_id, player_in_id, player_out_id
        )
        
        if not validation['is_valid']:
            return {
                'success': False,
                'errors': validation['errors']
            }
        
        try:
            # Get league team and fantasy team
            league_team = db.query(LeagueTeam).filter(
                LeagueTeam.id == team_id,
                LeagueTeam.league_id == league_id
            ).first()
            
            fantasy_team = league_team.fantasy_team
            
            # Verify ownership
            if fantasy_team.user_id != user_id:
                return {
                    'success': False,
                    'errors': ['You do not own this team']
                }
            
            # Check if transfers are locked (only block if active matchday has locked transfers)
            current_matchday = db.query(Matchday).filter(Matchday.is_active == True).first()
            if current_matchday and current_matchday.is_transfer_locked:
                return {
                    'success': False,
                    'errors': [f'Transfers are locked during matchday {current_matchday.matchday_number}']
                }
            
            # Get players
            player_in = db.query(Player).filter(Player.id == player_in_id).first()
            player_out = db.query(Player).filter(Player.id == player_out_id).first() if player_out_id else None
            
            # Remove player out from league team (if specified)
            if player_out:
                league_player_out = db.query(LeagueTeamPlayer).filter(
                    LeagueTeamPlayer.league_team_id == team_id,
                    LeagueTeamPlayer.player_id == player_out_id
                ).first()
                
                if league_player_out:
                    db.delete(league_player_out)
                
                # Also remove from fantasy team
                fantasy_player_out = db.query(FantasyTeamPlayer).filter(
                    FantasyTeamPlayer.fantasy_team_id == fantasy_team.id,
                    FantasyTeamPlayer.player_id == player_out_id
                ).first()
                if fantasy_player_out:
                    db.delete(fantasy_player_out)
            
            # Get next matchday for tracking (not current active one)
            next_matchday = db.query(Matchday).filter(
                Matchday.is_finished == False
            ).order_by(Matchday.start_date.asc()).first()
            
            # Add player in to league team
            league_player_in = LeagueTeamPlayer(
                league_team_id=team_id,
                player_id=player_in_id,
                league_id=league_id,
                position_in_team=player_in.position,
                added_for_matchday=next_matchday.matchday_number if next_matchday else None
            )
            db.add(league_player_in)
            
            # Also add to fantasy team
            fantasy_player_in = FantasyTeamPlayer(
                fantasy_team_id=fantasy_team.id,
                player_id=player_in_id,
                position_in_team=player_in.position,
                added_for_matchday=next_matchday.matchday_number if next_matchday else None
            )
            db.add(fantasy_player_in)
            
            # Record transfer history
            player_out_price = player_out.price if player_out else 0
            transfer_cost = player_in.price - player_out_price
            transfer_history = TransferHistory(
                fantasy_team_id=fantasy_team.id,
                league_id=league_id,
                matchday_id=next_matchday.id if next_matchday else None,
                transfer_type='free_agent',
                player_in_id=player_in_id,
                player_out_id=player_out_id,
                transfer_cost=transfer_cost,
                is_free_transfer=True,
                penalty_points=0.0
            )
            db.add(transfer_history)
            
            db.commit()
            
            # Build response message
            if player_out:
                message = f'Successfully transferred {player_in.name} for {player_out.name}'
            else:
                message = f'Successfully added {player_in.name} to your team'
            
            return {
                'success': True,
                'message': message,
                'transfer': {
                    'player_in': {
                        'id': player_in.id,
                        'name': player_in.name,
                        'position': player_in.position,
                        'price': player_in.price
                    },
                    'player_out': {
                        'id': player_out.id,
                        'name': player_out.name,
                        'position': player_out.position,
                        'price': player_out.price
                    } if player_out else None,
                    'cost': transfer_cost,
                    'new_budget': league_team.remaining_budget - transfer_cost
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error executing free transfer: {e}")
            return {
                'success': False,
                'errors': [f'Transfer failed: {str(e)}']
            }


class UserTransferService:
    """Service for handling user-to-user transfers via offers."""
    
    @staticmethod
    def create_offer(db: Session, league_id: int, from_team_id: int,
                     to_team_id: int, player_id: int, offer_type: str,
                     money_offered: float = 0.0, player_offered_id: Optional[int] = None,
                     player_out_id: Optional[int] = None,
                     user_id: Optional[int] = None) -> Dict:
        """
        Create a transfer offer from one team to another.
        
        Args:
            league_id: League ID
            from_team_id: Team making the offer (buyer)
            to_team_id: Team receiving the offer (seller)
            player_id: Player being requested
            offer_type: 'money' or 'player_exchange'
            money_offered: Amount offered (for money offers)
            player_offered_id: Player offered in exchange (for player_exchange offers)
            player_out_id: Player to drop (for money offers)
            user_id: User creating the offer
            
        Returns:
            Dict with offer creation result
        """
        try:
            # Validate teams are in the same league
            from_team = db.query(LeagueTeam).filter(
                LeagueTeam.id == from_team_id,
                LeagueTeam.league_id == league_id
            ).first()
            
            to_team = db.query(LeagueTeam).filter(
                LeagueTeam.id == to_team_id,
                LeagueTeam.league_id == league_id
            ).first()
            
            if not from_team or not to_team:
                return {
                    'success': False,
                    'errors': ['One or both teams not found in this league']
                }
            
            # Verify ownership if user_id provided
            if user_id and from_team.fantasy_team.user_id != user_id:
                return {
                    'success': False,
                    'errors': ['You do not own the buying team']
                }
            
            # Check if same team
            if from_team_id == to_team_id:
                return {
                    'success': False,
                    'errors': ['Cannot make offer to your own team']
                }
            
            # Check if transfers are locked
            current_matchday = db.query(Matchday).filter(Matchday.is_active == True).first()
            if current_matchday and current_matchday.is_transfer_locked:
                return {
                    'success': False,
                    'errors': [f'Transfers locked until {current_matchday.end_date}']
                }
            
            # Get the player being requested
            player = db.query(Player).filter(Player.id == player_id).first()
            if not player:
                return {
                    'success': False,
                    'errors': ['Player not found']
                }
            
            # Check if player is owned by the target team
            player_owned = db.query(LeagueTeamPlayer).filter(
                LeagueTeamPlayer.league_team_id == to_team_id,
                LeagueTeamPlayer.player_id == player_id
            ).first()
            
            if not player_owned:
                return {
                    'success': False,
                    'errors': ['Player not owned by target team']
                }
            
            # Validate offer type
            if offer_type == 'money':
                if money_offered <= 0:
                    return {
                        'success': False,
                        'errors': ['Money offer must be greater than 0']
                    }
                
                # Check if buyer has enough budget
                if money_offered > from_team.remaining_budget:
                    return {
                        'success': False,
                        'errors': [f'Insufficient budget. Have {from_team.remaining_budget:.2f}M, need {money_offered:.2f}M']
                    }
                
                # Require player_out_id for money offers
                if not player_out_id:
                    return {
                        'success': False,
                        'errors': ['Money offers require selecting a player to drop from your squad']
                    }
                
                # Validate player_out is owned by buyer
                player_out_owned = db.query(LeagueTeamPlayer).filter(
                    LeagueTeamPlayer.league_team_id == from_team_id,
                    LeagueTeamPlayer.player_id == player_out_id
                ).first()
                
                if not player_out_owned:
                    return {
                        'success': False,
                        'errors': ['Player to drop is not in your squad']
                    }
                
            elif offer_type == 'player_exchange':
                if not player_offered_id:
                    return {
                        'success': False,
                        'errors': ['Player exchange requires a player to be offered']
                    }
                
                # Check if offered player is owned by buyer
                offered_player_owned = db.query(LeagueTeamPlayer).filter(
                    LeagueTeamPlayer.league_team_id == from_team_id,
                    LeagueTeamPlayer.player_id == player_offered_id
                ).first()
                
                if not offered_player_owned:
                    return {
                        'success': False,
                        'errors': ['Offered player not in your team']
                    }
                
            else:
                return {
                    'success': False,
                    'errors': ['Invalid offer type. Must be "money" or "player_exchange"']
                }
            
            # Check for existing pending offers for the same player
            existing_offer = db.query(TransferOffer).filter(
                TransferOffer.league_id == league_id,
                TransferOffer.from_team_id == from_team_id,
                TransferOffer.to_team_id == to_team_id,
                TransferOffer.player_id == player_id,
                TransferOffer.status == 'pending'
            ).first()
            
            if existing_offer:
                return {
                    'success': False,
                    'errors': ['You already have a pending offer for this player']
                }
            
            # Set expiry to next matchday deadline, or 7 days if no matchday
            next_matchday = db.query(Matchday).filter(
                Matchday.is_finished == False
            ).order_by(Matchday.start_date.asc()).first()
            
            from datetime import datetime, timedelta
            expires_at = next_matchday.deadline if next_matchday else datetime.now() + timedelta(days=7)
            
            # Create the offer
            offer = TransferOffer(
                league_id=league_id,
                from_team_id=from_team_id,
                to_team_id=to_team_id,
                player_id=player_id,
                offer_type=offer_type,
                money_offered=money_offered if offer_type == 'money' else 0.0,
                player_offered_id=player_offered_id if offer_type == 'player_exchange' else None,
                player_out_id=player_out_id if offer_type == 'money' else None,
                status='pending',
                budget_reserved=offer_type == 'money',  # Reserve budget for money offers
                expires_at=expires_at
            )
            
            db.add(offer)
            db.commit()
            db.refresh(offer)
            
            # Get player names for response
            player_offered = None
            if player_offered_id:
                player_offered = db.query(Player).filter(Player.id == player_offered_id).first()
            
            return {
                'success': True,
                'message': f'Offer created for {player.name}',
                'offer': {
                    'id': offer.id,
                    'player_requested': {
                        'id': player.id,
                        'name': player.name,
                        'position': player.position,
                        'price': player.price
                    },
                    'offer_type': offer_type,
                    'money_offered': money_offered if offer_type == 'money' else None,
                    'player_offered': {
                        'id': player_offered.id,
                        'name': player_offered.name,
                        'position': player_offered.position,
                        'price': player_offered.price
                    } if player_offered else None,
                    'expires_at': offer.expires_at.isoformat(),
                    'time_until_expiry': offer.time_until_expiry
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating transfer offer: {e}")
            return {
                'success': False,
                'errors': [f'Failed to create offer: {str(e)}']
            }
    
    @staticmethod
    def get_team_offers(db: Session, league_id: int, team_id: int,
                        offer_direction: str = 'received') -> List[Dict]:
        """
        Get transfer offers for a team (received or sent).
        
        Args:
            league_id: League ID
            team_id: Team ID (LeagueTeam ID)
            offer_direction: 'received' or 'sent'
            
        Returns:
            List of offers with details
        """
        if offer_direction == 'received':
            offers = db.query(TransferOffer).filter(
                TransferOffer.league_id == league_id,
                TransferOffer.to_team_id == team_id,
                TransferOffer.status == 'pending'
            ).all()
        else:  # sent
            offers = db.query(TransferOffer).filter(
                TransferOffer.league_id == league_id,
                TransferOffer.from_team_id == team_id,
                TransferOffer.status == 'pending'
            ).all()
        
        result = []
        for offer in offers:
            player = db.query(Player).filter(Player.id == offer.player_id).first()
            player_offered = None
            if offer.player_offered_id:
                player_offered = db.query(Player).filter(Player.id == offer.player_offered_id).first()
            
            from_team = db.query(LeagueTeam).filter(LeagueTeam.id == offer.from_team_id).first()
            to_team = db.query(LeagueTeam).filter(LeagueTeam.id == offer.to_team_id).first()
            
            result.append({
                'id': offer.id,
                'from_team': {
                    'id': from_team.id,
                    'name': from_team.team_name or from_team.fantasy_team.name,
                    'user_name': from_team.fantasy_team.user.name
                },
                'to_team': {
                    'id': to_team.id,
                    'name': to_team.team_name or to_team.fantasy_team.name,
                    'user_name': to_team.fantasy_team.user.name
                },
                'player_requested': {
                    'id': player.id,
                    'name': player.name,
                    'position': player.position,
                    'price': player.price,
                    'team': player.team
                },
                'offer_type': offer.offer_type,
                'money_offered': offer.money_offered if offer.offer_type == 'money' else None,
                'player_offered': {
                    'id': player_offered.id,
                    'name': player_offered.name,
                    'position': player_offered.position,
                    'price': player_offered.price,
                    'team': player_offered.team
                } if player_offered else None,
                'status': offer.status,
                'created_at': offer.created_at.isoformat(),
                'expires_at': offer.expires_at.isoformat(),
                'time_until_expiry': offer.time_until_expiry,
                'is_expired': offer.is_expired
            })
        
        return result
    
    @staticmethod
    def accept_offer(db: Session, offer_id: int, league_id: int,
                     user_id: Optional[int] = None) -> Dict:
        """
        Accept a transfer offer.
        
        Args:
            offer_id: Offer ID
            league_id: League ID
            user_id: User accepting (must own the selling team)
            
        Returns:
            Dict with acceptance result
        """
        try:
            offer = db.query(TransferOffer).filter(
                TransferOffer.id == offer_id,
                TransferOffer.league_id == league_id
            ).first()
            
            if not offer:
                return {
                    'success': False,
                    'errors': ['Offer not found']
                }
            
            # Verify ownership
            to_team = db.query(LeagueTeam).filter(LeagueTeam.id == offer.to_team_id).first()
            if user_id and to_team.fantasy_team.user_id != user_id:
                return {
                    'success': False,
                    'errors': ['You do not own the selling team']
                }
            
            # Check offer status
            if offer.status != 'pending':
                return {
                    'success': False,
                    'errors': [f'Offer already {offer.status}']
                }
            
            # Check if expired
            if offer.is_expired:
                offer.status = 'expired'
                db.commit()
                return {
                    'success': False,
                    'errors': ['Offer has expired']
                }
            
            # Execute the transfer based on offer type
            if offer.offer_type == 'money':
                result = UserTransferService._execute_money_transfer(db, offer)
            else:  # player_exchange
                result = UserTransferService._execute_player_exchange(db, offer)
            
            if result['success']:
                offer.status = 'accepted'
                offer.responded_at = datetime.now(timezone.utc)
                db.commit()
            
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error accepting offer: {e}")
            return {
                'success': False,
                'errors': [f'Failed to accept offer: {str(e)}']
            }
    
    @staticmethod
    def _execute_money_transfer(db: Session, offer: TransferOffer) -> Dict:
        """Execute a money-based transfer."""
        try:
            # Check if transfers are locked
            current_matchday = db.query(Matchday).filter(Matchday.is_active == True).first()
            if current_matchday and current_matchday.is_transfer_locked:
                return {'success': False, 'errors': ['Transfers are locked during active matchday']}
            
            from_team = db.query(LeagueTeam).filter(LeagueTeam.id == offer.from_team_id).first()
            to_team = db.query(LeagueTeam).filter(LeagueTeam.id == offer.to_team_id).first()
            player_in = db.query(Player).filter(Player.id == offer.player_id).first()
            player_out = db.query(Player).filter(Player.id == offer.player_out_id).first() if offer.player_out_id else None
            
            # Get next matchday for tracking
            next_matchday = db.query(Matchday).filter(
                Matchday.is_finished == False
            ).order_by(Matchday.start_date.asc()).first()
            
            # Remove player_out from buyer's team (if specified)
            if player_out:
                buyer_player_out = db.query(LeagueTeamPlayer).filter(
                    LeagueTeamPlayer.league_team_id == from_team.id,
                    LeagueTeamPlayer.player_id == player_out.id
                ).first()
                if buyer_player_out:
                    db.delete(buyer_player_out)
                
                fantasy_buyer_player_out = db.query(FantasyTeamPlayer).filter(
                    FantasyTeamPlayer.fantasy_team_id == from_team.fantasy_team_id,
                    FantasyTeamPlayer.player_id == player_out.id
                ).first()
                if fantasy_buyer_player_out:
                    db.delete(fantasy_buyer_player_out)
            
            # Remove player_in from seller's team
            seller_player = db.query(LeagueTeamPlayer).filter(
                LeagueTeamPlayer.league_team_id == to_team.id,
                LeagueTeamPlayer.player_id == player_in.id
            ).first()
            db.delete(seller_player)
            
            # Also delete from fantasy team
            fantasy_seller_player = db.query(FantasyTeamPlayer).filter(
                FantasyTeamPlayer.fantasy_team_id == to_team.fantasy_team_id,
                FantasyTeamPlayer.player_id == player_in.id
            ).first()
            if fantasy_seller_player:
                db.delete(fantasy_seller_player)
            
            # CRITICAL: Flush deletes to database before inserts to avoid unique constraint violations
            db.flush()
            
            # CRITICAL: Flush deletes to database before inserts to avoid unique constraint violations
            db.flush()
            
            # Add player_in to buyer's team
            buyer_player = LeagueTeamPlayer(
                league_team_id=from_team.id,
                player_id=player_in.id,
                league_id=offer.league_id,
                position_in_team=player_in.position,
                added_for_matchday=next_matchday.matchday_number if next_matchday else None
            )
            db.add(buyer_player)
            
            # Also add to fantasy team
            fantasy_buyer_player = FantasyTeamPlayer(
                fantasy_team_id=from_team.fantasy_team_id,
                player_id=player_in.id,
                position_in_team=player_in.position,
                added_for_matchday=next_matchday.matchday_number if next_matchday else None
            )
            db.add(fantasy_buyer_player)
            
            # Update budgets (seller gains money, buyer loses money)
            to_team.total_budget += offer.money_offered
            from_team.total_budget -= offer.money_offered
            
            # Record transfer history for both teams
            buyer_history = TransferHistory(
                fantasy_team_id=from_team.fantasy_team_id,
                league_id=offer.league_id,
                matchday_id=next_matchday.id if next_matchday else None,
                transfer_type='user_to_user',
                player_in_id=player_in.id,
                player_out_id=player_out.id if player_out else None,
                transfer_cost=-offer.money_offered,  # Negative because paying
                seller_team_id=to_team.fantasy_team_id,
                transfer_offer_id=offer.id,
                is_free_transfer=False
            )
            db.add(buyer_history)
            
            seller_history = TransferHistory(
                fantasy_team_id=to_team.fantasy_team_id,
                league_id=offer.league_id,
                matchday_id=next_matchday.id if next_matchday else None,
                transfer_type='user_to_user',
                player_in_id=None,
                player_out_id=player_in.id,
                transfer_cost=offer.money_offered,  # Positive because receiving
                seller_team_id=from_team.fantasy_team_id,
                transfer_offer_id=offer.id,
                is_free_transfer=False
            )
            db.add(seller_history)
            
            db.commit()
            
            return {
                'success': True,
                'message': f'{player_in.name} transferred for {offer.money_offered:.2f}M'
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error executing money transfer: {e}")
            return {'success': False, 'errors': [str(e)]}
    
    @staticmethod
    def _execute_player_exchange(db: Session, offer: TransferOffer) -> Dict:
        """Execute a player exchange transfer."""
        try:
            # Check if transfers are locked
            current_matchday = db.query(Matchday).filter(Matchday.is_active == True).first()
            if current_matchday and current_matchday.is_transfer_locked:
                return {'success': False, 'errors': ['Transfers are locked during active matchday']}
            
            from_team = db.query(LeagueTeam).filter(LeagueTeam.id == offer.from_team_id).first()
            to_team = db.query(LeagueTeam).filter(LeagueTeam.id == offer.to_team_id).first()
            player_requested = db.query(Player).filter(Player.id == offer.player_id).first()
            player_offered = db.query(Player).filter(Player.id == offer.player_offered_id).first()
            
            # Get next matchday for tracking
            next_matchday = db.query(Matchday).filter(
                Matchday.is_finished == False
            ).order_by(Matchday.start_date.asc()).first()
            
            # Swap players in league teams
            # Remove player_requested from to_team
            to_team_player = db.query(LeagueTeamPlayer).filter(
                LeagueTeamPlayer.league_team_id == to_team.id,
                LeagueTeamPlayer.player_id == player_requested.id
            ).first()
            db.delete(to_team_player)
            
            # Remove player_offered from from_team
            from_team_player = db.query(LeagueTeamPlayer).filter(
                LeagueTeamPlayer.league_team_id == from_team.id,
                LeagueTeamPlayer.player_id == player_offered.id
            ).first()
            db.delete(from_team_player)
            
            # Flush deletes to database before inserting
            db.flush()
            
            # Add player_requested to from_team
            new_from_team_player = LeagueTeamPlayer(
                league_team_id=from_team.id,
                player_id=player_requested.id,
                league_id=offer.league_id,
                position_in_team=player_requested.position,
                added_for_matchday=next_matchday.matchday_number if next_matchday else None
            )
            db.add(new_from_team_player)
            
            # Add player_offered to to_team
            new_to_team_player = LeagueTeamPlayer(
                league_team_id=to_team.id,
                player_id=player_offered.id,
                league_id=offer.league_id,
                position_in_team=player_offered.position,
                added_for_matchday=next_matchday.matchday_number if next_matchday else None
            )
            db.add(new_to_team_player)
            
            # Also swap in fantasy teams
            # Remove from fantasy teams
            fantasy_from_player = db.query(FantasyTeamPlayer).filter(
                FantasyTeamPlayer.fantasy_team_id == from_team.fantasy_team_id,
                FantasyTeamPlayer.player_id == player_offered.id
            ).first()
            if fantasy_from_player:
                db.delete(fantasy_from_player)
            
            fantasy_to_player = db.query(FantasyTeamPlayer).filter(
                FantasyTeamPlayer.fantasy_team_id == to_team.fantasy_team_id,
                FantasyTeamPlayer.player_id == player_requested.id
            ).first()
            if fantasy_to_player:
                db.delete(fantasy_to_player)
            
            # Add to fantasy teams
            new_fantasy_from = FantasyTeamPlayer(
                fantasy_team_id=from_team.fantasy_team_id,
                player_id=player_requested.id,
                position_in_team=player_requested.position,
                added_for_matchday=next_matchday.matchday_number if next_matchday else None
            )
            db.add(new_fantasy_from)
            
            new_fantasy_to = FantasyTeamPlayer(
                fantasy_team_id=to_team.fantasy_team_id,
                player_id=player_offered.id,
                position_in_team=player_offered.position,
                added_for_matchday=next_matchday.matchday_number if next_matchday else None
            )
            db.add(new_fantasy_to)
            
            # Record transfer history for both teams
            buyer_history = TransferHistory(
                fantasy_team_id=from_team.fantasy_team_id,
                league_id=offer.league_id,
                matchday_id=next_matchday.id if next_matchday else None,
                transfer_type='user_to_user',
                player_in_id=player_requested.id,
                player_out_id=player_offered.id,
                transfer_cost=0.0,
                seller_team_id=to_team.fantasy_team_id,
                transfer_offer_id=offer.id,
                is_free_transfer=False
            )
            db.add(buyer_history)
            
            seller_history = TransferHistory(
                fantasy_team_id=to_team.fantasy_team_id,
                league_id=offer.league_id,
                matchday_id=next_matchday.id if next_matchday else None,
                transfer_type='user_to_user',
                player_in_id=player_offered.id,
                player_out_id=player_requested.id,
                transfer_cost=0.0,
                seller_team_id=from_team.fantasy_team_id,
                transfer_offer_id=offer.id,
                is_free_transfer=False
            )
            db.add(seller_history)
            
            db.commit()
            
            return {
                'success': True,
                'message': f'Players exchanged: {player_requested.name} ↔ {player_offered.name}'
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error executing player exchange: {e}")
            return {'success': False, 'errors': [str(e)]}
    
    @staticmethod
    def reject_offer(db: Session, offer_id: int, league_id: int,
                     user_id: Optional[int] = None) -> Dict:
        """
        Reject a transfer offer.
        
        Args:
            offer_id: Offer ID
            league_id: League ID
            user_id: User rejecting (must own the selling team)
            
        Returns:
            Dict with rejection result
        """
        try:
            offer = db.query(TransferOffer).filter(
                TransferOffer.id == offer_id,
                TransferOffer.league_id == league_id
            ).first()
            
            if not offer:
                return {
                    'success': False,
                    'errors': ['Offer not found']
                }
            
            # Verify ownership
            to_team = db.query(LeagueTeam).filter(LeagueTeam.id == offer.to_team_id).first()
            if user_id and to_team.fantasy_team.user_id != user_id:
                return {
                    'success': False,
                    'errors': ['You do not own the selling team']
                }
            
            # Check offer status
            if offer.status != 'pending':
                return {
                    'success': False,
                    'errors': [f'Offer already {offer.status}']
                }
            
            # Reject the offer
            offer.status = 'rejected'
            offer.responded_at = datetime.now(timezone.utc)
            db.commit()
            
            return {
                'success': True,
                'message': 'Offer rejected'
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error rejecting offer: {e}")
            return {
                'success': False,
                'errors': [f'Failed to reject offer: {str(e)}']
            }
    
    @staticmethod
    def cancel_offer(db: Session, offer_id: int, league_id: int,
                     user_id: Optional[int] = None) -> Dict:
        """
        Cancel a transfer offer (by the offering team).
        
        Args:
            offer_id: Offer ID
            league_id: League ID
            user_id: User cancelling (must own the offering team)
            
        Returns:
            Dict with cancellation result
        """
        try:
            offer = db.query(TransferOffer).filter(
                TransferOffer.id == offer_id,
                TransferOffer.league_id == league_id
            ).first()
            
            if not offer:
                return {
                    'success': False,
                    'errors': ['Offer not found']
                }
            
            # Verify ownership
            from_team = db.query(LeagueTeam).filter(LeagueTeam.id == offer.from_team_id).first()
            if user_id and from_team.fantasy_team.user_id != user_id:
                return {
                    'success': False,
                    'errors': ['You do not own the offering team']
                }
            
            # Check offer status
            if offer.status != 'pending':
                return {
                    'success': False,
                    'errors': [f'Offer already {offer.status}']
                }
            
            # Cancel the offer
            offer.status = 'cancelled'
            db.commit()
            
            return {
                'success': True,
                'message': 'Offer cancelled'
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error cancelling offer: {e}")
            return {
                'success': False,
                'errors': [f'Failed to cancel offer: {str(e)}']
            }
