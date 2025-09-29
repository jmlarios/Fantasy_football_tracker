import sys
from pathlib import Path
import logging
from sqlalchemy import text

# Adding the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from config import engine, SessionLocal
from src.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Run database migration to add Matchday table and update existing tables."""
    
    logger.info("Starting database migration for Matchday system...")
    
    try:
        # Create all new tables (this will only create tables that don't exist)
        logger.info("Creating new tables...")
        Base.metadata.create_all(bind=engine)
        
        # Add new columns to existing tables
        with engine.connect() as conn:
            logger.info("Adding new columns to existing tables...")
            
            # Add matchday_id to matches table
            try:
                conn.execute(text("""
                    ALTER TABLE matches 
                    ADD COLUMN matchday_id INTEGER REFERENCES matchdays(id);
                """))
                logger.info("Added matchday_id column to matches table")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info("matchday_id column already exists in matches table")
                else:
                    logger.warning(f"Could not add matchday_id column: {e}")
            
            # Add transfer tracking to fantasy_team_players table
            try:
                conn.execute(text("""
                    ALTER TABLE fantasy_team_players 
                    ADD COLUMN added_for_matchday INTEGER;
                """))
                logger.info("Added added_for_matchday column to fantasy_team_players table")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info("added_for_matchday column already exists in fantasy_team_players table")
                else:
                    logger.warning(f"Could not add added_for_matchday column: {e}")
            
            conn.commit()
        
        logger.info("Database migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


def check_migration_status():
    """Check if migration has been applied."""
    
    try:
        with engine.connect() as conn:
            # Check if matchdays table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'matchdays'
                );
            """))
            
            matchdays_exists = result.fetchone()[0]
            
            if matchdays_exists:
                # Count matchdays
                result = conn.execute(text("SELECT COUNT(*) FROM matchdays"))
                matchday_count = result.fetchone()[0]
                
                logger.info(f"Migration status: APPLIED")
                logger.info(f"Matchdays table exists with {matchday_count} records")
            else:
                logger.info("Migration status: NOT APPLIED")
                logger.info("Matchdays table does not exist")
            
            return matchdays_exists
            
    except Exception as e:
        logger.error(f"Could not check migration status: {e}")
        return False


if __name__ == "__main__":
    logger.info("=== Matchday Migration Tool ===")
    
    # Check current status
    is_migrated = check_migration_status()
    
    if not is_migrated:
        response = input("Apply migration? (y/n): ")
        if response.lower() == 'y':
            success = run_migration()
            if success:
                logger.info("Migration completed! You can now initialize matchday data.")
            else:
                logger.error("Migration failed!")
                sys.exit(1)
        else:
            logger.info("Migration cancelled")
    else:
        logger.info("Migration already applied!")
