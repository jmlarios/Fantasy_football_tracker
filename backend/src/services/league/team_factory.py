from typing import Optional
from sqlalchemy.orm import Session
from src.models import FantasyTeam, LeagueTeam, FantasyLeagueParticipant
import logging


class TeamFactory:
    """Factory for creating league-related team entities."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._logger = logger or logging.getLogger(__name__)

    def create_user_team(self, db: Session, user_id: int, team_name: str) -> FantasyTeam:
        team = FantasyTeam(user_id=user_id, name=team_name)
        db.add(team)
        db.flush()
        self._logger.info("Created fantasy team %s for user %s", team_name, user_id)
        return team

    def create_league_team(self, db: Session, league_id: int, fantasy_team_id: int, team_name: str) -> LeagueTeam:
        league_team = LeagueTeam(
            league_id=league_id,
            fantasy_team_id=fantasy_team_id,
            team_name=team_name
        )
        db.add(league_team)
        db.flush()
        self._logger.info(
            "Created league team %s for fantasy team %s in league %s",
            team_name,
            fantasy_team_id,
            league_id,
        )
        return league_team

    def create_participant(
        self,
        db: Session,
        league_id: int,
        user_id: int,
        fantasy_team_id: int,
        league_team_id: int,
    ) -> FantasyLeagueParticipant:
        participant = FantasyLeagueParticipant(
            league_id=league_id,
            user_id=user_id,
            fantasy_team_id=fantasy_team_id,
            league_team_id=league_team_id
        )
        db.add(participant)
        self._logger.info(
            "Registered participant %s in league %s with team %s",
            user_id,
            league_id,
            league_team_id,
        )
        return participant
