import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from config import engine, SessionLocal
from src.models import Base
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_transfer_features():
    """Add transfer-related tables and update existing data."""
    
    db = SessionLocal()
    try:
        logger.info("Starting transfer feature migration...")
        
        # Step 1: Add missing columns to existing tables
        logger.info("Adding missing columns...")
        
        # Add total_budget to fantasy_teams if it doesn't exist
        try:
            db.execute(text("""
                ALTER TABLE fantasy_teams 
                ADD COLUMN IF NOT EXISTS total_budget FLOAT DEFAULT 100000000.0
            """))
            logger.info("Added total_budget column to fantasy_teams")
        except Exception as e:
            logger.warning(f"Could not add total_budget column: {e}")
        
        # Add price to players if it doesn't exist
        try:
            db.execute(text("""
                ALTER TABLE players 
                ADD COLUMN IF NOT EXISTS price FLOAT DEFAULT 5000000.0
            """))
            logger.info("Added price column to players")
        except Exception as e:
            logger.warning(f"Could not add price column: {e}")
        
        # Add free_transfers to matchdays if it doesn't exist
        try:
            db.execute(text("""
                ALTER TABLE matchdays 
                ADD COLUMN IF NOT EXISTS free_transfers INTEGER DEFAULT 2
            """))
            logger.info("Added free_transfers column to matchdays")
        except Exception as e:
            logger.warning(f"Could not add free_transfers column: {e}")
        
        db.commit()
        logger.info("Column additions completed")
        
        # Step 2: Create new tables (transfer_history)
        logger.info("Creating new tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Transfer tables created successfully")
        
        # Step 3: Update existing data with default values
        logger.info("Updating existing data with default values...")
        
        # Update fantasy teams without budget
        result = db.execute(text("""
            UPDATE fantasy_teams 
            SET total_budget = 100000000.0 
            WHERE total_budget IS NULL OR total_budget = 0
        """))
        logger.info(f"Updated {result.rowcount} fantasy teams with default budget")
        
        # Update players without price (set different prices by position)
        position_prices = {
            'GK': 5000000,   # 5M
            'DEF': 6000000,  # 6M  
            'MID': 8000000,  # 8M
            'FWD': 10000000  # 10M
        }
        
        for position, price in position_prices.items():
            result = db.execute(text("""
                UPDATE players 
                SET price = :price 
                WHERE position = :position AND (price IS NULL OR price = 0)
            """), {'price': price, 'position': position})
            logger.info(f"Updated {result.rowcount} {position} players with price {price:,}")
        
        # Update matchdays without free_transfers
        result = db.execute(text("""
            UPDATE matchdays 
            SET free_transfers = 2 
            WHERE free_transfers IS NULL OR free_transfers = 0
        """))
        logger.info(f"Updated {result.rowcount} matchdays with default free transfers")
        
        db.commit()
        logger.info("Migration completed successfully!")
        
        # Step 4: Verify the migration
        logger.info("Verifying migration...")
        
        # Check if columns exist and have data
        fantasy_teams_count = db.execute(text("SELECT COUNT(*) FROM fantasy_teams WHERE total_budget > 0")).scalar()
        players_with_price = db.execute(text("SELECT COUNT(*) FROM players WHERE price > 0")).scalar()
        matchdays_with_transfers = db.execute(text("SELECT COUNT(*) FROM matchdays WHERE free_transfers > 0")).scalar()
        
        logger.info(f"{fantasy_teams_count} fantasy teams have budget")
        logger.info(f"{players_with_price} players have prices")
        logger.info(f"{matchdays_with_transfers} matchdays have free transfer settings")
        
        # Check if transfer_history table exists
        transfer_table_exists = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'transfer_history'
            )
        """)).scalar()
        
        if transfer_table_exists:
            logger.info("Transfer history table created")
        else:
            logger.error("Transfer history table not found")
        
        logger.info("Transfer feature migration completed successfully!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_transfer_features()
