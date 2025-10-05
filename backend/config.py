import os
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration using Docker credentials."""
    
    # Use your Docker database credentials
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://fantasy:football@db:5432/tracker"
    )
    
    # SQLAlchemy settings
    POOL_SIZE: int = 10
    MAX_OVERFLOW: int = 20
    POOL_PRE_PING: bool = True
    ECHO_SQL: bool = os.getenv("DEBUG", "false").lower() == "true"


class AppConfig:
    """Application configuration for FastAPI."""
    
    APP_NAME: str = "LaLiga Fantasy Football Tracker"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # FastAPI settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5000"))


# Initialize database configuration
db_config = DatabaseConfig()
app_config = AppConfig()

# Create SQLAlchemy engine
engine = create_engine(
    db_config.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=db_config.POOL_SIZE,
    max_overflow=db_config.MAX_OVERFLOW,
    pool_pre_ping=db_config.POOL_PRE_PING,
    echo=db_config.ECHO_SQL
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_database_connection() -> bool:
    """
    Test the database connection.
    Returns True if successful, False otherwise.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False
