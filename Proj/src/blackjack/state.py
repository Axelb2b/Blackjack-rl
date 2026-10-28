from dataclasses import dataclass
from typing import Optional

from Proj.src.blackjack.hand import Hand


@dataclass(frozen=True)
class BlackjackState:
    player_ranks: tuple[str, ...]
    dealer_upcard_rank: str
    true_count: Optional[int] = None

    def to_hand(self) -> Hand:
        """
        Construit une main à partir des rangs.
        Les couleurs n'ont pas d'importance ici.
        """
        cards = [(rank, "♠") for rank in self.player_ranks]
        return Hand(cards)

    def player_value(self) -> int:
        return self.to_hand().value()

    def is_soft(self) -> bool:
        return self.to_hand().is_soft()

    def can_split(self) -> bool:
        return self.to_hand().can_split()

    def is_pair(self) -> bool:
        return self.can_split()

    def describe(self) -> str:
        tc = f", TC={self.true_count}" if self.true_count is not None else ""
        return f"Joueur={list(self.player_ranks)} vs Dealer={self.dealer_upcard_rank}{tc}"