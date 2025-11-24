from __future__ import annotations

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
import logging

from src.models import (
    FantasyTeam,
    FantasyTeamPlayer,
    LeagueTeam,
    LeagueTeamPlayer,
    Matchday,
    Player,
    TransferHistory,
)

from .base import TransferStrategy
from .contracts import (
    FreeAgentTransferCommand,
    TransferExecutionResult,
    TransferValidationResult,
)

logger = logging.getLogger(__name__)


class FreeAgentQueryService:
    """Read-only helpers for free agent transfer flows."""

    @staticmethod
    def get_available_players(
        db: Session,
        league_id: int,
        position: Optional[str] = None,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> List[Dict]:
        owned_player_ids = (
            db.query(LeagueTeamPlayer.player_id)
            .filter(LeagueTeamPlayer.league_id == league_id)
            .distinct()
            .all()
        )
        owned_ids = [pid[0] for pid in owned_player_ids]

        query = db.query(Player).filter(Player.is_active == True)  # noqa: E712
        if owned_ids:
            query = query.filter(~Player.id.in_(owned_ids))

        if position:
            query = query.filter(Player.position == position)

        if search:
            pattern = f"%{search}%"
            query = query.filter(or_(Player.name.ilike(pattern), Player.team.ilike(pattern)))

        if min_price is not None:
            query = query.filter(Player.price >= min_price)
        if max_price is not None:
            query = query.filter(Player.price <= max_price)

        players = query.order_by(Player.price.desc()).all()
        return [
            {
                "id": player.id,
                "name": player.name,
                "team": player.team,
                "position": player.position,
                "price": player.price,
                "goals": player.goals,
                "assists": player.assists,
                "total_stats": {
                    "goals": player.goals,
                    "assists": player.assists,
                    "yellow_cards": player.yellow_cards,
                    "red_cards": player.red_cards,
                    "minutes_played": player.minutes_played,
                    "clean_sheets": player.clean_sheets,
                },
            }
            for player in players
        ]

    @staticmethod
    def check_player_availability(db: Session, league_id: int, player_id: int) -> Dict:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return {"available": False, "reason": "Player not found"}

        is_owned = (
            db.query(LeagueTeamPlayer)
            .filter(
                LeagueTeamPlayer.league_id == league_id,
                LeagueTeamPlayer.player_id == player_id,
            )
            .first()
            is not None
        )
        if is_owned:
            owner_team = (
                db.query(LeagueTeam)
                .join(LeagueTeamPlayer, LeagueTeam.id == LeagueTeamPlayer.league_team_id)
                .filter(
                    LeagueTeamPlayer.league_id == league_id,
                    LeagueTeamPlayer.player_id == player_id,
                )
                .first()
            )
            return {
                "available": False,
                "reason": "Player already owned in this league",
                "owned_by_team": owner_team.team_name if owner_team else "Unknown",
            }

        return {
            "available": True,
            "player": {
                "id": player.id,
                "name": player.name,
                "team": player.team,
                "position": player.position,
                "price": player.price,
            },
        }


class FreeAgentTransferStrategy(TransferStrategy[FreeAgentTransferCommand]):
    """Transfer strategy for free-agent acquisitions within a league."""

    def validate(self, db: Session, command: FreeAgentTransferCommand) -> TransferValidationResult:
        validation = TransferValidationResult(is_valid=True)

        league_team = (
            db.query(LeagueTeam)
            .filter(
                LeagueTeam.id == command.league_team_id,
                LeagueTeam.league_id == command.league_id,
            )
            .first()
        )
        if not league_team:
            validation.is_valid = False
            validation.errors.append("Team not found in this league")
            return validation

        squad_size = (
            db.query(LeagueTeamPlayer)
            .filter(LeagueTeamPlayer.league_team_id == command.league_team_id)
            .count()
        )
        if squad_size >= 11 and not command.player_out_id:
            validation.is_valid = False
            validation.errors.append("Team has 11 players. You must select a player to drop.")
            return validation
        if squad_size < 11 and command.player_out_id:
            validation.warnings.append(
                f"Team only has {squad_size} players. You can add without dropping anyone."
            )

        current_matchday = db.query(Matchday).filter(Matchday.is_active == True).first()  # noqa: E712
        if current_matchday and current_matchday.is_transfer_locked:
            validation.is_valid = False
            validation.errors.append(
                f"Transfers locked until {current_matchday.end_date}"
            )
            return validation

        player_in = db.query(Player).filter(Player.id == command.player_in_id).first()
        if not player_in:
            validation.is_valid = False
            validation.errors.append("Player to buy not found")
            return validation

        availability = FreeAgentQueryService.check_player_availability(
            db, command.league_id, command.player_in_id
        )
        if not availability.get("available", False):
            validation.is_valid = False
            validation.errors.append(availability.get("reason", "Player unavailable"))
            return validation

        player_out = None
        if command.player_out_id:
            player_out = db.query(Player).filter(Player.id == command.player_out_id).first()
            if not player_out:
                validation.is_valid = False
                validation.errors.append("Player to sell not found")
                return validation

            team_has_player = (
                db.query(LeagueTeamPlayer)
                .filter(
                    LeagueTeamPlayer.league_team_id == command.league_team_id,
                    LeagueTeamPlayer.player_id == command.player_out_id,
                )
                .first()
            )
            if not team_has_player:
                validation.is_valid = False
                validation.errors.append("Player to sell is not in your team")
                return validation

        if player_out and player_in.position != player_out.position:
            validation.warnings.append(
                f"Position change: {player_out.position} → {player_in.position}"
            )

        player_out_price = player_out.price if player_out else 0
        cost = player_in.price - player_out_price
        if cost > league_team.remaining_budget:
            validation.is_valid = False
            validation.errors.append(
                f"Insufficient budget. Need {cost:.2f}M, have {league_team.remaining_budget:.2f}M"
            )

        validation.cost_breakdown = {
            "player_in_price": player_in.price,
            "player_out_price": player_out_price,
            "net_cost": cost,
            "current_budget": league_team.remaining_budget,
            "budget_after_transfer": league_team.remaining_budget - cost,
        }
        return validation

    def execute(self, db: Session, command: FreeAgentTransferCommand) -> TransferExecutionResult:
        validation = self.validate(db, command)
        if not validation.is_valid:
            return TransferExecutionResult(success=False, errors=validation.errors)

        league_team = (
            db.query(LeagueTeam)
            .filter(
                LeagueTeam.id == command.league_team_id,
                LeagueTeam.league_id == command.league_id,
            )
            .first()
        )
        fantasy_team = league_team.fantasy_team if league_team else None
        if not fantasy_team:
            return TransferExecutionResult(
                success=False,
                errors=["Fantasy team for league team not found"],
            )

        if command.user_id is None:
            return TransferExecutionResult(
                success=False,
                errors=["User identifier is required to perform transfers"],
            )

        if fantasy_team.user_id != command.user_id:
            return TransferExecutionResult(
                success=False, errors=["You do not own this team"],
            )

        current_matchday = db.query(Matchday).filter(Matchday.is_active == True).first()  # noqa: E712
        if current_matchday and current_matchday.is_transfer_locked:
            return TransferExecutionResult(
                success=False,
                errors=[
                    f"Transfers are locked during matchday {current_matchday.matchday_number}"
                ],
            )

        player_in = db.query(Player).filter(Player.id == command.player_in_id).first()
        player_out = (
            db.query(Player).filter(Player.id == command.player_out_id).first()
            if command.player_out_id
            else None
        )

        next_matchday = (
            db.query(Matchday)
            .filter(Matchday.is_finished == False)
            .order_by(Matchday.start_date.asc())
            .first()
        )

        try:
            if player_out:
                league_player_out = (
                    db.query(LeagueTeamPlayer)
                    .filter(
                        LeagueTeamPlayer.league_team_id == command.league_team_id,
                        LeagueTeamPlayer.player_id == command.player_out_id,
                    )
                    .first()
                )
                if league_player_out:
                    db.delete(league_player_out)

                fantasy_player_out = (
                    db.query(FantasyTeamPlayer)
                    .filter(
                        FantasyTeamPlayer.fantasy_team_id == fantasy_team.id,
                        FantasyTeamPlayer.player_id == command.player_out_id,
                    )
                    .first()
                )
                if fantasy_player_out:
                    db.delete(fantasy_player_out)

            league_player_in = LeagueTeamPlayer(
                league_team_id=command.league_team_id,
                player_id=command.player_in_id,
                league_id=command.league_id,
                position_in_team=player_in.position,
                added_for_matchday=next_matchday.matchday_number if next_matchday else None,
            )
            db.add(league_player_in)

            fantasy_player_in = FantasyTeamPlayer(
                fantasy_team_id=fantasy_team.id,
                player_id=command.player_in_id,
                position_in_team=player_in.position,
                added_for_matchday=next_matchday.matchday_number if next_matchday else None,
            )
            db.add(fantasy_player_in)

            player_out_price = player_out.price if player_out else 0
            transfer_cost = player_in.price - player_out_price
            transfer_history = TransferHistory(
                fantasy_team_id=fantasy_team.id,
                league_id=command.league_id,
                matchday_id=next_matchday.id if next_matchday else None,
                transfer_type="free_agent",
                player_in_id=command.player_in_id,
                player_out_id=command.player_out_id,
                transfer_cost=transfer_cost,
                is_free_transfer=True,
                penalty_points=0.0,
            )
            db.add(transfer_history)

            db.commit()
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            logger.error("Error executing free transfer: %s", exc)
            return TransferExecutionResult(
                success=False,
                errors=[f"Transfer failed: {exc}"],
            )

        if player_out:
            message = f"Successfully transferred {player_in.name} for {player_out.name}"
        else:
            message = f"Successfully added {player_in.name} to your team"

        return TransferExecutionResult(
            success=True,
            message=message,
            data={
                "player_in": {
                    "id": player_in.id,
                    "name": player_in.name,
                    "position": player_in.position,
                    "price": player_in.price,
                },
                "player_out": {
                    "id": player_out.id,
                    "name": player_out.name,
                    "position": player_out.position,
                    "price": player_out.price,
                }
                if player_out
                else None,
                "cost": transfer_cost,
                "new_budget": league_team.remaining_budget - transfer_cost,
            },
        )
