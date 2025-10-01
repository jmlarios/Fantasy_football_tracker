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

def fix_matchday_season():
    """Fix the season dates for matchdays from 2024-2025 to 2025-2026."""
    
    db = SessionLocal()
    try:
        logger.info("=== Fixing Matchday Season ===")
        
        # Check current seasons
        seasons = db.execute(text("""
            SELECT DISTINCT season, COUNT(*) as count 
            FROM matchdays 
            GROUP BY season 
            ORDER BY season
        """)).fetchall()
        
        logger.info("Current seasons in database:")
        for season, count in seasons:
            logger.info(f"  - {season}: {count} matchdays")
        
        # Update season from 2024-2025 to 2025-2026
        result = db.execute(text("""
            UPDATE matchdays 
            SET season = '2025-2026' 
            WHERE season = '2024-2025'
        """))
        
        logger.info(f"Updated {result.rowcount} matchdays from 2024-2025 to 2025-2026")
        
        # Also update any matches with wrong season
        result2 = db.execute(text("""
            UPDATE matches 
            SET season = '2025-2026' 
            WHERE season = '2024-2025'
        """))
        
        logger.info(f"Updated {result2.rowcount} matches from 2024-2025 to 2025-2026")
        
        db.commit()
        
        # Verify the fix
        seasons_after = db.execute(text("""
            SELECT DISTINCT season, COUNT(*) as count 
            FROM matchdays 
            GROUP BY season 
            ORDER BY season
        """)).fetchall()
        
        logger.info("Seasons after fix:")
        for season, count in seasons_after:
            logger.info(f"  - {season}: {count} matchdays")
        
        logger.info("✅ Season fix completed!")
        
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Season fix failed: {e}")
        return False
    finally:
        db.close()

def check_season_status():
    """Check current season status in database."""
    
    db = SessionLocal()
    try:
        # Check matchdays
        matchday_seasons = db.execute(text("""
            SELECT season, COUNT(*) as count
            FROM matchdays 
            GROUP BY season 
            ORDER BY season
        """)).fetchall()
        
        print("📅 Matchdays by season:")
        for season, count in matchday_seasons:
            print(f"   {season}: {count} matchdays")
        
        # Check matches (if they exist)
        try:
            match_seasons = db.execute(text("""
                SELECT season, COUNT(*) as count
                FROM matches 
                GROUP BY season 
                ORDER BY season
            """)).fetchall()
            
            print("\n⚽ Matches by season:")
            for season, count in match_seasons:
                print(f"   {season}: {count} matches")
        except:
            print("\n⚽ No matches table found or no matches")
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking season status: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 50)
    print("🔄 MATCHDAY SEASON UPDATER")
    print("=" * 50)
    
    # Show current status
    print("Current status:")
    check_season_status()
    
    print("\n" + "=" * 50)
    response = input("Update season from 2024-2025 to 2025-2026? (y/n): ")
    
    if response.lower() == 'y':
        success = fix_matchday_season()
        if success:
            print("\n" + "=" * 50)
            print("Updated status:")
            check_season_status()
        else:
            print("❌ Update failed!")
    else:
        print("Update cancelled")
