"""Seed LaLiga players and matches using the FBref scraper pipeline."""

import sys
from pathlib import Path
from typing import Dict
import logging

# Ensure backend root is on the path so imports work when executed as a script
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from config import SessionLocal
from src.models import Player, Match
from src.services.laliga_scraper import FBrefScraper
from src.services.scraper_db_service import ScraperDatabaseService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def import_laliga_data(start_matchday: int = 1, end_matchday: int = 1, season: str = "2025-2026") -> Dict[str, int]:
    """Scrape FBref data and persist players/matches for the given matchday range."""
    logger.info("Starting LaLiga data import...")
    logger.info("Season: %s | Matchdays: %s-%s", season, start_matchday, end_matchday)

    scraper = FBrefScraper(season=season)
    db = SessionLocal()

    results = {
        "matchdays_processed": 0,
        "players_scraped": 0,
        "stats_saved": 0,
        "stats_failed": 0,
    }

    try:
        for matchday in range(start_matchday, end_matchday + 1):
            logger.info("Processing matchday %s", matchday)

            player_stats = scraper.scrape_matchday(matchday)
            if not player_stats:
                logger.warning("No player stats returned for matchday %s", matchday)
                continue

            results["players_scraped"] += len(player_stats)

            saved, failed = ScraperDatabaseService.save_matchday_stats(db, player_stats)
            results["stats_saved"] += saved
            results["stats_failed"] += failed
            results["matchdays_processed"] += 1

            logger.info(
                "Matchday %s complete | records scraped: %s | saved: %s | failed: %s",
                matchday,
                len(player_stats),
                saved,
                failed,
            )

        # Summaries for visibility
        player_count = db.query(Player).count()
        match_count = db.query(Match).count()
        logger.info("Database now has %s players and %s matches", player_count, match_count)

        return results

    except Exception as exc:  # noqa: BLE001
        logger.exception("Import failed: %s", exc)
        db.rollback()
        raise
    finally:
        db.close()


def check_database_status():
    """Log basic database stats for quick health checks."""
    db = SessionLocal()
    try:
        player_count = db.query(Player).count()
        match_count = db.query(Match).count()

        logger.info("Database status:")
        logger.info("  Players: %s", player_count)
        logger.info("  Matches: %s", match_count)

        sample_players = db.query(Player).limit(5).all()
        if sample_players:
            logger.info("Sample players:")
            for player in sample_players:
                logger.info("  - %s (%s, %s)", player.name, player.team, player.position)
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        check_database_status()
        sys.exit(0)

    start_md = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end_md = int(sys.argv[2]) if len(sys.argv) > 2 else start_md
    season_arg = sys.argv[3] if len(sys.argv) > 3 else "2025-2026"

    summary = import_laliga_data(start_md, end_md, season_arg)
    logger.info("Import summary: %s", summary)


