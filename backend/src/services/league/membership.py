from typing import Optional
from sqlalchemy.orm import Session
from src.models import FantasyLeagueParticipant, FantasyLeague
import logging


class LeagueMembershipService:
    """Encapsulates membership policies for fantasy leagues."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._logger = logger or logging.getLogger(__name__)

    def ensure_user_can_join(self, db: Session, league_id: int, user_id: int, max_participants: int) -> int:
        existing_participant = db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.league_id == league_id,
            FantasyLeagueParticipant.user_id == user_id
        ).first()
        if existing_participant:
            raise ValueError("You are already a member of this league")

        current_count = self.count_participants(db, league_id)
        if current_count >= max_participants:
            raise ValueError("League is full")

        return current_count

    def count_participants(self, db: Session, league_id: int) -> int:
        return db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.league_id == league_id
        ).count()

    def remove_participant(self, db: Session, league_id: int, user_id: int) -> Optional[FantasyLeagueParticipant]:
        participant = db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.league_id == league_id,
            FantasyLeagueParticipant.user_id == user_id
        ).first()

        if not participant:
            return None

        db.delete(participant)
        return participant

    def transfer_ownership_if_needed(self, db: Session, league: FantasyLeague, departing_user_id: int) -> None:
        if league.creator_id != departing_user_id:
            return

        successor = db.query(FantasyLeagueParticipant).filter(
            FantasyLeagueParticipant.league_id == league.id,
            FantasyLeagueParticipant.user_id != departing_user_id
        ).first()

        if successor:
            league.creator_id = successor.user_id
            self._logger.info(
                "Transferred league %s ownership to user %s",
                league.id,
                successor.user_id,
            )
        else:
            db.delete(league)
            self._logger.info("Removed empty league %s", league.id)
