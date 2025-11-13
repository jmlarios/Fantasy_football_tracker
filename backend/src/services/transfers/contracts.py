from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from src.models import TransferOffer


class TransferKind(str, Enum):
    """Supported high-level transfer operations."""

    FREE_AGENT = "free_agent"
    MONEY_OFFER = "money_offer"
    PLAYER_EXCHANGE = "player_exchange"


@dataclass(frozen=True)
class FreeAgentTransferCommand:
    """Command payload required to process a free-agent transfer."""

    league_id: int
    league_team_id: int
    player_in_id: int
    user_id: Optional[int] = None
    player_out_id: Optional[int] = None


@dataclass(frozen=True)
class OfferAcceptanceCommand:
    """Command payload for accepting a transfer offer between teams."""

    offer_id: int
    acting_user_id: int


@dataclass(frozen=True)
class OfferAcceptanceContext:
    """Context passed to offer strategies after the offer is loaded."""

    offer: "TransferOffer"
    acting_user_id: int


@dataclass(frozen=True)
class OfferCreationCommand:
    """Command payload for creating an offer between two league teams."""

    league_id: int
    from_team_id: int
    to_team_id: int
    player_id: int
    offer_type: str
    created_by_user_id: int
    money_offered: float = 0.0
    player_offered_id: Optional[int] = None
    player_out_id: Optional[int] = None


@dataclass(frozen=True)
class OfferCancellationCommand:
    """Command payload for cancelling an existing offer by its creator."""

    offer_id: int
    acting_user_id: int


@dataclass(frozen=True)
class OfferRejectionCommand:
    """Command payload for rejecting an existing offer by the receiver."""

    offer_id: int
    acting_user_id: int


@dataclass
class TransferValidationResult:
    """Represents the outcome of transfer validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    cost_breakdown: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Return a serialisable representation used by legacy endpoints."""

        return {
            "is_valid": self.is_valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "cost_breakdown": dict(self.cost_breakdown),
        }


@dataclass
class TransferExecutionResult:
    """Represents the outcome of executing a transfer."""

    success: bool
    message: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a serialisable representation used by legacy endpoints."""

        payload: Dict[str, Any] = {
            "success": self.success,
            "message": self.message,
            "errors": list(self.errors),
        }
        if self.data:
            payload["transfer"] = self.data
        return payload
