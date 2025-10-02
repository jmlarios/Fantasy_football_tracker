import sys
from pathlib import Path

# Add the parent directory (backend) to the Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Add src directory to path
src_path = backend_path / "src"
sys.path.insert(0, str(src_path))

from config import engine, SessionLocal
from src.models import Base, FantasyLeagueParticipant
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_league_features():
    """Add league-related tables and update existing data."""
    
    db = SessionLocal()
    try:
        logger.info("Starting league feature migration...")
        
        # Step 1: Add missing columns to existing tables
        logger.info("Adding missing columns...")
        
        # Add creator_id to fantasy_leagues if it doesn't exist
        try:
            db.execute(text("""
                ALTER TABLE fantasy_leagues 
                ADD COLUMN IF NOT EXISTS creator_id INTEGER REFERENCES users(id)
            """))
            logger.info("Added creator_id column to fantasy_leagues")
        except Exception as e:
            logger.warning(f"Could not add creator_id column: {e}")
        
        db.commit()
        logger.info("Column additions completed")
        
        # Step 2: Create new tables
        logger.info("Creating new tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("League tables created successfully")
        
        # Step 3: Update existing leagues to have creator_id
        logger.info("Updating existing data...")
        
        # Set creator_id for leagues without one (use first user as fallback)
        result = db.execute(text("""
            UPDATE fantasy_leagues 
            SET creator_id = (SELECT id FROM users LIMIT 1)
            WHERE creator_id IS NULL
        """))
        logger.info(f"Updated {result.rowcount} leagues with creator_id")
        
        db.commit()
        logger.info("Migration completed successfully!")
        
        # Step 4: Verify the migration
        logger.info("Verifying migration...")
        
        # Check if tables exist
        leagues_count = db.execute(text("SELECT COUNT(*) FROM fantasy_leagues")).scalar()
        participants_table_exists = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'fantasy_league_participants'
            )
        """)).scalar()
        
        logger.info(f"{leagues_count} fantasy leagues exist")
        
        if participants_table_exists:
            logger.info("Fantasy league participants table created")
        else:
            logger.error("Fantasy league participants table not found")
        
        logger.info("League feature migration completed successfully!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_league_features()
