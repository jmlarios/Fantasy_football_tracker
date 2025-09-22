import sys
from pathlib import Path
import logging

# Adding the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

# Importing necessary modules from config and models
from config import engine, test_database_connection, SessionLocal
from src.models import Base, User, Player, FantasyTeam, Match, FantasyLeague
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database() -> bool:
    """
    Initialize the database by creating all tables from models.
    Returns True if successful, False otherwise.
    """
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("All database tables created successfully!")
        
        # List the tables that were created
        table_names = [table.name for table in Base.metadata.tables.values()]
        logger.info(f"Created tables: {', '.join(table_names)}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False


def check_existing_data() -> dict:
    """
    Check if there's already data in the database.
    Returns a dictionary with counts of records in each table.
    """
    db = SessionLocal()
    try:
        # Check if tables exist first
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if not existing_tables:
            logger.info("No tables exist yet - database is empty")
            return {}
        
        counts = {}
        # Only check tables that actually exist
        if 'users' in existing_tables:
            counts['users'] = db.query(User).count()
        if 'players' in existing_tables:
            counts['players'] = db.query(Player).count()
        if 'fantasy_teams' in existing_tables:
            counts['fantasy_teams'] = db.query(FantasyTeam).count()
        if 'matches' in existing_tables:
            counts['matches'] = db.query(Match).count()
        if 'fantasy_leagues' in existing_tables:
            counts['fantasy_leagues'] = db.query(FantasyLeague).count()
        
        logger.info("Current database state:")
        for table, count in counts.items():
            logger.info(f"   {table}: {count} records")
            
        return counts
    except Exception as e:
        logger.error(f"Error checking existing data: {e}")
        return {}
    finally:
        db.close()


def main():
    """
    Main function to initialize the database.
    """
    logger.info("Starting Fantasy Football Tracker Database Initialization")
    
    # Test database connection first
    logger.info("Testing database connection...")
    if not test_database_connection():
        logger.error("Cannot connect to database. Make sure Docker container is running.")
        logger.info("Try: docker-compose up -d")
        return False
    
    # Check if tables already exist and have data
    logger.info("Checking existing database state...")
    existing_counts = check_existing_data()
    
    if any(count > 0 for count in existing_counts.values()):
        logger.warning("Database already contains data!")
        response = input("Do you want to continue? This will not delete existing data (y/n): ")
        if response.lower() != 'y':
            logger.info("Aborted by user")
            return False
    
    # Initialize database tables
    if not init_database():
        return False
    
    logger.info("Database initialization completed successfully!")
    logger.info("Next step: Add sample data for testing")

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
