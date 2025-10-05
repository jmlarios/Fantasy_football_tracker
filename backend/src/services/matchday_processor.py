"""Matchday processing service for scraping stats and calculating fantasy points."""

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
    
    def __init__(self, db: Session, season: str = "2025-2026"):
        self.db = db
        self.season = season
        self.scraper = FBrefScraper(season=season)
    
    def process_matchday(self, matchday: int) -> Dict[str, Any]:
        """Scrape stats, save to DB, calculate points, update teams."""
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
            player_stats = self.scraper.scrape_matchday(matchday)
            results['players_scraped'] = len(player_stats)
            
            if not player_stats:
                return results
            
            successful, failed = ScraperDatabaseService.save_matchday_stats(
                self.db, player_stats
            )
            results['stats_saved'] = successful
            results['stats_failed'] = failed
            
            if successful == 0:
                logger.error("Failed to save any statistics to database")
                return results
            
            points_calculated = self._calculate_fantasy_points_for_matchday(matchday)
            results['fantasy_points_calculated'] = points_calculated
            
            teams_updated = self._update_fantasy_team_points(matchday)
            results['teams_updated'] = teams_updated
            
        except Exception as e:
            logger.error(f"Error processing matchday {matchday}: {e}", exc_info=True)
            results['errors'].append(str(e))
        
        return results
    
    def _calculate_fantasy_points_for_matchday(self, matchday: int) -> int:
        """Calculate fantasy points only for players in active teams."""
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
            return 0
        
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
                    continue
                
                player = stat.player
                
                if not player:
                    continue
                
                points_breakdown = self._calculate_player_fantasy_points(
                    stat, player.position
                )
                
                if self._save_fantasy_points(stat, match, points_breakdown):
                    points_calculated += 1
        
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
        
        fantasy_teams = self.db.query(FantasyTeam).all()
        
        for team in fantasy_teams:
            try:
                # Calculate points for this matchday
                matchday_points = self._calculate_team_matchday_points(team, matchday)
                
                team.total_points += matchday_points
                
                league_teams = self.db.query(LeagueTeam).filter(
                    LeagueTeam.fantasy_team_id == team.id
                ).all()
                
                for league_team in league_teams:
                    league_team.league_points += matchday_points
                
                self.db.flush()
                teams_updated += 1
                
            except Exception as e:
                logger.error(f"Error updating team {team.id}: {e}")
        
        self.db.commit()
        
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
                
                if team_player.is_captain:
                    player_total *= fantasy_scoring.scoring_rules['captain_multiplier']
                
                total_points += player_total
        
        return total_points
