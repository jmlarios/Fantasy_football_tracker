from __future__ import annotations

from abc import ABC
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from src.models import (
    FantasyTeamPlayer,
    LeagueTeam,
    LeagueTeamPlayer,
    Matchday,
    Player,
    TransferHistory,
    TransferOffer,
)

from .base import TransferStrategy
from .contracts import OfferAcceptanceContext, TransferExecutionResult, TransferValidationResult


class OfferStrategy(TransferStrategy[OfferAcceptanceContext], ABC):
    """Base class for offer execution strategies."""

    offer_type: str

    def supports(self, offer: TransferOffer) -> bool:
        return offer.offer_type == self.offer_type

    def validate(self, db: Session, command: OfferAcceptanceContext) -> TransferValidationResult:
        current_matchday = db.query(Matchday).filter(Matchday.is_active == True).first()  # noqa: E712
        if current_matchday and current_matchday.is_transfer_locked:
            return TransferValidationResult(
                is_valid=False,
                errors=["Transfers are locked during active matchday"],
            )
        return TransferValidationResult(is_valid=True)


class MoneyOfferStrategy(OfferStrategy):
    offer_type = "money"

    def execute(self, db: Session, command: OfferAcceptanceContext) -> TransferExecutionResult:
        validation = self.validate(db, command)
        if not validation.is_valid:
            return TransferExecutionResult(success=False, errors=validation.errors)

        offer = command.offer
        from_team = db.query(LeagueTeam).filter(LeagueTeam.id == offer.from_team_id).first()
        to_team = db.query(LeagueTeam).filter(LeagueTeam.id == offer.to_team_id).first()
        player_in = db.query(Player).filter(Player.id == offer.player_id).first()
        player_out = (
            db.query(Player).filter(Player.id == offer.player_out_id).first()
            if offer.player_out_id
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
                buyer_player_out = (
                    db.query(LeagueTeamPlayer)
                    .filter(
                        LeagueTeamPlayer.league_team_id == from_team.id,
                        LeagueTeamPlayer.player_id == player_out.id,
                    )
                    .first()
                )
                if buyer_player_out:
                    db.delete(buyer_player_out)

                fantasy_buyer_player_out = (
                    db.query(FantasyTeamPlayer)
                    .filter(
                        FantasyTeamPlayer.fantasy_team_id == from_team.fantasy_team_id,
                        FantasyTeamPlayer.player_id == player_out.id,
                    )
                    .first()
                )
                if fantasy_buyer_player_out:
                    db.delete(fantasy_buyer_player_out)

            seller_player = (
                db.query(LeagueTeamPlayer)
                .filter(
                    LeagueTeamPlayer.league_team_id == to_team.id,
                    LeagueTeamPlayer.player_id == player_in.id,
                )
                .first()
            )
            if seller_player:
                db.delete(seller_player)

            fantasy_seller_player = (
                db.query(FantasyTeamPlayer)
                .filter(
                    FantasyTeamPlayer.fantasy_team_id == to_team.fantasy_team_id,
                    FantasyTeamPlayer.player_id == player_in.id,
                )
                .first()
            )
            if fantasy_seller_player:
                db.delete(fantasy_seller_player)

            db.flush()

            buyer_player = LeagueTeamPlayer(
                league_team_id=from_team.id,
                player_id=player_in.id,
                league_id=offer.league_id,
                position_in_team=player_in.position,
                added_for_matchday=next_matchday.matchday_number if next_matchday else None,
            )
            db.add(buyer_player)

            fantasy_buyer_player = FantasyTeamPlayer(
                fantasy_team_id=from_team.fantasy_team_id,
                player_id=player_in.id,
                position_in_team=player_in.position,
                added_for_matchday=next_matchday.matchday_number if next_matchday else None,
            )
            db.add(fantasy_buyer_player)

            to_team.total_budget += offer.money_offered
            from_team.total_budget -= offer.money_offered

            history_entries = _build_history_entries_for_money_offer(
                offer=offer,
                next_matchday_id=next_matchday.id if next_matchday else None,
                next_matchday_number=next_matchday.matchday_number if next_matchday else None,
            )
            for entry in history_entries:
                db.add(entry)

            db.commit()
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            return TransferExecutionResult(success=False, errors=[str(exc)])

        return TransferExecutionResult(
            success=True,
            message=f"{player_in.name} transferred for {offer.money_offered:.2f}M",
        )


class PlayerExchangeOfferStrategy(OfferStrategy):
    offer_type = "player_exchange"

    def execute(self, db: Session, command: OfferAcceptanceContext) -> TransferExecutionResult:
        validation = self.validate(db, command)
        if not validation.is_valid:
            return TransferExecutionResult(success=False, errors=validation.errors)

        offer = command.offer
        from_team = db.query(LeagueTeam).filter(LeagueTeam.id == offer.from_team_id).first()
        to_team = db.query(LeagueTeam).filter(LeagueTeam.id == offer.to_team_id).first()
        player_requested = db.query(Player).filter(Player.id == offer.player_id).first()
        player_offered = db.query(Player).filter(Player.id == offer.player_offered_id).first()

        next_matchday = (
            db.query(Matchday)
            .filter(Matchday.is_finished == False)
            .order_by(Matchday.start_date.asc())
            .first()
        )

        try:
            _swap_players_between_teams(
                db=db,
                from_team=from_team,
                to_team=to_team,
                player_requested=player_requested,
                player_offered=player_offered,
                matchday_number=next_matchday.matchday_number if next_matchday else None,
                matchday_id=next_matchday.id if next_matchday else None,
            )
            db.commit()
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            return TransferExecutionResult(success=False, errors=[str(exc)])

        return TransferExecutionResult(
            success=True,
            message=f"Players exchanged: {player_requested.name} ↔ {player_offered.name}",
        )


def _build_history_entries_for_money_offer(
    *,
    offer: TransferOffer,
    next_matchday_id: Optional[int],
    next_matchday_number: Optional[int],
) -> Iterable[TransferHistory]:
    buyer_history = TransferHistory(
        fantasy_team_id=offer.from_team.fantasy_team_id,
        league_id=offer.league_id,
        matchday_id=next_matchday_id,
        transfer_type="user_to_user",
        player_in_id=offer.player_id,
        player_out_id=offer.player_out_id,
        transfer_cost=-offer.money_offered,
        seller_team_id=offer.to_team.fantasy_team_id,
        transfer_offer_id=offer.id,
        is_free_transfer=False,
    )
    seller_history = TransferHistory(
        fantasy_team_id=offer.to_team.fantasy_team_id,
        league_id=offer.league_id,
        matchday_id=next_matchday_id,
        transfer_type="user_to_user",
        player_in_id=None,
        player_out_id=offer.player_id,
        transfer_cost=offer.money_offered,
        seller_team_id=offer.from_team.fantasy_team_id,
        transfer_offer_id=offer.id,
        is_free_transfer=False,
    )
    return buyer_history, seller_history


def _swap_players_between_teams(
    *,
    db: Session,
    from_team: LeagueTeam,
    to_team: LeagueTeam,
    player_requested: Player,
    player_offered: Player,
    matchday_number: Optional[int],
    matchday_id: Optional[int],
) -> None:
    to_team_player = (
        db.query(LeagueTeamPlayer)
        .filter(
            LeagueTeamPlayer.league_team_id == to_team.id,
            LeagueTeamPlayer.player_id == player_requested.id,
        )
        .first()
    )
    if to_team_player:
        db.delete(to_team_player)

    from_team_player = (
        db.query(LeagueTeamPlayer)
        .filter(
            LeagueTeamPlayer.league_team_id == from_team.id,
            LeagueTeamPlayer.player_id == player_offered.id,
        )
        .first()
    )
    if from_team_player:
        db.delete(from_team_player)

    fantasy_to_team_player = (
        db.query(FantasyTeamPlayer)
        .filter(
            FantasyTeamPlayer.fantasy_team_id == to_team.fantasy_team_id,
            FantasyTeamPlayer.player_id == player_requested.id,
        )
        .first()
    )
    if fantasy_to_team_player:
        db.delete(fantasy_to_team_player)

    fantasy_from_team_player = (
        db.query(FantasyTeamPlayer)
        .filter(
            FantasyTeamPlayer.fantasy_team_id == from_team.fantasy_team_id,
            FantasyTeamPlayer.player_id == player_offered.id,
        )
        .first()
    )
    if fantasy_from_team_player:
        db.delete(fantasy_from_team_player)

    db.flush()

    to_team_player_in = LeagueTeamPlayer(
        league_team_id=to_team.id,
        player_id=player_offered.id,
        league_id=to_team.league_id,
        position_in_team=player_offered.position,
        added_for_matchday=matchday_number,
    )
    db.add(to_team_player_in)

    from_team_player_in = LeagueTeamPlayer(
        league_team_id=from_team.id,
        player_id=player_requested.id,
        league_id=from_team.league_id,
        position_in_team=player_requested.position,
        added_for_matchday=matchday_number,
    )
    db.add(from_team_player_in)

    fantasy_to_team_player_in = FantasyTeamPlayer(
        fantasy_team_id=to_team.fantasy_team_id,
        player_id=player_offered.id,
        position_in_team=player_offered.position,
        added_for_matchday=matchday_number,
    )
    db.add(fantasy_to_team_player_in)

    fantasy_from_team_player_in = FantasyTeamPlayer(
        fantasy_team_id=from_team.fantasy_team_id,
        player_id=player_requested.id,
        position_in_team=player_requested.position,
        added_for_matchday=matchday_number,
    )
    db.add(fantasy_from_team_player_in)

    buyer_history = TransferHistory(
        fantasy_team_id=from_team.fantasy_team_id,
        league_id=from_team.league_id,
        matchday_id=matchday_id,
        transfer_type="player_exchange",
        player_in_id=player_requested.id,
        player_out_id=player_offered.id,
        transfer_cost=0.0,
        seller_team_id=to_team.fantasy_team_id,
        transfer_offer_id=None,
        is_free_transfer=True,
    )
    seller_history = TransferHistory(
        fantasy_team_id=to_team.fantasy_team_id,
        league_id=to_team.league_id,
        matchday_id=matchday_id,
        transfer_type="player_exchange",
        player_in_id=player_offered.id,
        player_out_id=player_requested.id,
        transfer_cost=0.0,
        seller_team_id=from_team.fantasy_team_id,
        transfer_offer_id=None,
        is_free_transfer=True,
    )
    db.add(buyer_history)
    db.add(seller_history)
