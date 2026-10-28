from typing import Optional

from Proj.src.blackjack.game import Action
from Proj.src.blackjack.hand import Hand


def dealer_rank_to_value(rank: str) -> int:
    if rank in {"10", "J", "Q", "K"}:
        return 10
    if rank == "A":
        return 11
    return int(rank)


class TableStrategy:
    """
    Stratégie basée sur des tables.

    Convention :
    - hard_table[(player_total, dealer_value)] = "hit" / "stand" / "double"
    - soft_table[(player_total, dealer_value)] = ...
    - pair_table[(pair_rank, dealer_value)] = ...
    """

    def __init__(
        self,
        hard_table: dict[tuple[int, int], Action] | None = None,
        soft_table: dict[tuple[int, int], Action] | None = None,
        pair_table: dict[tuple[str, int], Action] | None = None,
        fallback_action: Action = "hit",
    ) -> None:
        self.hard_table = hard_table or {}
        self.soft_table = soft_table or {}
        self.pair_table = pair_table or {}
        self.fallback_action = fallback_action

    def __call__(
        self,
        player_hand: Hand,
        dealer_upcard: tuple[str, Optional[str]],
        can_double: bool,
        can_split: bool,
    ) -> Action:
        dealer_value = dealer_rank_to_value(dealer_upcard[0])

        # Pair table d'abord
        if can_split and player_hand.can_split():
            pair_rank = player_hand.cards[0][0]
            action = self.pair_table.get((pair_rank, dealer_value))
            if action is not None:
                if action == "split":
                    return "split"
                if action == "double" and can_double:
                    return "double"
                if action in {"hit", "stand"}:
                    return action

        # Soft table
        if player_hand.is_soft():
            total = player_hand.value()
            action = self.soft_table.get((total, dealer_value))
            if action is not None:
                if action == "double" and not can_double:
                    return "hit"
                return action

        # Hard table
        total = player_hand.value()
        action = self.hard_table.get((total, dealer_value))
        if action is not None:
            if action == "double" and not can_double:
                return "hit"
            return action

        return self.fallback_action