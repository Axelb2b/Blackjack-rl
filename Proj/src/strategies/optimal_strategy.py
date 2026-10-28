from typing import Optional

from Proj.src.blackjack.game import Action
from Proj.src.blackjack.hand import Hand


def dealer_value(rank: str) -> int:
    if rank in ["J", "Q", "K", "10"]:
        return 10
    if rank == "A":
        return 11
    return int(rank)


class OptimalStrategy:
    """
    Implémentation de la basic strategy (simplifiée).
    """

    def __call__(
        self,
        player_hand: Hand,
        dealer_upcard: tuple[str, Optional[str]],
        can_double: bool,
        can_split: bool,
    ) -> Action:

        dealer = dealer_value(dealer_upcard[0])

        # --- SPLIT ---
        if can_split:
            rank = player_hand.cards[0][0]

            if rank == "A" or rank == "8":
                return "split"

            if rank == "10":
                return "stand"

            if rank == "9":
                if dealer in [2,3,4,5,6,8,9]:
                    return "split"
                return "stand"

            if rank == "7":
                if dealer <= 7:
                    return "split"
                return "hit"

            if rank == "6":
                if dealer <= 6:
                    return "split"
                return "hit"

            if rank == "5":
                pass  # traité comme hard 10

            if rank == "4":
                if dealer in [5,6]:
                    return "split"
                return "hit"

            if rank == "3" or rank == "2":
                if dealer <= 7:
                    return "split"
                return "hit"

        # --- SOFT TOTAL ---
        if player_hand.is_soft():
            value = player_hand.value()

            if value >= 19:
                return "stand"

            if value == 18:
                if dealer in [3,4,5,6] and can_double:
                    return "double"
                if dealer in [2,7,8]:
                    return "stand"
                return "hit"

            if value == 17:
                if dealer in [3,4,5,6] and can_double:
                    return "double"
                return "hit"

            if value == 16 or value == 15:
                if dealer in [4,5,6] and can_double:
                    return "double"
                return "hit"

            if value == 14 or value == 13:
                if dealer in [5,6] and can_double:
                    return "double"
                return "hit"

        # --- HARD TOTAL ---
        value = player_hand.value()

        if value >= 17:
            return "stand"

        if value == 16:
            if dealer <= 6:
                return "stand"
            return "hit"

        if value == 15:
            if dealer <= 6:
                return "stand"
            return "hit"

        if value == 14 or value == 13:
            if dealer <= 6:
                return "stand"
            return "hit"

        if value == 12:
            if dealer in [4,5,6]:
                return "stand"
            return "hit"

        if value == 11:
            if can_double:
                return "double"
            return "hit"

        if value == 10:
            if dealer <= 9 and can_double:
                return "double"
            return "hit"

        if value == 9:
            if dealer in [3,4,5,6] and can_double:
                return "double"
            return "hit"

        return "hit"