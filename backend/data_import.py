import sys
import os
from pathlib import Path
from typing import List, Dict
from sqlalchemy.orm import Session
import logging

# Add the backend root directory to path to import config
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from config import SessionLocal
from src.models import Player, Match
from src.services.laliga_api import laliga_api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LaLigaDataImporter:
    """Service to import LaLiga data from TheSportsDB API into our database."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def import_all_data(self) -> Dict[str, int]:
        """Import all LaLiga data (teams, players, fixtures)."""
        results = {
            'teams_imported': 0,
            'players_imported': 0,
            'fixtures_imported': 0,
            'errors': []
        }
        
        try:
            # Import teams and players
            teams_result = self.import_teams_and_players()
            results['teams_imported'] = teams_result['teams']
            results['players_imported'] = teams_result['players']
            results['errors'].extend(teams_result['errors'])
            
            # Import fixtures
            fixtures_result = self.import_fixtures()
            results['fixtures_imported'] = fixtures_result['fixtures']
            results['errors'].extend(fixtures_result['errors'])
            
        except Exception as e:
            logger.error(f"Error during data import: {e}")
            results['errors'].append(str(e))
        
        return results
    
    def import_teams_and_players(self) -> Dict[str, int]:
        """Import LaLiga teams and their players."""
        results = {'teams': 0, 'players': 0, 'errors': []}
        
        try:
            # Get all LaLiga teams
            logger.info("Fetching LaLiga teams...")
            teams = laliga_api.get_laliga_teams()
            
            if not teams:
                logger.warning("No teams found")
                return results
            
            for team in teams:
                try:
                    team_name = team['name']
                    logger.info(f"Processing team: {team_name}")
                    
                    # Get players for this team
                    players = laliga_api.get_team_players(team_name)
                    
                    if not players:
                        logger.warning(f"No players found for {team_name}")
                        continue
                    
                    # Import players to database
                    for player_data in players:
                        try:
                            self._import_player(player_data, team_name)
                            results['players'] += 1
                        except Exception as e:
                            error_msg = f"Error importing player {player_data.get('name', 'Unknown')}: {e}"
                            logger.error(error_msg)
                            results['errors'].append(error_msg)
                    
                    results['teams'] += 1
                    logger.info(f"Imported {len(players)} players for {team_name}")
                    
                except Exception as e:
                    error_msg = f"Error processing team {team.get('name', 'Unknown')}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            self.db.commit()
            logger.info(f"Successfully imported {results['teams']} teams and {results['players']} players")
            
        except Exception as e:
            self.db.rollback()
            error_msg = f"Error importing teams and players: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
    def import_fixtures(self) -> Dict[str, int]:
        """Import LaLiga fixtures/matches."""
        results = {'fixtures': 0, 'errors': []}
        
        try:
            logger.info("Fetching LaLiga fixtures...")
            fixtures = laliga_api.get_season_fixtures()
            
            if not fixtures:
                logger.warning("No fixtures found")
                return results
            
            for fixture_data in fixtures:
                try:
                    self._import_fixture(fixture_data)
                    results['fixtures'] += 1
                except Exception as e:
                    error_msg = f"Error importing fixture {fixture_data.get('id', 'Unknown')}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            self.db.commit()
            logger.info(f"Successfully imported {results['fixtures']} fixtures")
            
        except Exception as e:
            self.db.rollback()
            error_msg = f"Error importing fixtures: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
    def _import_player(self, player_data: Dict, team_name: str):
        """Import a single player to the database."""
        # Check if player already exists
        existing_player = self.db.query(Player).filter(
            Player.name == player_data['name'],
            Player.team == team_name
        ).first()
        
        if existing_player:
            # Update existing player
            existing_player.position = player_data['position']
            existing_player.is_active = True
            logger.debug(f"Updated existing player: {player_data['name']}")
        else:
            # Create new player
            new_player = Player(
                name=player_data['name'],
                team=team_name,
                position=player_data['position'],
                is_active=True
            )
            self.db.add(new_player)
            logger.debug(f"Added new player: {player_data['name']}")
    
    def _import_fixture(self, fixture_data: Dict):
        """Import a single fixture to the database."""
        from datetime import datetime
        
        # Check if fixture already exists
        existing_match = self.db.query(Match).filter(
            Match.home_team == fixture_data['home_team'],
            Match.away_team == fixture_data['away_team'],
            Match.season == fixture_data.get('season', '2024-2025')
        ).first()
        
        if existing_match:
            # Update existing match
            if fixture_data.get('home_score') is not None:
                existing_match.home_score = fixture_data['home_score']
            if fixture_data.get('away_score') is not None:
                existing_match.away_score = fixture_data['away_score']
            existing_match.is_finished = (fixture_data.get('status') == 'finished')
            logger.debug(f"Updated existing match: {fixture_data['home_team']} vs {fixture_data['away_team']}")
        else:
            # Parse date
            match_date = datetime.now()
            if fixture_data.get('date'):
                try:
                    match_date = datetime.strptime(fixture_data['date'], '%Y-%m-%d')
                except:
                    logger.warning(f"Could not parse date: {fixture_data.get('date')}")
            
            # Create new match
            new_match = Match(
                home_team=fixture_data['home_team'],
                away_team=fixture_data['away_team'],
                match_date=match_date,
                matchday=fixture_data.get('round', 1),
                season=fixture_data.get('season', '2024-2025'),
                competition='LaLiga',
                home_score=fixture_data.get('home_score'),
                away_score=fixture_data.get('away_score'),
                is_finished=(fixture_data.get('status') == 'finished')
            )
            self.db.add(new_match)
            logger.debug(f"Added new match: {fixture_data['home_team']} vs {fixture_data['away_team']}")
    
    def close(self):
        """Close database session."""
        self.db.close()


def import_laliga_data():
    """CLI function to import LaLiga data."""
    logger.info("Starting LaLiga data import...")
    
    importer = LaLigaDataImporter()
    
    try:
        results = importer.import_all_data()
        
        logger.info("Import completed!")
        logger.info(f"Teams imported: {results['teams_imported']}")
        logger.info(f"Players imported: {results['players_imported']}")
        logger.info(f"Fixtures imported: {results['fixtures_imported']}")
        
        if results['errors']:
            logger.warning(f"Errors encountered: {len(results['errors'])}")
            for error in results['errors'][:5]:  # Show first 5 errors
                logger.warning(f"  - {error}")
        
        return results
        
    finally:
        importer.close()


if __name__ == "__main__":
    import_laliga_data()
