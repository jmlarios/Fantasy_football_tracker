"""
Matchday Status Service
Automatically activates/deactivates matchdays based on current date/time.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.models import Matchday
import logging

logger = logging.getLogger(__name__)


class MatchdayStatusService:
    """Service to manage automatic matchday status updates based on dates."""
    
    @staticmethod
    def update_matchday_status(db: Session) -> dict:
        """
        Automatically update matchday statuses based on current date/time.
        
        Logic:
        1. Deactivate matchdays where end_date has passed
        2. Activate matchdays where start_date <= now <= end_date
        3. Only one matchday should be active at a time
        
        Returns:
            dict with status information
        """
        try:
            now = datetime.now(timezone.utc)
            
            # Get all matchdays
            all_matchdays = db.query(Matchday).order_by(Matchday.matchday_number).all()
            
            if not all_matchdays:
                return {
                    'success': True,
                    'message': 'No matchdays found in database',
                    'active_matchday': None,
                    'changes_made': 0
                }
            
            changes_made = 0
            currently_active = None
            
            for matchday in all_matchdays:
                # Handle timezone-aware dates
                start = matchday.start_date
                end = matchday.end_date
                
                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)
                if end.tzinfo is None:
                    end = end.replace(tzinfo=timezone.utc)
                
                # Determine if this matchday should be active
                should_be_active = start <= now <= end
                
                # Check if status needs to be updated
                if should_be_active and not matchday.is_active:
                    # Activate this matchday
                    logger.info(f"Activating Matchday {matchday.matchday_number} (current period)")
                    matchday.is_active = True
                    matchday.is_finished = False
                    changes_made += 1
                    currently_active = matchday.matchday_number
                    
                elif not should_be_active and matchday.is_active:
                    # Deactivate this matchday
                    logger.info(f"Deactivating Matchday {matchday.matchday_number} (period ended)")
                    matchday.is_active = False
                    
                    # Mark as finished if end date has passed
                    if now > end:
                        matchday.is_finished = True
                        
                    changes_made += 1
                    
                elif should_be_active:
                    # Already active and should be - track it
                    currently_active = matchday.matchday_number
            
            # Commit all changes
            if changes_made > 0:
                db.commit()
                logger.info(f"Updated {changes_made} matchday statuses")
            
            return {
                'success': True,
                'message': f'Matchday statuses updated successfully',
                'active_matchday': currently_active,
                'changes_made': changes_made,
                'total_matchdays': len(all_matchdays)
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating matchday statuses: {e}")
            return {
                'success': False,
                'error': str(e),
                'active_matchday': None,
                'changes_made': 0
            }
    
    @staticmethod
    def get_current_matchday(db: Session) -> Matchday | None:
        """
        Get the currently active matchday.
        
        Returns:
            Matchday object if one is active, None otherwise
        """
        return db.query(Matchday).filter(Matchday.is_active == True).first()
    
    @staticmethod
    def get_matchday_info(db: Session) -> dict:
        """
        Get information about current matchday status.
        
        Returns:
            dict with matchday information
        """
        now = datetime.now(timezone.utc)
        current = MatchdayStatusService.get_current_matchday(db)
        
        if not current:
            # No active matchday - find next one
            next_matchday = db.query(Matchday).filter(
                Matchday.start_date > now
            ).order_by(Matchday.start_date.asc()).first()
            
            return {
                'has_active_matchday': False,
                'active_matchday': None,
                'next_matchday': {
                    'matchday_number': next_matchday.matchday_number,
                    'starts_at': next_matchday.start_date.isoformat() if next_matchday else None
                } if next_matchday else None,
                'transfers_allowed': True  # No active matchday means transfers are open
            }
        
        # There is an active matchday
        deadline = current.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        
        transfers_locked = now >= deadline
        
        return {
            'has_active_matchday': True,
            'active_matchday': {
                'matchday_number': current.matchday_number,
                'season': current.season,
                'start_date': current.start_date.isoformat(),
                'end_date': current.end_date.isoformat(),
                'deadline': current.deadline.isoformat(),
                'is_transfer_locked': transfers_locked,
                'time_until_deadline': current.time_until_deadline
            },
            'transfers_allowed': not transfers_locked
        }


# Convenience function for easy import
def update_matchday_status(db: Session) -> dict:
    """Convenience function to update matchday statuses."""
    return MatchdayStatusService.update_matchday_status(db)
