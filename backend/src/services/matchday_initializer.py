import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import logging

# Add backend root to path
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from config import SessionLocal
from src.models import Matchday, Match

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MatchdayInitializer:
    """Service to initialize LaLiga matchdays from fixture data."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def parse_fixture_csv_data(self, csv_data: str) -> List[Dict]:
        """Parse the CSV fixture data into structured format."""
        fixtures = []
        lines = csv_data.strip().split('\n')
        
        for line in lines:
            if not line.strip():
                continue
                
            parts = line.split(',')
            if len(parts) >= 6:
                try:
                    # Parse CSV format: id,date,round,home_team,home_score,away_team,away_score,status,image
                    fixture = {
                        'id': parts[0],
                        'date': parts[1],
                        'round': parts[2].replace('Round ', ''),
                        'home_team': parts[3],
                        'home_score': parts[4] if parts[4] else None,
                        'away_team': parts[5],
                        'away_score': parts[6] if len(parts) > 6 and parts[6] else None,
                        'status': 'finished' if parts[4] and parts[6] else 'scheduled'
                    }
                    fixtures.append(fixture)
                except Exception as e:
                    logger.warning(f"Could not parse line: {line} - {e}")
        
        logger.info(f"Parsed {len(fixtures)} fixtures from CSV data")
        return fixtures
    
    def group_fixtures_by_matchday(self, fixtures: List[Dict]) -> Dict[int, List[Dict]]:
        """Group fixtures by matchday number."""
        matchdays = {}
        
        for fixture in fixtures:
            try:
                matchday_num = int(fixture['round'])
                if matchday_num not in matchdays:
                    matchdays[matchday_num] = []
                matchdays[matchday_num].append(fixture)
            except ValueError:
                logger.warning(f"Invalid matchday number: {fixture['round']}")
        
        logger.info(f"Grouped fixtures into {len(matchdays)} matchdays")
        return matchdays
    
    def calculate_matchday_periods(self, matchday_fixtures: Dict[int, List[Dict]]) -> List[Dict]:
        """Calculate start/end dates and deadlines for each matchday."""
        matchday_periods = []
        
        for matchday_num, fixtures in matchday_fixtures.items():
            try:
                # Parse all dates for this matchday
                match_dates = []
                for fixture in fixtures:
                    try:
                        # Parse date format: 2025-08-15
                        match_date = datetime.strptime(fixture['date'], '%Y-%m-%d')
                        match_date = match_date.replace(tzinfo=timezone.utc)
                        match_dates.append(match_date)
                    except ValueError as e:
                        logger.warning(f"Could not parse date {fixture['date']}: {e}")
                
                if not match_dates:
                    logger.warning(f"No valid dates found for matchday {matchday_num}")
                    continue
                
                # Calculate period
                start_date = min(match_dates)
                end_date = max(match_dates) + timedelta(hours=23, minutes=59)  # End of last match day
                
                # Transfer deadline: 2 hours before first match
                deadline = start_date - timedelta(hours=2)
                
                matchday_periods.append({
                    'matchday_number': matchday_num,
                    'season': '2025-2026',
                    'start_date': start_date,
                    'end_date': end_date,
                    'deadline': deadline,
                    'fixtures': fixtures
                })
                
                logger.info(f"Matchday {matchday_num}: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
                
            except Exception as e:
                logger.error(f"Error processing matchday {matchday_num}: {e}")
        
        # Sort by matchday number
        matchday_periods.sort(key=lambda x: x['matchday_number'])
        return matchday_periods
    
    def initialize_matchdays(self, csv_data: str) -> Dict:
        """Initialize all matchdays from CSV data."""
        results = {
            'matchdays_created': 0,
            'matches_updated': 0,
            'errors': []
        }
        
        try:
            # Parse CSV data
            fixtures = self.parse_fixture_csv_data(csv_data)
            if not fixtures:
                raise ValueError("No fixtures found in CSV data")
            
            # Group by matchday
            matchday_fixtures = self.group_fixtures_by_matchday(fixtures)
            
            # Calculate periods
            matchday_periods = self.calculate_matchday_periods(matchday_fixtures)
            
            # Create matchday records
            for period in matchday_periods:
                try:
                    # Check if matchday already exists
                    existing = self.db.query(Matchday).filter(
                        Matchday.matchday_number == period['matchday_number'],
                        Matchday.season == period['season']
                    ).first()
                    
                    if existing:
                        # Update existing matchday
                        existing.start_date = period['start_date']
                        existing.end_date = period['end_date']
                        existing.deadline = period['deadline']
                        logger.info(f"Updated existing matchday {period['matchday_number']}")
                    else:
                        # Create new matchday
                        matchday = Matchday(
                            matchday_number=period['matchday_number'],
                            season=period['season'],
                            start_date=period['start_date'],
                            end_date=period['end_date'],
                            deadline=period['deadline'],
                            is_active=False,
                            is_finished=False,
                            points_calculated=False
                        )
                        self.db.add(matchday)
                        results['matchdays_created'] += 1
                        logger.info(f"Created matchday {period['matchday_number']}")
                    
                    # Update existing matches to link to this matchday
                    self._link_matches_to_matchday(period)
                    
                except Exception as e:
                    error_msg = f"Error creating matchday {period['matchday_number']}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            self.db.commit()
            logger.info(f"Successfully created/updated {results['matchdays_created']} matchdays")
            
        except Exception as e:
            self.db.rollback()
            error_msg = f"Failed to initialize matchdays: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
    def _link_matches_to_matchday(self, period: Dict):
        """Link existing matches to their matchday."""
        try:
            # Get the matchday record
            matchday = self.db.query(Matchday).filter(
                Matchday.matchday_number == period['matchday_number'],
                Matchday.season == period['season']
            ).first()
            
            if not matchday:
                return
            
            # Update matches for this matchday
            updated = self.db.query(Match).filter(
                Match.matchday == period['matchday_number'],
                Match.season == period['season']
            ).update({Match.matchday_id: matchday.id})
            
            if updated > 0:
                logger.info(f"Linked {updated} matches to matchday {period['matchday_number']}")
        
        except Exception as e:
            logger.error(f"Error linking matches to matchday {period['matchday_number']}: {e}")
    
    def get_current_matchday(self) -> Matchday:
        """Get the currently active matchday."""
        now = datetime.utcnow()
        return self.db.query(Matchday).filter(
            Matchday.start_date <= now,
            Matchday.end_date >= now
        ).first()
    
    def get_next_matchday(self) -> Matchday:
        """Get the next upcoming matchday."""
        now = datetime.utcnow()
        return self.db.query(Matchday).filter(
            Matchday.start_date > now
        ).order_by(Matchday.start_date.asc()).first()
    
    def update_matchday_status(self):
        """Update active/finished status for all matchdays."""
        now = datetime.utcnow()
        
        # Set active matchdays
        active_updated = self.db.query(Matchday).filter(
            Matchday.start_date <= now,
            Matchday.end_date >= now,
            Matchday.is_active == False
        ).update({Matchday.is_active: True})
        
        # Set finished matchdays
        finished_updated = self.db.query(Matchday).filter(
            Matchday.end_date < now,
            Matchday.is_finished == False
        ).update({Matchday.is_finished: True, Matchday.is_active: False})
        
        # Clear active status for future matchdays
        future_updated = self.db.query(Matchday).filter(
            Matchday.start_date > now,
            Matchday.is_active == True
        ).update({Matchday.is_active: False})
        
        self.db.commit()
        
        if active_updated or finished_updated or future_updated:
            logger.info(f"Updated matchday status: {active_updated} active, {finished_updated} finished, {future_updated} future")
    
    def close(self):
        """Close database connection."""
        self.db.close()


def initialize_laliga_matchdays(csv_data: str) -> Dict:
    """
    Initialize LaLiga matchdays from fixture CSV data.
    
    Args:
        csv_data: CSV string with fixture data
        
    Returns:
        Dictionary with initialization results
    """
    from config import SessionLocal
    from src.models import Matchday, Match
    
    results = {
        'matchdays_created': 0,
        'matches_updated': 0,
        'errors': []
    }
    
    db = SessionLocal()
    
    try:
        # Parse fixtures and group by matchday
        matchday_fixtures = {}
        
        for line in csv_data.strip().split('\n'):
            if not line.strip():
                continue
                
            try:
                parts = line.split(',')
                if len(parts) < 6:
                    continue
                
                match_id = parts[0]
                match_date_str = parts[1]
                round_str = parts[2]
                home_team = parts[3]
                away_team = parts[5]
                
                # Extract matchday number
                matchday_num = int(round_str.replace('Round ', ''))
                
                # Parse date with timezone awareness
                match_date = datetime.strptime(match_date_str, '%Y-%m-%d')
                match_date = match_date.replace(tzinfo=timezone.utc)
                
                if matchday_num not in matchday_fixtures:
                    matchday_fixtures[matchday_num] = []
                
                matchday_fixtures[matchday_num].append({
                    'match_id': match_id,
                    'date': match_date,
                    'home_team': home_team,
                    'away_team': away_team
                })
                
            except Exception as e:
                results['errors'].append(f"Error parsing line: {line[:50]}... - {str(e)}")
                continue
        
        logger.info(f"Parsed {len(matchday_fixtures)} unique matchdays")
        
        # Create/update matchdays
        for matchday_num, fixtures in matchday_fixtures.items():
            try:
                # Calculate matchday period from fixtures
                fixture_dates = [f['date'] for f in fixtures]
                start_date = min(fixture_dates)
                end_date = max(fixture_dates) + timedelta(hours=23, minutes=59)
                
                # Transfer deadline: 2 hours before first match
                deadline = start_date - timedelta(hours=2)
                
                # Check if matchday exists
                existing_matchday = db.query(Matchday).filter(
                    Matchday.matchday_number == matchday_num,
                    Matchday.season == "2025-2026"
                ).first()
                
                if existing_matchday:
                    # Update existing matchday dates
                    existing_matchday.start_date = start_date
                    existing_matchday.end_date = end_date
                    existing_matchday.deadline = deadline
                    logger.info(f"Updated existing matchday {matchday_num}")
                else:
                    # Create new matchday
                    matchday = Matchday(
                        matchday_number=matchday_num,
                        season="2025-2026",
                        start_date=start_date,
                        end_date=end_date,
                        deadline=deadline,
                        is_active=False,
                        is_finished=False,
                        points_calculated=False
                    )
                    
                    db.add(matchday)
                    results['matchdays_created'] += 1
                    logger.info(f"Created matchday {matchday_num}")
                
                results['matches_updated'] += len(fixtures)
                
            except Exception as e:
                error_msg = f"Error processing matchday {matchday_num}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
                continue
        
        # Commit changes
        db.commit()
        
        # Update matchday statuses based on current time
        update_matchday_statuses(db)
        
        logger.info(f"Successfully created/updated matchdays")
        logger.info("Matchday initialization completed!")
        logger.info(f"Results: {results}")
        
    except Exception as e:
        db.rollback()
        error_msg = f"Failed to initialize matchdays: {str(e)}"
        results['errors'].append(error_msg)
        logger.error(error_msg)
        
    finally:
        db.close()
    
    return results


def update_matchday_statuses(db: Session):
    """Update matchday statuses based on current time."""
    try:
        now = datetime.now(timezone.utc)
        
        # Set active matchdays (currently in progress)
        active_updated = db.execute(
            """UPDATE matchdays SET 
               is_active=true, 
               updated_at=now() 
               WHERE start_date <= :now 
               AND end_date >= :now 
               AND is_active = false""",
            {'now': now}
        ).rowcount
        
        # Set finished matchdays
        finished_updated = db.execute(
            """UPDATE matchdays SET 
               is_active=false, 
               is_finished=true, 
               updated_at=now() 
               WHERE end_date < :now 
               AND is_finished = false""",
            {'now': now}
        ).rowcount
        
        # Deactivate future matchdays
        future_updated = db.execute(
            """UPDATE matchdays SET 
               is_active=false, 
               updated_at=now() 
               WHERE start_date > :now 
               AND is_active = true""",
            {'now': now}
        ).rowcount
        
        db.commit()
        
        if active_updated or finished_updated or future_updated:
            logger.info(f"Updated matchday status: {active_updated} active, {finished_updated} finished, {future_updated} future")
            
    except Exception as e:
        logger.error(f"Error updating matchday statuses: {e}")
        db.rollback()
