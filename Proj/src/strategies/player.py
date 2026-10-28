from typing import Optional

from Proj.src.blackjack.game import Action
from Proj.src.blackjack.hand import Hand


class PlayerStrategy:
    """
    Stratégie interactive pilotée par l'utilisateur via la console.
    """

    def __call__(
        self,
        player_hand: Hand,
        dealer_upcard: tuple[str, Optional[str]],
        can_double: bool,
        can_split: bool,
    ) -> Action:
        while True:
            dealer_rank, dealer_suit = dealer_upcard
            dealer_card_display = f"{dealer_rank}{dealer_suit}"

            print()
            print("=== Ton tour ===")
            print(f"Ta main        : {player_hand.pretty_cards()} (valeur = {player_hand.value()})")
            print(f"Carte du dealer: {dealer_card_display}")

            allowed_actions = ["hit", "stand"]
            if can_double:
                allowed_actions.append("double")
            if can_split:
                allowed_actions.append("split")

            print(f"Actions possibles : {', '.join(allowed_actions)}")
            choice = input("Que veux-tu faire ? ").strip().lower()

            mapping = {
                "h": "hit",
                "hit": "hit",
                "s": "stand",
                "stand": "stand",
                "d": "double",
                "double": "double",
                "p": "split",
                "split": "split",
            }

            if choice not in mapping:
                print("Entrée invalide. Réessaie.")
                continue

            action = mapping[choice]

            if action == "double" and not can_double:
                print("Tu ne peux pas doubler maintenant.")
                continue

            if action == "split" and not can_split:
                print("Tu ne peux pas splitter maintenant.")
                continue

            return action