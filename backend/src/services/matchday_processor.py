"""
Matchday processing service.

This service handles the complete workflow for processing a finished matchday:
1. Scrape player statistics from FBref
2. Save stats to MatchPlayerStats
3. Calculate fantasy points ONLY for players in fantasy teams
4. Update fantasy team total points
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.models import (
    Player, Match, MatchPlayerStats, FantasyPoints, 
    FantasyTeam, FantasyTeamPlayer, Matchday, LeagueTeam
)
from src.services.laliga_scraper import FBrefScraper
from src.services.scraper_db_service import ScraperDatabaseService
from src.services.scoring import fantasy_scoring
from config import get_db

logger = logging.getLogger(__name__)


class MatchdayProcessor:
    """
    Process a complete matchday: scrape stats, calculate points, update teams.
    """
    
    def __init__(self, db: Session, season: str = "2025-2026"):
        """
        Initialize the matchday processor.
        
        Args:
            db: Database session
            season: Season string (e.g., "2025-2026")
        """
        self.db = db
        self.season = season
        self.scraper = FBrefScraper(season=season)
        logger.info(f"MatchdayProcessor initialized for season {season}")
    
    def process_matchday(self, matchday: int) -> Dict[str, Any]:
        """
        Complete workflow to process a finished matchday.
        
        Steps:
        1. Scrape player stats from FBref
        2. Save stats to database
        3. Calculate fantasy points for players in fantasy teams
        4. Update fantasy team points
        
        Args:
            matchday: Matchday number (1-38)
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Starting matchday {matchday} processing")
        
        results = {
            'matchday': matchday,
            'season': self.season,
            'players_scraped': 0,
            'stats_saved': 0,
            'stats_failed': 0,
            'fantasy_points_calculated': 0,
            'teams_updated': 0,
            'errors': []
        }
        
        try:
            # Step 1: Scrape player stats
            logger.info("Step 1: Scraping player statistics...")
            player_stats = self.scraper.scrape_matchday(matchday)
            results['players_scraped'] = len(player_stats)
            
            if not player_stats:
                logger.warning(f"No player stats found for matchday {matchday}")
                return results
            
            # Step 2: Save stats to database
            logger.info("Step 2: Saving statistics to database...")
            successful, failed = ScraperDatabaseService.save_matchday_stats(
                self.db, player_stats
            )
            results['stats_saved'] = successful
            results['stats_failed'] = failed
            
            if successful == 0:
                logger.error("Failed to save any statistics to database")
                return results
            
            # Step 3: Calculate fantasy points for players in fantasy teams
            logger.info("Step 3: Calculating fantasy points for fantasy team players...")
            points_calculated = self._calculate_fantasy_points_for_matchday(matchday)
            results['fantasy_points_calculated'] = points_calculated
            
            # Step 4: Update fantasy team totals
            logger.info("Step 4: Updating fantasy team total points...")
            teams_updated = self._update_fantasy_team_points(matchday)
            results['teams_updated'] = teams_updated
            
            logger.info(f"Matchday {matchday} processing completed successfully!")
            logger.info(f"Results: {successful} stats saved, {points_calculated} fantasy points calculated, {teams_updated} teams updated")
            
        except Exception as e:
            logger.error(f"Error processing matchday {matchday}: {e}", exc_info=True)
            results['errors'].append(str(e))
        
        return results
    
    def _calculate_fantasy_points_for_matchday(self, matchday: int) -> int:
        """
        Calculate fantasy points ONLY for players who are in fantasy teams.
        
        This is efficient because we:
        1. Only calculate points for active fantasy team players
        2. Skip players not in any fantasy team
        
        Args:
            matchday: Matchday number
            
        Returns:
            Number of fantasy point records created/updated
        """
        points_calculated = 0
        
        # Get all matches for this matchday
        matches = self.db.query(Match).filter(
            and_(
                Match.matchday == matchday,
                Match.season == self.season,
                Match.is_finished == True
            )
        ).all()
        
        if not matches:
            logger.warning(f"No finished matches found for matchday {matchday}")
            return 0
        
        logger.info(f"Processing {len(matches)} matches for fantasy points")
        
        for match in matches:
            # Get all players who played in this match AND are in fantasy teams
            match_stats = self.db.query(MatchPlayerStats).filter(
                MatchPlayerStats.match_id == match.id
            ).all()
            
            for stat in match_stats:
                # Check if this player is in ANY fantasy team
                player_in_teams = self.db.query(FantasyTeamPlayer).filter(
                    FantasyTeamPlayer.player_id == stat.player_id
                ).first()
                
                if not player_in_teams:
                    # Player not in any fantasy team, skip
                    continue
                
                # Player is in at least one fantasy team, calculate points
                player = stat.player
                
                if not player:
                    logger.warning(f"Player not found for player_id {stat.player_id}")
                    continue
                
                # Calculate fantasy points
                points_breakdown = self._calculate_player_fantasy_points(
                    stat, player.position
                )
                
                # Save or update fantasy points
                if self._save_fantasy_points(stat, match, points_breakdown):
                    points_calculated += 1
        
        logger.info(f"Calculated fantasy points for {points_calculated} player-match records")
        return points_calculated
    
    def _calculate_player_fantasy_points(
        self, 
        match_stats: MatchPlayerStats, 
        position: str
    ) -> Dict[str, float]:
        """
        Calculate fantasy points breakdown for a player's match performance.
        
        Args:
            match_stats: Player's match statistics
            position: Player position (GK, DEF, MID, FWD)
            
        Returns:
            Dictionary with points breakdown
        """
        # Prepare stats dict for scoring calculator
        stats_dict = {
            'minutes_played': match_stats.minutes_played,
            'goals': match_stats.goals,
            'assists': match_stats.assists,
            'yellow_cards': match_stats.yellow_cards,
            'red_cards': match_stats.red_cards,
            'saves': match_stats.saves,
            'clean_sheet': match_stats.clean_sheet,
            'own_goals': match_stats.own_goals,
            'penalties_missed': match_stats.penalties_missed,
            'penalties_saved': match_stats.penalties_saved
        }
        
        # Calculate total points using instance method
        breakdown = fantasy_scoring.calculate_player_points(
            stats_dict, 
            position
        )
        
        # The breakdown already includes total_points from calculate_player_points
        # Just extract it
        total_points = breakdown.get('total', 0.0)
        
        breakdown['total_points'] = total_points
        
        return breakdown
    
    def _save_fantasy_points(
        self, 
        match_stats: MatchPlayerStats, 
        match: Match,
        points_breakdown: Dict[str, float]
    ) -> bool:
        """
        Save or update fantasy points for a player-match combination.
        
        Args:
            match_stats: Player's match statistics
            match: Match object
            points_breakdown: Points breakdown dictionary
            
        Returns:
            True if successful
        """
        try:
            # Check if fantasy points already exist
            existing_points = self.db.query(FantasyPoints).filter(
                and_(
                    FantasyPoints.player_id == match_stats.player_id,
                    FantasyPoints.match_id == match.id
                )
            ).first()
            
            if existing_points:
                # Update existing record
                existing_points.points_from_goals = points_breakdown.get('points_from_goals', 0.0)
                existing_points.points_from_assists = points_breakdown.get('points_from_assists', 0.0)
                existing_points.points_from_clean_sheet = points_breakdown.get('points_from_clean_sheet', 0.0)
                existing_points.points_from_cards = points_breakdown.get('points_from_cards', 0.0)
                existing_points.points_from_saves = points_breakdown.get('points_from_saves', 0.0)
                existing_points.points_from_minutes = points_breakdown.get('points_from_minutes', 0.0)
                existing_points.penalty_points = points_breakdown.get('penalty_points', 0.0)
                existing_points.total_points = points_breakdown.get('total_points', 0.0)
                
                logger.debug(f"Updated fantasy points for player {match_stats.player_id} in match {match.id}")
            else:
                # Create new record
                new_points = FantasyPoints(
                    player_id=match_stats.player_id,
                    match_id=match.id,
                    points_from_goals=points_breakdown.get('points_from_goals', 0.0),
                    points_from_assists=points_breakdown.get('points_from_assists', 0.0),
                    points_from_clean_sheet=points_breakdown.get('points_from_clean_sheet', 0.0),
                    points_from_cards=points_breakdown.get('points_from_cards', 0.0),
                    points_from_saves=points_breakdown.get('points_from_saves', 0.0),
                    points_from_minutes=points_breakdown.get('points_from_minutes', 0.0),
                    penalty_points=points_breakdown.get('penalty_points', 0.0),
                    bonus_points=0.0,
                    total_points=points_breakdown.get('total_points', 0.0)
                )
                
                self.db.add(new_points)
                logger.debug(f"Created fantasy points for player {match_stats.player_id} in match {match.id}")
            
            self.db.flush()
            return True
            
        except Exception as e:
            logger.error(f"Error saving fantasy points: {e}")
            return False
    
    def _update_fantasy_team_points(self, matchday: int) -> int:
        """
        Update total points for all fantasy teams based on their players' performance.
        
        For each team:
        1. Get all players in the team
        2. Sum their fantasy points for this matchday
        3. Apply captain multiplier if applicable
        4. Update team's total_points (fantasy_teams table)
        5. Update league_points for all league_teams linked to this fantasy team
        
        Args:
            matchday: Matchday number
            
        Returns:
            Number of teams updated
        """
        teams_updated = 0
        
        # Get all active fantasy teams
        fantasy_teams = self.db.query(FantasyTeam).all()
        
        logger.info(f"Updating points for {len(fantasy_teams)} fantasy teams")
        
        for team in fantasy_teams:
            try:
                # Calculate points for this matchday
                matchday_points = self._calculate_team_matchday_points(team, matchday)
                
                # Update team's total points in fantasy_teams table
                team.total_points += matchday_points
                
                # Also update league_points for all league_teams linked to this fantasy team
                league_teams = self.db.query(LeagueTeam).filter(
                    LeagueTeam.fantasy_team_id == team.id
                ).all()
                
                logger.info(f"Found {len(league_teams)} league_teams for fantasy_team_id={team.id}")
                
                for league_team in league_teams:
                    old_points = league_team.league_points
                    league_team.league_points += matchday_points
                    logger.info(f"League team '{league_team.team_name}' (ID: {league_team.id}): {old_points} + {matchday_points} = {league_team.league_points} points")
                
                self.db.flush()
                teams_updated += 1
                
                logger.debug(f"Fantasy team '{team.name}' (ID: {team.id}): +{matchday_points} points (Total: {team.total_points})")
                
            except Exception as e:
                logger.error(f"Error updating team {team.id}: {e}")
        
        self.db.commit()
        logger.info(f"Updated {teams_updated} fantasy teams and their league entries")
        
        return teams_updated
    
    def _calculate_team_matchday_points(self, team: FantasyTeam, matchday: int) -> float:
        """
        Calculate total points for a fantasy team for a specific matchday.
        
        Args:
            team: FantasyTeam object
            matchday: Matchday number
            
        Returns:
            Total points for this matchday
        """
        total_points = 0.0
        
        # Get all players in this team
        team_players = self.db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == team.id
        ).all()
        
        # Get all matches for this matchday
        matches = self.db.query(Match).filter(
            and_(
                Match.matchday == matchday,
                Match.season == self.season
            )
        ).all()
        
        match_ids = [match.id for match in matches]
        
        for team_player in team_players:
            # Get fantasy points for this player in this matchday
            player_points = self.db.query(FantasyPoints).filter(
                and_(
                    FantasyPoints.player_id == team_player.player_id,
                    FantasyPoints.match_id.in_(match_ids)
                )
            ).all()
            
            # Sum up points (should be just one match per matchday per player)
            for points in player_points:
                player_total = points.total_points
                
                # Apply captain multiplier if this player is captain
                if team_player.is_captain:
                    player_total *= fantasy_scoring.scoring_rules['captain_multiplier']
                    logger.debug(f"Captain {team_player.player.name}: {points.total_points} × 2 = {player_total}")
                
                total_points += player_total
        
        return total_points
