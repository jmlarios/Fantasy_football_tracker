from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Sequence

from sqlalchemy.orm import Session

from src.models import LeagueTeam, LeagueTeamPlayer, Matchday, Player, TransferOffer

from .transfers.contracts import FreeAgentTransferCommand, OfferAcceptanceContext
from .transfers.free_agent_strategy import (
    FreeAgentQueryService,
    FreeAgentTransferStrategy,
)
from .transfers.offer_strategies import (
    MoneyOfferStrategy,
    OfferStrategy,
    PlayerExchangeOfferStrategy,
)

logger = logging.getLogger(__name__)


class FreeAgentTransferService:
    """Facade around strategy-based free-agent transfers."""

    _strategy = FreeAgentTransferStrategy()

    @staticmethod
    def get_available_players(
        db: Session,
        league_id: int,
        position: Optional[str] = None,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> List[Dict]:
        return FreeAgentQueryService.get_available_players(
            db=db,
            league_id=league_id,
            position=position,
            search=search,
            min_price=min_price,
            max_price=max_price,
        )

    @staticmethod
    def check_player_availability(db: Session, league_id: int, player_id: int) -> Dict:
        return FreeAgentQueryService.check_player_availability(
            db=db,
            league_id=league_id,
            player_id=player_id,
        )

    @classmethod
    def validate_free_transfer(
        cls,
        db: Session,
        league_id: int,
        team_id: int,
        player_in_id: int,
        player_out_id: Optional[int] = None,
    ) -> Dict:
        command = FreeAgentTransferCommand(
            league_id=league_id,
            league_team_id=team_id,
            player_in_id=player_in_id,
            player_out_id=player_out_id,
        )
        return cls._strategy.validate(db, command).to_dict()

    @classmethod
    def execute_free_transfer(
        cls,
        db: Session,
        league_id: int,
        team_id: int,
        player_in_id: int,
        player_out_id: Optional[int],
        user_id: int,
    ) -> Dict:
        command = FreeAgentTransferCommand(
            league_id=league_id,
            league_team_id=team_id,
            player_in_id=player_in_id,
            player_out_id=player_out_id,
            user_id=user_id,
        )
        return cls._strategy.execute(db, command).to_dict()


class UserTransferService:
    """Facade that orchestrates offer flows using strategy implementations."""

    _offer_strategies: Sequence[OfferStrategy] = (
        MoneyOfferStrategy(),
        PlayerExchangeOfferStrategy(),
    )

    @staticmethod
    def create_offer(
        db: Session,
        league_id: int,
        from_team_id: int,
        to_team_id: int,
        player_id: int,
        offer_type: str,
        money_offered: float = 0.0,
        player_offered_id: Optional[int] = None,
        player_out_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Dict:
        try:
            from_team = (
                db.query(LeagueTeam)
                .filter(LeagueTeam.id == from_team_id, LeagueTeam.league_id == league_id)
                .first()
            )
            to_team = (
                db.query(LeagueTeam)
                .filter(LeagueTeam.id == to_team_id, LeagueTeam.league_id == league_id)
                .first()
            )

            if not from_team or not to_team:
                return {
                    "success": False,
                    "errors": ["One or both teams not found in this league"],
                }

            if user_id and from_team.fantasy_team.user_id != user_id:
                return {
                    "success": False,
                    "errors": ["You do not own the buying team"],
                }

            if from_team_id == to_team_id:
                return {
                    "success": False,
                    "errors": ["Cannot make offer to your own team"],
                }

            current_matchday = db.query(Matchday).filter(Matchday.is_active == True).first()  # noqa: E712
            if current_matchday and current_matchday.is_transfer_locked:
                return {
                    "success": False,
                    "errors": [f"Transfers locked until {current_matchday.end_date}"],
                }

            player = db.query(Player).filter(Player.id == player_id).first()
            if not player:
                return {"success": False, "errors": ["Player not found"]}

            player_owned = (
                db.query(LeagueTeamPlayer)
                .filter(
                    LeagueTeamPlayer.league_team_id == to_team_id,
                    LeagueTeamPlayer.player_id == player_id,
                )
                .first()
            )
            if not player_owned:
                return {
                    "success": False,
                    "errors": ["Player not owned by target team"],
                }

            if offer_type == "money":
                if money_offered <= 0:
                    return {
                        "success": False,
                        "errors": ["Money offer must be greater than 0"],
                    }
                if money_offered > from_team.remaining_budget:
                    return {
                        "success": False,
                        "errors": [
                            f"Insufficient budget. Have {from_team.remaining_budget:.2f}M, "
                            f"need {money_offered:.2f}M",
                        ],
                    }
                if not player_out_id:
                    return {
                        "success": False,
                        "errors": [
                            "Money offers require selecting a player to drop from your squad",
                        ],
                    }
                player_out_owned = (
                    db.query(LeagueTeamPlayer)
                    .filter(
                        LeagueTeamPlayer.league_team_id == from_team_id,
                        LeagueTeamPlayer.player_id == player_out_id,
                    )
                    .first()
                )
                if not player_out_owned:
                    return {
                        "success": False,
                        "errors": ["Player to drop is not in your squad"],
                    }

            elif offer_type == "player_exchange":
                if not player_offered_id:
                    return {
                        "success": False,
                        "errors": ["Player exchange requires a player to be offered"],
                    }
                offered_player_owned = (
                    db.query(LeagueTeamPlayer)
                    .filter(
                        LeagueTeamPlayer.league_team_id == from_team_id,
                        LeagueTeamPlayer.player_id == player_offered_id,
                    )
                    .first()
                )
                if not offered_player_owned:
                    return {
                        "success": False,
                        "errors": ["Offered player not in your team"],
                    }
            else:
                return {
                    "success": False,
                    "errors": ['Invalid offer type. Must be "money" or "player_exchange"'],
                }

            existing_offer = (
                db.query(TransferOffer)
                .filter(
                    TransferOffer.league_id == league_id,
                    TransferOffer.from_team_id == from_team_id,
                    TransferOffer.to_team_id == to_team_id,
                    TransferOffer.player_id == player_id,
                    TransferOffer.status == "pending",
                )
                .first()
            )
            if existing_offer:
                return {
                    "success": False,
                    "errors": ["You already have a pending offer for this player"],
                }

            next_matchday = (
                db.query(Matchday)
                .filter(Matchday.is_finished == False)
                .order_by(Matchday.start_date.asc())
                .first()
            )
            expires_at = (
                next_matchday.deadline
                if next_matchday
                else datetime.now(timezone.utc) + timedelta(days=7)
            )

            offer = TransferOffer(
                league_id=league_id,
                from_team_id=from_team_id,
                to_team_id=to_team_id,
                player_id=player_id,
                offer_type=offer_type,
                money_offered=money_offered if offer_type == "money" else 0.0,
                player_offered_id=player_offered_id if offer_type == "player_exchange" else None,
                player_out_id=player_out_id if offer_type == "money" else None,
                status="pending",
                budget_reserved=offer_type == "money",
                expires_at=expires_at,
            )

            db.add(offer)
            db.commit()
            db.refresh(offer)

            player_offered = None
            if player_offered_id:
                player_offered = db.query(Player).filter(Player.id == player_offered_id).first()

            return {
                "success": True,
                "message": f"Offer created for {player.name}",
                "offer": {
                    "id": offer.id,
                    "player_requested": {
                        "id": player.id,
                        "name": player.name,
                        "position": player.position,
                        "price": player.price,
                    },
                    "offer_type": offer_type,
                    "money_offered": money_offered if offer_type == "money" else None,
                    "player_offered": {
                        "id": player_offered.id,
                        "name": player_offered.name,
                        "position": player_offered.position,
                        "price": player_offered.price,
                    }
                    if player_offered
                    else None,
                    "expires_at": offer.expires_at.isoformat(),
                    "time_until_expiry": offer.time_until_expiry,
                },
            }

        except Exception as exc:  # noqa: BLE001
            db.rollback()
            logger.error("Error creating transfer offer: %s", exc)
            return {"success": False, "errors": [f"Failed to create offer: {exc}"]}

    @staticmethod
    def get_team_offers(
        db: Session,
        league_id: int,
        team_id: int,
        offer_direction: str = "received",
    ) -> List[Dict]:
        if offer_direction == "received":
            offers = (
                db.query(TransferOffer)
                .filter(
                    TransferOffer.league_id == league_id,
                    TransferOffer.to_team_id == team_id,
                    TransferOffer.status == "pending",
                )
                .all()
            )
        else:
            offers = (
                db.query(TransferOffer)
                .filter(
                    TransferOffer.league_id == league_id,
                    TransferOffer.from_team_id == team_id,
                    TransferOffer.status == "pending",
                )
                .all()
            )

        result: List[Dict] = []
        for offer in offers:
            player = db.query(Player).filter(Player.id == offer.player_id).first()
            player_offered = None
            if offer.player_offered_id:
                player_offered = db.query(Player).filter(Player.id == offer.player_offered_id).first()

            from_team = db.query(LeagueTeam).filter(LeagueTeam.id == offer.from_team_id).first()
            to_team = db.query(LeagueTeam).filter(LeagueTeam.id == offer.to_team_id).first()

            result.append(
                {
                    "id": offer.id,
                    "from_team": {
                        "id": from_team.id,
                        "name": from_team.team_name or from_team.fantasy_team.name,
                        "user_name": from_team.fantasy_team.user.name,
                    },
                    "to_team": {
                        "id": to_team.id,
                        "name": to_team.team_name or to_team.fantasy_team.name,
                        "user_name": to_team.fantasy_team.user.name,
                    },
                    "player_requested": {
                        "id": player.id,
                        "name": player.name,
                        "position": player.position,
                        "price": player.price,
                        "team": player.team,
                    },
                    "offer_type": offer.offer_type,
                    "money_offered": offer.money_offered if offer.offer_type == "money" else None,
                    "player_offered": {
                        "id": player_offered.id,
                        "name": player_offered.name,
                        "position": player_offered.position,
                        "price": player_offered.price,
                        "team": player_offered.team,
                    }
                    if player_offered
                    else None,
                    "status": offer.status,
                    "created_at": offer.created_at.isoformat(),
                    "expires_at": offer.expires_at.isoformat(),
                    "time_until_expiry": offer.time_until_expiry,
                    "is_expired": offer.is_expired,
                }
            )

        return result

    @staticmethod
    def accept_offer(
        db: Session,
        offer_id: int,
        league_id: int,
        user_id: Optional[int] = None,
    ) -> Dict:
        try:
            offer = (
                db.query(TransferOffer)
                .filter(
                    TransferOffer.id == offer_id,
                    TransferOffer.league_id == league_id,
                )
                .first()
            )
            if not offer:
                return {"success": False, "errors": ["Offer not found"]}

            to_team = db.query(LeagueTeam).filter(LeagueTeam.id == offer.to_team_id).first()
            if user_id and to_team.fantasy_team.user_id != user_id:
                return {"success": False, "errors": ["You do not own the selling team"]}

            if offer.status != "pending":
                return {"success": False, "errors": [f"Offer already {offer.status}"]}

            if offer.is_expired:
                offer.status = "expired"
                db.commit()
                return {"success": False, "errors": ["Offer has expired"]}

            strategy = UserTransferService._resolve_offer_strategy(offer)
            context = OfferAcceptanceContext(
                offer=offer,
                acting_user_id=user_id or to_team.fantasy_team.user_id,
            )
            execution = strategy.execute(db, context)

            if execution.success:
                offer.status = "accepted"
                offer.responded_at = datetime.now(timezone.utc)
                db.commit()

            return execution.to_dict()

        except Exception as exc:  # noqa: BLE001
            db.rollback()
            logger.error("Error accepting offer: %s", exc)
            return {"success": False, "errors": [f"Failed to accept offer: {exc}"]}

    @staticmethod
    def reject_offer(
        db: Session,
        offer_id: int,
        league_id: int,
        user_id: Optional[int] = None,
    ) -> Dict:
        try:
            offer = (
                db.query(TransferOffer)
                .filter(
                    TransferOffer.id == offer_id,
                    TransferOffer.league_id == league_id,
                )
                .first()
            )
            if not offer:
                return {"success": False, "errors": ["Offer not found"]}

            to_team = db.query(LeagueTeam).filter(LeagueTeam.id == offer.to_team_id).first()
            if user_id and to_team.fantasy_team.user_id != user_id:
                return {"success": False, "errors": ["You do not own the selling team"]}

            if offer.status != "pending":
                return {"success": False, "errors": [f"Offer already {offer.status}"]}

            offer.status = "rejected"
            offer.responded_at = datetime.now(timezone.utc)
            db.commit()

            return {"success": True, "message": "Offer rejected"}

        except Exception as exc:  # noqa: BLE001
            db.rollback()
            logger.error("Error rejecting offer: %s", exc)
            return {"success": False, "errors": [f"Failed to reject offer: {exc}"]}

    @staticmethod
    def cancel_offer(
        db: Session,
        offer_id: int,
        league_id: int,
        user_id: Optional[int] = None,
    ) -> Dict:
        try:
            offer = (
                db.query(TransferOffer)
                .filter(
                    TransferOffer.id == offer_id,
                    TransferOffer.league_id == league_id,
                )
                .first()
            )
            if not offer:
                return {"success": False, "errors": ["Offer not found"]}

            from_team = db.query(LeagueTeam).filter(LeagueTeam.id == offer.from_team_id).first()
            if user_id and from_team.fantasy_team.user_id != user_id:
                return {"success": False, "errors": ["You do not own the offering team"]}

            if offer.status != "pending":
                return {"success": False, "errors": [f"Offer already {offer.status}"]}

            offer.status = "cancelled"
            db.commit()

            return {"success": True, "message": "Offer cancelled"}

        except Exception as exc:  # noqa: BLE001
            db.rollback()
            logger.error("Error cancelling offer: %s", exc)
            return {"success": False, "errors": [f"Failed to cancel offer: {exc}"]}

    @classmethod
    def _resolve_offer_strategy(cls, offer: TransferOffer) -> OfferStrategy:
        for strategy in cls._offer_strategies:
            if strategy.supports(offer):
                return strategy
        raise ValueError(
            f"No strategy registered for offer type '{offer.offer_type}'"
        )
