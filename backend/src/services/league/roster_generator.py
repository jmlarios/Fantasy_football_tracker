from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models import LeagueTeamPlayer, FantasyTeamPlayer, Player
import logging


class RosterGenerator:
    """Generate initial rosters for league teams."""

    def __init__(self, formation: Optional[Dict[str, int]] = None, logger: Optional[logging.Logger] = None) -> None:
        self._formation = formation or {'GK': 1, 'DEF': 4, 'MID': 4, 'FWD': 2}
        self._logger = logger or logging.getLogger(__name__)

    def generate_initial_squad(
        self,
        db: Session,
        *,
        league_team_id: int,
        league_id: int,
        fantasy_team_id: int,
    ) -> None:
        players_added = []

        for position, count in self._formation.items():
            available_players = db.query(Player).filter(
                Player.position == position,
                Player.is_active == True,
                ~Player.id.in_(
                    db.query(LeagueTeamPlayer.player_id).filter(
                        LeagueTeamPlayer.league_id == league_id
                    )
                )
            ).order_by(func.random()).limit(count).all()

            if len(available_players) < count:
                self._logger.warning("Not enough %s players available for auto squad", position)
                continue

            for player in available_players:
                league_player = LeagueTeamPlayer(
                    league_team_id=league_team_id,
                    player_id=player.id,
                    league_id=league_id,
                    position_in_team=position,
                    is_captain=False,
                    is_vice_captain=False
                )
                fantasy_player = FantasyTeamPlayer(
                    fantasy_team_id=fantasy_team_id,
                    player_id=player.id,
                    position_in_team=position,
                    is_captain=False,
                    is_vice_captain=False
                )
                db.add(league_player)
                db.add(fantasy_player)
                players_added.append(player.id)

        db.flush()
        self._logger.info(
            "Auto-generated %s players for league team %s",
            len(players_added),
            league_team_id,
        )
