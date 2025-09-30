import sys
from pathlib import Path
from typing import Dict
import logging

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from config import SessionLocal
from src.models import Player, Match
from src.services.laliga_api import laliga_api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_laliga_data():
    """Import LaLiga data directly."""
    logger.info("Starting LaLiga data import...")
    
    db = SessionLocal()
    results = {'teams': 0, 'players': 0, 'fixtures': 0, 'errors': []}
    
    try:
        # Get teams
        teams = laliga_api.get_laliga_teams()
        logger.info(f"Found {len(teams)} teams")
        
        for team in teams:  # Import all teams
            team_name = team['name']
            logger.info(f"Processing {team_name}...")
            
            # Get players
            players = laliga_api.get_team_players(team_name)
            logger.info(f"Found {len(players)} players for {team_name}")
            
            # Import players
            for player_data in players:
                # Check if player already exists
                existing_player = db.query(Player).filter(
                    Player.name == player_data['name'],
                    Player.team == team_name
                ).first()
                
                if not existing_player:
                    new_player = Player(
                        name=player_data['name'],
                        team=team_name,
                        position=player_data['position'],
                        is_active=True
                    )
                    db.add(new_player)
                    results['players'] += 1
            
            results['teams'] += 1
        
        # Get fixtures
        logger.info("Importing fixtures...")
        fixtures = laliga_api.get_season_fixtures()
        logger.info(f"Found {len(fixtures)} fixtures")
        
        for fixture_data in fixtures:
            # Check if fixture already exists
            existing_match = db.query(Match).filter(
                Match.home_team == fixture_data['home_team'],
                Match.away_team == fixture_data['away_team'],
                Match.season == '2024-2025'
            ).first()
            
            if not existing_match:
                from datetime import datetime
                
                match_date = datetime.now()
                if fixture_data.get('date'):
                    try:
                        match_date = datetime.strptime(fixture_data['date'], '%Y-%m-%d')
                    except:
                        pass
                
                new_match = Match(
                    home_team=fixture_data['home_team'],
                    away_team=fixture_data['away_team'],
                    match_date=match_date,
                    matchday=fixture_data.get('round', 1),
                    season='2024-2025',
                    competition='LaLiga',
                    home_score=fixture_data.get('home_score'),
                    away_score=fixture_data.get('away_score'),
                    is_finished=(fixture_data.get('status') == 'finished')
                )
                db.add(new_match)
                results['fixtures'] += 1
        
        db.commit()
        logger.info(f"Import successful: {results}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Import failed: {e}")
        
    finally:
        db.close()

def check_database_status():
    """Check current database status."""
    db = SessionLocal()
    try:
        player_count = db.query(Player).count()
        match_count = db.query(Match).count()
        
        logger.info(f"Database status:")
        logger.info(f"  Players: {player_count}")
        logger.info(f"  Matches: {match_count}")
        
        # Show some sample data
        sample_players = db.query(Player).limit(5).all()
        logger.info("Sample players:")
        for player in sample_players:
            logger.info(f"  - {player.name} ({player.team}, {player.position})")
        
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        check_database_status()
    else:
        import_laliga_data()
