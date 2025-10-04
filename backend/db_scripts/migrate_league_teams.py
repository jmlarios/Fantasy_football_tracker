"""
Database migration script to add league-specific team support.

This migration:
1. Creates league_teams table
2. Creates league_team_players table with unique constraint on (league_id, player_id)
3. Adds league_team_id column to fantasy_league_participants
4. Updates max_players in fantasy_teams from 14 to 11

Run this migration after updating the models.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Execute the migration."""
    
    # Get database URL from config
    database_url = config.db_config.DATABASE_URL
    logger.info(f"Connecting to database: {database_url}")
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        try:
            logger.info("Starting migration...")
            
            # Create league_teams table
            logger.info("Creating league_teams table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS league_teams (
                    id SERIAL PRIMARY KEY,
                    fantasy_team_id INTEGER NOT NULL REFERENCES fantasy_teams(id) ON DELETE CASCADE,
                    league_id INTEGER NOT NULL REFERENCES fantasy_leagues(id) ON DELETE CASCADE,
                    league_points DOUBLE PRECISION DEFAULT 0.0,
                    league_rank INTEGER,
                    total_budget DOUBLE PRECISION DEFAULT 100000000.0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE
                );
            """))
            conn.commit()
            logger.info("league_teams table created successfully")
            
            # Create league_team_players table
            logger.info("Creating league_team_players table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS league_team_players (
                    id SERIAL PRIMARY KEY,
                    league_team_id INTEGER NOT NULL REFERENCES league_teams(id) ON DELETE CASCADE,
                    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
                    league_id INTEGER NOT NULL REFERENCES fantasy_leagues(id) ON DELETE CASCADE,
                    position_in_team VARCHAR(50) NOT NULL,
                    is_captain BOOLEAN DEFAULT FALSE,
                    is_vice_captain BOOLEAN DEFAULT FALSE,
                    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    added_for_matchday INTEGER,
                    CONSTRAINT uix_league_player UNIQUE (league_id, player_id)
                );
            """))
            conn.commit()
            logger.info("league_team_players table created successfully")
            
            # Add league_team_id to fantasy_league_participants if it doesn't exist
            logger.info("Adding league_team_id column to fantasy_league_participants...")
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'fantasy_league_participants' 
                        AND column_name = 'league_team_id'
                    ) THEN
                        ALTER TABLE fantasy_league_participants 
                        ADD COLUMN league_team_id INTEGER REFERENCES league_teams(id) ON DELETE SET NULL;
                    END IF;
                END $$;
            """))
            conn.commit()
            logger.info("league_team_id column added successfully")
            
            # Update max_players in fantasy_teams
            logger.info("Updating max_players in fantasy_teams...")
            conn.execute(text("""
                UPDATE fantasy_teams 
                SET max_players = 11 
                WHERE max_players != 11;
            """))
            conn.commit()
            logger.info("max_players updated successfully")
            
            # Create indexes for better performance
            logger.info("Creating indexes...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_league_teams_fantasy_team 
                ON league_teams(fantasy_team_id);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_league_teams_league 
                ON league_teams(league_id);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_league_team_players_league_team 
                ON league_team_players(league_team_id);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_league_team_players_player 
                ON league_team_players(player_id);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_league_team_players_league 
                ON league_team_players(league_id);
            """))
            conn.commit()
            logger.info("Indexes created successfully")
            
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            conn.rollback()
            raise


if __name__ == "__main__":
    run_migration()
