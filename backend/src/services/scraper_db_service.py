"""
Database integration service for FBref scraper.

This module handles saving scraped player statistics to the database,
including match creation, player lookup/creation, and stats updates.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.models import Player, Match, MatchPlayerStats, Matchday
from config import get_db

logger = logging.getLogger(__name__)


class ScraperDatabaseService:
    """Service to save scraped data to the database."""
    
    @staticmethod
    def find_or_create_player(db: Session, player_name: str, team: str) -> Optional[Player]:
        """
        Find an existing player or create a new one.
        
        Args:
            db: Database session
            player_name: Name of the player
            team: Team name
            
        Returns:
            Player object or None if creation fails
        """
        # Try to find existing player by name and team
        player = db.query(Player).filter(
            and_(
                Player.name == player_name,
                Player.team == team,
                Player.is_active == True
            )
        ).first()
        
        if player:
            logger.debug(f"Found existing player: {player_name} ({team})")
            return player
        
        # Player not found, need to create
        # Note: Position and price need to be set separately or with default values
        logger.warning(f"Player not found in database: {player_name} ({team}). Creating with default values.")
        
        try:
            new_player = Player(
                name=player_name,
                team=team,
                position="MID",  # Default position, should be updated later
                price=5000000.0,  # Default price, should be updated later
                is_active=True
            )
            db.add(new_player)
            db.flush()  # Get the ID without committing
            
            logger.info(f"Created new player: {player_name} ({team}) with ID {new_player.id}")
            return new_player
            
        except Exception as e:
            logger.error(f"Failed to create player {player_name}: {e}")
            return None
    
    @staticmethod
    def find_or_create_match(db: Session, match_info: Dict[str, Any]) -> Optional[Match]:
        """
        Find an existing match or create a new one.
        
        Args:
            db: Database session
            match_info: Dictionary containing match information
            
        Returns:
            Match object or None if creation fails
        """
        # Try to find existing match
        match = db.query(Match).filter(
            and_(
                Match.home_team == match_info['home_team'],
                Match.away_team == match_info['away_team'],
                Match.matchday == match_info['matchday'],
                Match.season == match_info['season']
            )
        ).first()
        
        if match:
            logger.debug(f"Found existing match: {match_info['home_team']} vs {match_info['away_team']}")
            
            # Update match if scores have changed
            if match_info.get('home_score') is not None:
                match.home_score = match_info['home_score']
                match.away_score = match_info['away_score']
                match.is_finished = True
                db.flush()
            
            return match
        
        # Create new match
        try:
            # Try to parse the date
            match_date = None
            if match_info.get('match_date'):
                try:
                    # FBref uses format like "2024-08-15"
                    match_date = datetime.strptime(match_info['match_date'], "%Y-%m-%d")
                except ValueError:
                    logger.warning(f"Could not parse date: {match_info.get('match_date')}")
                    match_date = datetime.now()
            else:
                match_date = datetime.now()
            
            # Find or create associated matchday
            matchday_obj = db.query(Matchday).filter(
                and_(
                    Matchday.matchday_number == match_info['matchday'],
                    Matchday.season == match_info['season']
                )
            ).first()
            
            new_match = Match(
                home_team=match_info['home_team'],
                away_team=match_info['away_team'],
                match_date=match_date,
                matchday=match_info['matchday'],
                matchday_id=matchday_obj.id if matchday_obj else None,
                season=match_info['season'],
                competition="La Liga",
                home_score=match_info.get('home_score'),
                away_score=match_info.get('away_score'),
                is_finished=match_info.get('home_score') is not None
            )
            
            db.add(new_match)
            db.flush()
            
            logger.info(f"Created new match: {match_info['home_team']} vs {match_info['away_team']} (ID: {new_match.id})")
            return new_match
            
        except Exception as e:
            logger.error(f"Failed to create match: {e}")
            return None
    
    @staticmethod
    def save_player_stats(db: Session, player_stat: Dict[str, Any]) -> bool:
        """
        Save or update player statistics for a match.
        
        Args:
            db: Database session
            player_stat: Dictionary containing player statistics
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get or create player
            player = ScraperDatabaseService.find_or_create_player(
                db,
                player_stat['player_name'],
                player_stat['team']
            )
            
            if not player:
                logger.error(f"Could not find/create player: {player_stat['player_name']}")
                return False
            
            # Get or create match
            match = ScraperDatabaseService.find_or_create_match(
                db,
                player_stat['match_info']
            )
            
            if not match:
                logger.error(f"Could not find/create match")
                return False
            
            # Check if stats already exist
            existing_stats = db.query(MatchPlayerStats).filter(
                and_(
                    MatchPlayerStats.match_id == match.id,
                    MatchPlayerStats.player_id == player.id
                )
            ).first()
            
            if existing_stats:
                # Update existing stats
                logger.debug(f"Updating stats for {player.name} in match {match.id}")
                
                existing_stats.minutes_played = player_stat['minutes_played']
                existing_stats.goals = player_stat['goals']
                existing_stats.assists = player_stat['assists']
                existing_stats.yellow_cards = player_stat['yellow_cards']
                existing_stats.red_cards = player_stat['red_cards']
                existing_stats.saves = player_stat['saves']
                existing_stats.clean_sheet = player_stat['clean_sheet']
                existing_stats.own_goals = player_stat['own_goals']
                existing_stats.penalties_missed = player_stat['penalties_missed']
                existing_stats.penalties_saved = player_stat['penalties_saved']
                
            else:
                # Create new stats entry
                logger.debug(f"Creating new stats for {player.name} in match {match.id}")
                
                new_stats = MatchPlayerStats(
                    match_id=match.id,
                    player_id=player.id,
                    minutes_played=player_stat['minutes_played'],
                    goals=player_stat['goals'],
                    assists=player_stat['assists'],
                    yellow_cards=player_stat['yellow_cards'],
                    red_cards=player_stat['red_cards'],
                    saves=player_stat['saves'],
                    clean_sheet=player_stat['clean_sheet'],
                    own_goals=player_stat['own_goals'],
                    penalties_missed=player_stat['penalties_missed'],
                    penalties_saved=player_stat['penalties_saved']
                )
                
                db.add(new_stats)
            
            db.flush()
            logger.debug(f"Saved stats for {player.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving player stats for {player_stat.get('player_name', 'Unknown')}: {e}")
            return False
    
    @staticmethod
    def save_matchday_stats(db: Session, matchday_stats: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Save all player statistics for a matchday.
        
        Args:
            db: Database session
            matchday_stats: List of player statistics dictionaries
            
        Returns:
            Tuple of (successful_saves, failed_saves)
        """
        successful = 0
        failed = 0
        
        logger.info(f"Saving stats for {len(matchday_stats)} player records")
        
        for player_stat in matchday_stats:
            try:
                if ScraperDatabaseService.save_player_stats(db, player_stat):
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Unexpected error saving stats: {e}")
                failed += 1
        
        # Commit all changes
        try:
            db.commit()
            logger.info(f"Successfully saved {successful} player stats, {failed} failed")
        except Exception as e:
            logger.error(f"Failed to commit transaction: {e}")
            db.rollback()
            return (0, len(matchday_stats))
        
        return (successful, failed)
    
    @staticmethod
    def update_player_cumulative_stats(db: Session, player_id: int) -> bool:
        """
        Update a player's cumulative season statistics based on all their match stats.
        
        Args:
            db: Database session
            player_id: ID of the player to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            if not player:
                logger.error(f"Player with ID {player_id} not found")
                return False
            
            # Get all match stats for this player
            all_stats = db.query(MatchPlayerStats).filter(
                MatchPlayerStats.player_id == player_id
            ).all()
            
            # Calculate cumulative stats
            total_goals = sum(stat.goals for stat in all_stats)
            total_assists = sum(stat.assists for stat in all_stats)
            total_yellow_cards = sum(stat.yellow_cards for stat in all_stats)
            total_red_cards = sum(stat.red_cards for stat in all_stats)
            total_minutes = sum(stat.minutes_played for stat in all_stats)
            total_clean_sheets = sum(1 for stat in all_stats if stat.clean_sheet)
            
            # Update player record
            player.goals = total_goals
            player.assists = total_assists
            player.yellow_cards = total_yellow_cards
            player.red_cards = total_red_cards
            player.minutes_played = total_minutes
            player.clean_sheets = total_clean_sheets
            
            db.commit()
            
            logger.info(f"Updated cumulative stats for {player.name}: "
                       f"{total_goals}G, {total_assists}A, {total_minutes}min")
            return True
            
        except Exception as e:
            logger.error(f"Error updating cumulative stats for player {player_id}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def update_all_players_cumulative_stats(db: Session, season: str) -> int:
        """
        Update cumulative stats for all players in a season.
        
        Args:
            db: Database session
            season: Season string (e.g., "2024-2025")
            
        Returns:
            Number of players updated
        """
        # Get all active players
        players = db.query(Player).filter(Player.is_active == True).all()
        
        updated = 0
        for player in players:
            if ScraperDatabaseService.update_player_cumulative_stats(db, player.id):
                updated += 1
        
        logger.info(f"Updated cumulative stats for {updated} players")
        return updated
