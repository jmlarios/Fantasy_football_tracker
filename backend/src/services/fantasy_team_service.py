from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from src.models import FantasyTeam, FantasyTeamPlayer, Player, LeagueTeam
import logging


class FantasyTeamService:
    """Application service for managing user fantasy teams."""

    def __init__(self, db: Session, logger: Optional[logging.Logger] = None) -> None:
        self._db = db
        self._logger = logger or logging.getLogger(__name__)

    def create_team(self, user_id: int, team_name: str) -> FantasyTeam:
        existing_team = self._db.query(FantasyTeam).filter(
            FantasyTeam.user_id == user_id,
            FantasyTeam.name == team_name
        ).first()

        if existing_team:
            raise ValueError("Team name already exists")

        team = FantasyTeam(
            user_id=user_id,
            name=team_name,
            total_points=0.0,
            total_budget=150000000.0,
            max_players=15
        )
        self._db.add(team)
        self._db.commit()
        self._db.refresh(team)
        return team

    def list_user_teams(self, user_id: int) -> List[Dict]:
        teams = self._db.query(FantasyTeam).filter(FantasyTeam.user_id == user_id).all()
        team_summaries: List[Dict] = []

        for team in teams:
            player_count = self._db.query(FantasyTeamPlayer).filter(
                FantasyTeamPlayer.fantasy_team_id == team.id
            ).count()

            league_teams = self._db.query(LeagueTeam).filter(
                LeagueTeam.fantasy_team_id == team.id
            ).all()
            total_league_points = sum(lt.league_points for lt in league_teams)

            team_summaries.append({
                'id': team.id,
                'name': team.name,
                'total_points': total_league_points,
                'max_players': team.max_players,
                'total_budget': team.total_budget,
                'player_count': player_count
            })

        return team_summaries

    def get_team_detail(self, team_id: int, user_id: int) -> Optional[Dict]:
        team = self._db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == user_id
        ).first()

        if not team:
            return None

        team_players = self._db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == team_id
        ).all()

        players_data: List[Dict] = []
        for team_player in team_players:
            player = self._db.query(Player).filter(Player.id == team_player.player_id).first()
            if player:
                players_data.append({
                    'id': player.id,
                    'name': player.name,
                    'team': player.team,
                    'position': player.position,
                    'is_captain': team_player.is_captain,
                    'is_vice_captain': team_player.is_vice_captain,
                    'position_in_team': team_player.position_in_team,
                    'price': player.price
                })

        league_teams = self._db.query(LeagueTeam).filter(
            LeagueTeam.fantasy_team_id == team_id
        ).all()
        total_league_points = sum(lt.league_points for lt in league_teams)

        team_dict = {
            'id': team.id,
            'name': team.name,
            'total_points': total_league_points,
            'max_players': team.max_players,
            'total_budget': team.total_budget
        }

        return {
            'team': team_dict,
            'players': players_data,
            'player_count': len(players_data)
        }

    def add_player(self, team_id: int, player_id: int, user_id: int) -> None:
        team = self._db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == user_id
        ).first()

        if not team:
            raise ValueError("Team not found")

        player = self._db.query(Player).filter(Player.id == player_id).first()
        if not player:
            raise ValueError("Player not found")

        existing = self._db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == team_id,
            FantasyTeamPlayer.player_id == player_id
        ).first()

        if existing:
            raise ValueError("Player already in team")

        current_count = self._db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == team_id
        ).count()

        if current_count >= team.max_players:
            raise ValueError(f"Team is full (max {team.max_players} players)")

        team_player = FantasyTeamPlayer(
            fantasy_team_id=team_id,
            player_id=player_id,
            position_in_team=player.position,
            is_captain=False,
            is_vice_captain=False
        )

        self._db.add(team_player)
        self._db.commit()
        self._logger.info("Added player %s to team %s", player.name, team.name)

    def remove_player(self, team_id: int, player_id: int, user_id: int) -> None:
        team = self._db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == user_id
        ).first()

        if not team:
            raise ValueError("Team not found")

        team_player = self._db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == team_id,
            FantasyTeamPlayer.player_id == player_id
        ).first()

        if not team_player:
            raise ValueError("Player not in team")

        self._db.delete(team_player)
        self._db.commit()
        self._logger.info("Removed player %s from team %s", player_id, team.name)

    def set_captain(self, team_id: int, player_id: int, user_id: int, *, is_vice: bool = False) -> None:
        team = self._db.query(FantasyTeam).filter(
            FantasyTeam.id == team_id,
            FantasyTeam.user_id == user_id
        ).first()

        if not team:
            raise ValueError("Team not found")

        team_player = self._db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == team_id,
            FantasyTeamPlayer.player_id == player_id
        ).first()

        if not team_player:
            raise ValueError("Player not in team")

        if is_vice:
            self._db.query(FantasyTeamPlayer).filter(
                FantasyTeamPlayer.fantasy_team_id == team_id,
                FantasyTeamPlayer.is_vice_captain == True
            ).update({'is_vice_captain': False})
            team_player.is_vice_captain = True
            team_player.is_captain = False
        else:
            self._db.query(FantasyTeamPlayer).filter(
                FantasyTeamPlayer.fantasy_team_id == team_id
            ).update({'is_captain': False, 'is_vice_captain': False})
            team_player.is_captain = True
            team_player.is_vice_captain = False

        self._db.commit()
        role = "vice-captain" if is_vice else "captain"
        self._logger.info("Set player %s as %s for team %s", player_id, role, team.name)
