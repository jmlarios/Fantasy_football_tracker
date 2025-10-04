"""
Squad Generator Service
Automatically generates valid 11-player squads when teams join leagues.
"""
from typing import List, Dict, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, not_, exists
from src.models import Player, LeagueTeamPlayer
import random
import logging

logger = logging.getLogger(__name__)


class SquadGenerator:
    """Service for generating random 11-player squads."""
    
    # Formation: 1 GK, 4 DEF, 4 MID, 2 FWD
    FORMATION = {
        'GK': 1,
        'DEF': 4,
        'MID': 4,
        'FWD': 2
    }
    
    TOTAL_PLAYERS = 11
    BUDGET = 100_000_000.0  # 100M euros
    
    @staticmethod
    def get_available_players_for_league(db: Session, league_id: int, position: str) -> List[Player]:
        """
        Get all players of a specific position that are not yet owned in this league.
        
        Args:
            db: Database session
            league_id: The league ID
            position: Player position (GK, DEF, MID, FWD)
            
        Returns:
            List of available players
        """
        # Find players not already in this league
        taken_player_ids = db.query(LeagueTeamPlayer.player_id).filter(
            LeagueTeamPlayer.league_id == league_id
        ).subquery()
        
        available_players = db.query(Player).filter(
            and_(
                Player.position == position,
                Player.is_active == True,
                not_(Player.id.in_(taken_player_ids))
            )
        ).all()
        
        return available_players
    
    @staticmethod
    def select_players_within_budget(
        players: List[Player], 
        count: int, 
        max_budget: float,
        already_selected: List[Player] = None
    ) -> List[Player]:
        """
        Randomly select players within budget constraints.
        
        Args:
            players: Available players to choose from
            count: Number of players to select
            max_budget: Maximum budget allowed
            already_selected: Players already selected (to track budget)
            
        Returns:
            List of selected players
        """
        if already_selected is None:
            already_selected = []
        
        # Calculate remaining budget
        budget_used = sum(p.price for p in already_selected)
        remaining_budget = max_budget - budget_used
        
        # Filter players we can afford
        affordable_players = [p for p in players if p.price <= remaining_budget]
        
        if len(affordable_players) < count:
            raise ValueError(f"Not enough affordable players available. Need {count}, found {len(affordable_players)}")
        
        # Try to select players randomly, ensuring we stay within budget
        max_attempts = 100
        for attempt in range(max_attempts):
            selected = random.sample(affordable_players, count)
            total_cost = sum(p.price for p in selected)
            
            if budget_used + total_cost <= max_budget:
                return selected
        
        # If random selection fails, use greedy approach
        # Sort by price and select cheapest players
        affordable_players.sort(key=lambda p: p.price)
        selected = affordable_players[:count]
        total_cost = sum(p.price for p in selected)
        
        if budget_used + total_cost > max_budget:
            raise ValueError(f"Cannot build squad within budget. Budget: {max_budget}, Required: {budget_used + total_cost}")
        
        return selected
    
    @staticmethod
    def generate_random_squad(db: Session, league_id: int) -> Dict[str, List[Player]]:
        """
        Generate a random 11-player squad for a league.
        
        Formation: 1 GK, 4 DEF, 4 MID, 2 FWD
        Budget: 100M
        
        Args:
            db: Database session
            league_id: The league ID
            
        Returns:
            Dictionary mapping position to list of players
            
        Raises:
            ValueError: If unable to generate a valid squad
        """
        squad = {}
        all_selected = []
        
        try:
            # Select players for each position
            for position, count in SquadGenerator.FORMATION.items():
                logger.info(f"Selecting {count} {position} player(s) for league {league_id}")
                
                # Get available players for this position
                available = SquadGenerator.get_available_players_for_league(db, league_id, position)
                
                if len(available) < count:
                    raise ValueError(
                        f"Not enough available {position} players in league {league_id}. "
                        f"Need {count}, found {len(available)}"
                    )
                
                # Select players within budget
                selected = SquadGenerator.select_players_within_budget(
                    available, 
                    count, 
                    SquadGenerator.BUDGET,
                    all_selected
                )
                
                squad[position] = selected
                all_selected.extend(selected)
            
            # Validate total cost
            total_cost = sum(p.price for p in all_selected)
            if total_cost > SquadGenerator.BUDGET:
                raise ValueError(
                    f"Squad exceeds budget. Total: {total_cost}, Budget: {SquadGenerator.BUDGET}"
                )
            
            logger.info(
                f"Successfully generated squad for league {league_id}. "
                f"Total cost: {total_cost}, Remaining: {SquadGenerator.BUDGET - total_cost}"
            )
            
            return squad
            
        except Exception as e:
            logger.error(f"Failed to generate squad for league {league_id}: {str(e)}")
            raise
    
    @staticmethod
    def validate_squad(squad: Dict[str, List[Player]]) -> bool:
        """
        Validate that a squad meets all requirements.
        
        Args:
            squad: Dictionary mapping position to players
            
        Returns:
            True if valid, False otherwise
        """
        # Check formation
        for position, count in SquadGenerator.FORMATION.items():
            if position not in squad or len(squad[position]) != count:
                logger.error(f"Invalid formation: {position} has {len(squad.get(position, []))} players, need {count}")
                return False
        
        # Check total players
        total_players = sum(len(players) for players in squad.values())
        if total_players != SquadGenerator.TOTAL_PLAYERS:
            logger.error(f"Invalid total players: {total_players}, need {SquadGenerator.TOTAL_PLAYERS}")
            return False
        
        # Check budget
        all_players = [p for players in squad.values() for p in players]
        total_cost = sum(p.price for p in all_players)
        if total_cost > SquadGenerator.BUDGET:
            logger.error(f"Squad exceeds budget: {total_cost} > {SquadGenerator.BUDGET}")
            return False
        
        # Check for duplicates
        player_ids = [p.id for p in all_players]
        if len(player_ids) != len(set(player_ids)):
            logger.error("Squad contains duplicate players")
            return False
        
        return True
