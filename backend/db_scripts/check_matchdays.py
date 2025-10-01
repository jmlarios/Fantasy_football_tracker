import sys
from pathlib import Path
import logging

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from config import SessionLocal
from src.models import Matchday

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_matchdays():
    """Check what matchdays exist in the database."""
    db = SessionLocal()
    
    try:
        # Get all matchdays
        matchdays = db.query(Matchday).order_by(Matchday.matchday_number).all()
        
        if not matchdays:
            print("No matchdays found in database")
            return
        
        print(f"Found {len(matchdays)} matchdays in database:")
        print("="*100)
        print(f"{'MD':<3} {'Start Date':<12} {'End Date':<12} {'Deadline':<17} {'Status':<15} {'Transfer Status'}")
        print("="*100)
        
        active_count = 0
        finished_count = 0
        upcoming_count = 0
        
        for md in matchdays:
            # Status indicators
            status_parts = []
            if md.is_active:
                status_parts.append("ACTIVE")
                active_count += 1
            elif md.is_finished:
                status_parts.append("FINISHED")
                finished_count += 1
            else:
                status_parts.append("UPCOMING")
                upcoming_count += 1
            
            if md.points_calculated:
                status_parts.append("CALC")
            
            status_str = " ".join(status_parts)
            
            # Transfer status
            if md.is_transfer_locked:
                transfer_status = "LOCKED"
            else:
                transfer_status = f"{md.time_until_deadline}"
            
            print(f"{md.matchday_number:<3} {md.start_date.strftime('%Y-%m-%d'):<12} {md.end_date.strftime('%Y-%m-%d'):<12} {md.deadline.strftime('%Y-%m-%d %H:%M'):<17} {status_str:<15} {transfer_status}")
        
        print("="*100)
        print(f"📊 Summary: {active_count} active, {finished_count} finished, {upcoming_count} upcoming")
        
        # Check for missing matchdays
        existing_numbers = {md.matchday_number for md in matchdays}
        missing = []
        for i in range(1, 39):  # LaLiga has 38 matchdays
            if i not in existing_numbers:
                missing.append(i)
        
        if missing:
            print(f"Missing matchdays: {', '.join(map(str, missing))}")
        else:
            print("All 38 matchdays present!")
        
        # Show current and next matchdays
        current = next((md for md in matchdays if md.is_active), None)
        if current:
            print(f"\nCurrent Matchday: {current.matchday_number} (ends {current.end_date.strftime('%Y-%m-%d %H:%M')})")
        
        next_md = next((md for md in matchdays if not md.is_finished and not md.is_active), None)
        if next_md:
            print(f"⏭Next Matchday: {next_md.matchday_number} (starts {next_md.start_date.strftime('%Y-%m-%d %H:%M')})")
            
    except Exception as e:
        logger.error(f"Error checking matchdays: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_matchdays()
