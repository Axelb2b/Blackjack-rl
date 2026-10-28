import random
from typing import Optional

from Proj.src.blackjack.game import Action
from Proj.src.blackjack.hand import Hand


class RandomStrategy:
    def __init__(self, seed: Optional[int] = None) -> None:
        self.random = random.Random(seed)

    def __call__(
        self,
        player_hand: Hand,
        dealer_upcard: tuple[str, Optional[str]],
        can_double: bool,
        can_split: bool,
    ) -> Action:
        actions: list[Action] = ["hit", "stand"]
        if can_double:
            actions.append("double")
        if can_split:
            actions.append("split")
        return self.random.choice(actions)