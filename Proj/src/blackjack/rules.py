from dataclasses import dataclass


@dataclass(frozen=True)
class BlackjackRules:
    """
    Configuration des règles de blackjack.

    Ce fichier sert à centraliser toutes les variantes classiques,
    même si le moteur n'utilise pas encore chacune d'entre elles.
    """

    # Sabot
    num_decks: int = 6
    cut_card_penetration: float = 0.75

    # Dealer
    dealer_stands_soft_17: bool = True
    dealer_peeks_for_blackjack: bool = True  

    # Paiement blackjack
    blackjack_payout: float = 1.5  # 3:2

    # Double
    allow_double: bool = True
    double_on_any_two_cards: bool = True
    double_on_hard_9_10_11_only: bool = False
    allow_double_after_split: bool = True
    allow_double_after_split_aces: bool = True

    # Split
    allow_split: bool = True
    max_split_hands: int = 4          # total max de mains après splits inclus
    allow_resplit: bool = True
    allow_resplit_aces: bool = False

    # Jeu après split
    allow_hit_split_aces: bool = True
    split_aces_receive_one_card_only: bool = False

    # Surrender / assurance
    allow_surrender: bool = False
    surrender_type: str | None = None   # None, "late", "early"
    allow_insurance: bool = True

    # Variantes de paiement / règles spéciales
    lose_all_to_dealer_blackjack_after_split_or_double: bool = False