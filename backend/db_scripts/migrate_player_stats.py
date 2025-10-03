import sys
from pathlib import Path

# Add the parent directory (backend) to the Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Add src directory to path
src_path = backend_path / "src"
sys.path.insert(0, str(src_path))

from config import engine, SessionLocal
from src.models import Base
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_player_statistics():
    """Add new statistics fields to the players table."""
    
    db = SessionLocal()
    try:
        logger.info("Starting player statistics migration...")
        
        # List of new columns to add with PostgreSQL-compatible syntax
        new_columns = [
            ("matches_played", "INTEGER DEFAULT 0"),
            ("minutes_played", "INTEGER DEFAULT 0"),
            ("yellow_cards", "INTEGER DEFAULT 0"), 
            ("red_cards", "INTEGER DEFAULT 0"),
            ("clean_sheets", "INTEGER DEFAULT 0"),
            ("goals_conceded", "INTEGER DEFAULT 0"),
            ("saves", "INTEGER DEFAULT 0"),
            ("penalties_saved", "INTEGER DEFAULT 0"),
            ("penalties_missed", "INTEGER DEFAULT 0"),
            ("penalties_won", "INTEGER DEFAULT 0"),
            ("penalties_committed", "INTEGER DEFAULT 0"),
            ("own_goals", "INTEGER DEFAULT 0"),
            ("balls_recovered", "INTEGER DEFAULT 0"),
            ("clearances", "INTEGER DEFAULT 0"),
            ("shots_on_target", "INTEGER DEFAULT 0"),
            ("successful_dribbles", "INTEGER DEFAULT 0"),
            ("entries_into_box", "INTEGER DEFAULT 0"),
            ("total_fantasy_points", "REAL DEFAULT 0.0"),
            ("last_match_points", "REAL DEFAULT 0.0"),
            ("form_points", "REAL DEFAULT 0.0"),
            ("points_per_match", "REAL DEFAULT 0.0"),
            ("consistency_rating", "REAL DEFAULT 0.0"),
            ("stats_last_updated", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("season", "VARCHAR(20) DEFAULT '2025-26'")  # 2025-26 season
        ]
        
        # Add each column individually with proper error handling
        for column_name, column_def in new_columns:
            try:
                # Check if column exists first
                check_query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'players' AND column_name = :column_name
                """)
                result = db.execute(check_query, {"column_name": column_name}).fetchone()
                
                if result:
                    logger.info(f"✓ Column {column_name} already exists, skipping")
                    continue
                
                # Add the column
                add_column_query = text(f"ALTER TABLE players ADD COLUMN {column_name} {column_def}")
                db.execute(add_column_query)
                db.commit()
                logger.info(f"✓ Added column: {column_name}")
                
            except Exception as e:
                db.rollback()
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    logger.info(f"✓ Column {column_name} already exists, skipping")
                else:
                    logger.warning(f"⚠️  Could not add column {column_name}: {e}")
        
        logger.info("\n" + "=" * 60)
        logger.info("Player statistics migration completed successfully!")
        logger.info("=" * 60)
        
        # Verify the migration
        logger.info("\n📋 Verifying migration...")
        
        # Check if new columns exist
        verification_columns = ['matches_played', 'total_fantasy_points', 'stats_last_updated', 'season']
        for col in verification_columns:
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'players' AND column_name = :column_name
            """)
            result = db.execute(check_query, {"column_name": col}).fetchone()
            if result:
                logger.info(f"✓ Column {col} exists")
            else:
                logger.warning(f"✗ Column {col} not found")
        
        # Update existing players with default values (only if columns exist)
        try:
            # Check if season column exists before updating
            season_check = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'players' AND column_name = 'season'
            """)
            season_exists = db.execute(season_check).fetchone()
            
            if season_exists:
                update_query = text("""
                    UPDATE players 
                    SET season = '2025-26', stats_last_updated = CURRENT_TIMESTAMP
                    WHERE season IS NULL OR season = ''
                """)
                result = db.execute(update_query)
                db.commit()
                logger.info(f"\n✓ Updated {result.rowcount} players with default season 2025-26")
            
            logger.info("\n" + "=" * 60)
            logger.info("Migration verification completed!")
            logger.info("=" * 60)
            
            logger.info("\n📊 New columns added to players table:")
            logger.info("   - matches_played, minutes_played")
            logger.info("   - yellow_cards, red_cards, clean_sheets")
            logger.info("   - goals_conceded, saves, penalties_saved")
            logger.info("   - total_fantasy_points, last_match_points")
            logger.info("   - points_per_match, form_points")
            logger.info("   - stats_last_updated, season")
            logger.info("   - And more detailed statistics fields...")
            
            logger.info("\n✅ Database is now ready for player stats updates!")
            logger.info("Next step: Run player stats update script")
            logger.info("   docker-compose exec backend python scripts/update_player_stats_from_matchdays.py")
            
        except Exception as e:
            db.rollback()
            logger.warning(f"⚠️  Could not update default values: {e}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"\n❌ Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_player_statistics()
if __name__ == "__main__":
    migrate_player_statistics()
