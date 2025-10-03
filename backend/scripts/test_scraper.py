"""
Example script demonstrating how to use the FBref scraper.

This script shows how to:
1. Scrape player statistics for a specific matchday
2. Save the data to the database
3. Update player cumulative stats
"""

import logging
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.services.laliga_scraper import FBrefScraper
from src.services.scraper_db_service import ScraperDatabaseService
from config import get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def scrape_and_save_matchday(matchday: int, season: str = "2025-2026"):
    """
    Scrape player statistics for a matchday and save to database.
    
    Args:
        matchday: Matchday number (1-38 for LaLiga)
        season: Season string in format "YYYY-YYYY"
    """
    logger.info(f"Starting to scrape matchday {matchday} for season {season}")
    
    # Initialize scraper
    scraper = FBrefScraper(season=season)
    
    # Scrape matchday data
    try:
        player_stats = scraper.scrape_matchday(matchday)
        
        if not player_stats:
            logger.warning(f"No player stats found for matchday {matchday}")
            return
        
        logger.info(f"Successfully scraped {len(player_stats)} player records")
        
        # Print sample of scraped data
        logger.info("Sample of scraped data:")
        for i, stat in enumerate(player_stats[:3]):  # Show first 3 records
            logger.info(f"  {i+1}. {stat['player_name']} ({stat['team']}): "
                       f"{stat['goals']}G, {stat['assists']}A, {stat['minutes_played']}min")
        
        # Save to database
        logger.info("Saving data to database...")
        db = next(get_db())
        
        try:
            successful, failed = ScraperDatabaseService.save_matchday_stats(db, player_stats)
            
            logger.info(f"Database save complete: {successful} successful, {failed} failed")
            
            # Update cumulative player stats
            if successful > 0:
                logger.info("Updating cumulative player statistics...")
                updated = ScraperDatabaseService.update_all_players_cumulative_stats(db, season)
                logger.info(f"Updated cumulative stats for {updated} players")
            
        finally:
            db.close()
        
        logger.info("Matchday scrape and save completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        raise


def test_scraper_only(matchday: int, season: str = "2025-2026"):
    """
    Test the scraper without saving to database.
    Useful for debugging and checking what data would be scraped.
    
    Args:
        matchday: Matchday number (1-38 for LaLiga)
        season: Season string in format "YYYY-YYYY"
    """
    logger.info(f"Testing scraper for matchday {matchday} (no database save)")
    
    scraper = FBrefScraper(season=season)
    
    try:
        # Get matches
        matches = scraper.get_matches_for_matchday(matchday)
        logger.info(f"Found {len(matches)} matches for matchday {matchday}:")
        
        for match in matches:
            logger.info(f"  - {match['home_team']} {match.get('home_score', '?')} - "
                       f"{match.get('away_score', '?')} {match['away_team']}")
        
        # Scrape player stats
        player_stats = scraper.scrape_matchday(matchday)
        
        logger.info(f"\nScraped {len(player_stats)} player records")
        
        # Display detailed stats for players who actually played (minutes > 0)
        if player_stats:
            players_with_minutes = [p for p in player_stats if p['minutes_played'] > 0]
            logger.info(f"Players who played: {len(players_with_minutes)} / {len(player_stats)}")
            
            # Show top scorers
            top_scorers = sorted(players_with_minutes, key=lambda x: x['goals'], reverse=True)[:5]
            if top_scorers and top_scorers[0]['goals'] > 0:
                logger.info("\n🥅 Top Scorers:")
                for i, stat in enumerate(top_scorers[:5]):
                    if stat['goals'] > 0:
                        logger.info(f"  {i+1}. {stat['player_name']} ({stat['team']}): {stat['goals']} goal(s), {stat['assists']} assist(s)")
            
            # Show players with assists
            top_assists = sorted(players_with_minutes, key=lambda x: x['assists'], reverse=True)[:5]
            if top_assists and top_assists[0]['assists'] > 0:
                logger.info("\n🎯 Top Assists:")
                for i, stat in enumerate(top_assists[:5]):
                    if stat['assists'] > 0:
                        logger.info(f"  {i+1}. {stat['player_name']} ({stat['team']}): {stat['assists']} assist(s)")
            
            # Show clean sheets
            clean_sheet_players = [p for p in players_with_minutes if p['clean_sheet']]
            if clean_sheet_players:
                logger.info(f"\n🧤 Clean Sheets: {len(clean_sheet_players)} players")
                for stat in clean_sheet_players[:5]:
                    logger.info(f"  - {stat['player_name']} ({stat['team']}): {stat['minutes_played']} min")
            
            # Show detailed stats for first few players who actually played
            logger.info("\nDetailed stats for first 5 players who played:")
            for i, stat in enumerate(players_with_minutes[:5]):
                logger.info(f"\n{i+1}. {stat['player_name']} ({stat['team']})")
                logger.info(f"   Minutes: {stat['minutes_played']}")
                logger.info(f"   Goals: {stat['goals']}, Assists: {stat['assists']}")
                logger.info(f"   Yellow Cards: {stat['yellow_cards']}, Red Cards: {stat['red_cards']}")
                logger.info(f"   Saves: {stat['saves']}")
                logger.info(f"   Clean Sheet: {stat['clean_sheet']}")
                logger.info(f"   Penalties Missed: {stat['penalties_missed']}")
                logger.info(f"   Penalties Saved: {stat['penalties_saved']}")
                logger.info(f"   Own Goals: {stat['own_goals']}")
        
        logger.info("\nTest completed successfully!")
        return player_stats
        
    except Exception as e:
        logger.error(f"Error during testing: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    """
    Example usage:
    
    # Test scraper without saving to database
    python scripts/test_scraper.py test 10
    
    # Scrape and save matchday 10 to database
    python scripts/test_scraper.py scrape 10
    
    # Scrape matchday 5 for a different season
    python scripts/test_scraper.py scrape 5 2024-2025
    """
    
    if len(sys.argv) < 3:
        print("Usage: python test_scraper.py [test|scrape] <matchday> [season]")
        print("Examples:")
        print("  python test_scraper.py test 10")
        print("  python test_scraper.py scrape 10")
        print("  python test_scraper.py scrape 5 2024-2025")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    matchday = int(sys.argv[2])
    season = sys.argv[3] if len(sys.argv) > 3 else "2025-2026"
    
    if mode == "test":
        test_scraper_only(matchday, season)
    elif mode == "scrape":
        scrape_and_save_matchday(matchday, season)
    else:
        print(f"Unknown mode: {mode}. Use 'test' or 'scrape'")
        sys.exit(1)
