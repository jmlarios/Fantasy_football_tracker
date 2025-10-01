import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from config import SessionLocal
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_schema():
    """Check the current database schema and missing columns."""
    
    db = SessionLocal()
    try:
        logger.info("=== Database Schema Check ===")
        
        # Check existing tables
        tables = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)).fetchall()
        
        logger.info(f"Found {len(tables)} tables:")
        for table in tables:
            logger.info(f"  - {table[0]}")
        
        # Check specific columns we need
        logger.info("\n=== Column Checks ===")
        
        # Check fantasy_teams columns
        fantasy_teams_columns = db.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'fantasy_teams'
            ORDER BY ordinal_position
        """)).fetchall()
        
        logger.info("fantasy_teams columns:")
        has_total_budget = False
        for col in fantasy_teams_columns:
            logger.info(f"  - {col[0]} ({col[1]}) {'NULL' if col[2]=='YES' else 'NOT NULL'} {col[3] or ''}")
            if col[0] == 'total_budget':
                has_total_budget = True
        
        if not has_total_budget:
            logger.warning("Missing: total_budget column in fantasy_teams")
        else:
            logger.info("total_budget column exists")
        
        # Check players columns
        players_columns = db.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'players'
            ORDER BY ordinal_position
        """)).fetchall()
        
        logger.info("\n📊 players columns:")
        has_price = False
        for col in players_columns:
            logger.info(f"  - {col[0]} ({col[1]}) {'NULL' if col[2]=='YES' else 'NOT NULL'} {col[3] or ''}")
            if col[0] == 'price':
                has_price = True
        
        if not has_price:
            logger.warning("Missing: price column in players")
        else:
            logger.info("price column exists")
        
        # Check matchdays columns
        matchdays_columns = db.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'matchdays'
            ORDER BY ordinal_position
        """)).fetchall()
        
        logger.info("\nmatchdays columns:")
        has_free_transfers = False
        for col in matchdays_columns:
            logger.info(f"  - {col[0]} ({col[1]}) {'NULL' if col[2]=='YES' else 'NOT NULL'} {col[3] or ''}")
            if col[0] == 'free_transfers':
                has_free_transfers = True
        
        if not has_free_transfers:
            logger.warning("Missing: free_transfers column in matchdays")
        else:
            logger.info("free_transfers column exists")
        
        # Check data counts
        logger.info("\n=== Data Counts ===")
        
        counts = {
            'users': db.execute(text("SELECT COUNT(*) FROM users")).scalar(),
            'players': db.execute(text("SELECT COUNT(*) FROM players")).scalar(),
            'fantasy_teams': db.execute(text("SELECT COUNT(*) FROM fantasy_teams")).scalar(),
            'matchdays': db.execute(text("SELECT COUNT(*) FROM matchdays")).scalar(),
        }
        
        for table, count in counts.items():
            logger.info(f"📈 {table}: {count} records")
        
        # Check if transfer_history exists
        transfer_exists = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'transfer_history'
            )
        """)).scalar()
        
        if transfer_exists:
            transfer_count = db.execute(text("SELECT COUNT(*) FROM transfer_history")).scalar()
            logger.info(f"transfer_history: {transfer_count} records")
        else:
            logger.warning("transfer_history table does not exist")
        
        logger.info("\n=== Schema Check Complete ===")
        
    except Exception as e:
        logger.error(f"Schema check failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_database_schema()
