"""
Process a completed matchday: scrape stats, calculate fantasy points, update teams.

Usage:
    python scripts/process_matchday.py <matchday> [season]

Examples:
    python scripts/process_matchday.py 2
    python scripts/process_matchday.py 5 2024-2025
"""

import logging
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.services.matchday_processor import MatchdayProcessor
from config import get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_matchday(matchday: int, season: str = "2025-2026"):
    """
    Process a complete matchday.
    
    This will:
    1. Scrape player statistics from FBref
    2. Save stats to MatchPlayerStats table
    3. Calculate fantasy points for players in fantasy teams
    4. Update fantasy team total points
    
    Args:
        matchday: Matchday number (1-38)
        season: Season string (e.g., "2025-2026")
    """
    logger.info("="*60)
    logger.info(f"Processing Matchday {matchday} - Season {season}")
    logger.info("="*60)
    
    db = next(get_db())
    
    try:
        # Create processor
        processor = MatchdayProcessor(db, season=season)
        
        # Process the matchday
        results = processor.process_matchday(matchday)
        
        # Display results
        logger.info("\n" + "="*60)
        logger.info("PROCESSING COMPLETE")
        logger.info("="*60)
        logger.info(f"Matchday: {results['matchday']}")
        logger.info(f"Season: {results['season']}")
        logger.info(f"")
        logger.info(f"📊 Statistics:")
        logger.info(f"  - Players scraped: {results['players_scraped']}")
        logger.info(f"  - Stats saved: {results['stats_saved']}")
        logger.info(f"  - Stats failed: {results['stats_failed']}")
        logger.info(f"")
        logger.info(f"⚽ Fantasy Points:")
        logger.info(f"  - Points calculated: {results['fantasy_points_calculated']}")
        logger.info(f"")
        logger.info(f"🏆 Fantasy Teams:")
        logger.info(f"  - Teams updated: {results['teams_updated']}")
        
        if results['errors']:
            logger.info(f"")
            logger.warning(f"⚠️ Errors encountered:")
            for error in results['errors']:
                logger.warning(f"  - {error}")
        
        logger.info("="*60)
        
        # Return success code
        return 0 if not results['errors'] else 1
        
    except Exception as e:
        logger.error(f"Fatal error processing matchday: {e}", exc_info=True)
        return 1
        
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_matchday.py <matchday> [season]")
        print("Examples:")
        print("  python process_matchday.py 2")
        print("  python process_matchday.py 5 2024-2025")
        sys.exit(1)
    
    matchday = int(sys.argv[1])
    season = sys.argv[2] if len(sys.argv) > 2 else "2025-2026"
    
    exit_code = process_matchday(matchday, season)
    sys.exit(exit_code)
