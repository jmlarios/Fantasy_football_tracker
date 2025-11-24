from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from sqlalchemy.orm import Session

from .contracts import TransferExecutionResult, TransferValidationResult

CommandT = TypeVar("CommandT")


class TransferStrategy(ABC, Generic[CommandT]):
    """Contract implemented by all transfer strategies."""

    @abstractmethod
    def validate(self, db: Session, command: CommandT) -> TransferValidationResult:
        """Validate the command without mutating state."""

    @abstractmethod
    def execute(self, db: Session, command: CommandT) -> TransferExecutionResult:
        """Perform the transfer applying state changes."""
