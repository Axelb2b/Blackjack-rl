from typing import Optional

from Proj.src.blackjack.game import Action
from Proj.src.blackjack.hand import Hand


class NaiveStrategy:
    """
    Stratégie simple pour tester le moteur :
    - split jamais
    - double sur 11 si autorisé
    - sinon hit tant que la main est < 17
    - sinon stand
    """

    def __call__(
        self,
        player_hand: Hand,
        dealer_upcard: tuple[str, Optional[str]],
        can_double: bool,
        can_split: bool,
    ) -> Action:
        hand_value = player_hand.value()

        if can_double and hand_value == 11:
            return "double"

        if hand_value < 17:
            return "hit"

        return "stand"