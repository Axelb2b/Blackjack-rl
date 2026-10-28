import random
from collections import Counter
from typing import List, Optional, Tuple

from Proj.src.blackjack.rules import BlackjackRules


Rank = str
Suit = Optional[str]
Card = Tuple[Rank, Suit]

RANKS: List[Rank] = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
SUITS: List[str] = ["♠", "♥", "♦", "♣"]

CUT_CARD: Card = ("__CUT_CARD__", None)


class Shoe:
    """
    Sabot de blackjack avec cut card physique insérée à une profondeur réaliste.

    Une carte normale est représentée par :
        (rank, suit)
    Exemples :
        ("A", "♠")
        ("10", "♥")

    La cut card est représentée par :
        ("__CUT_CARD__", None)
    """

    def __init__(self, rules: BlackjackRules, seed: Optional[int] = None) -> None:
        self.rules = rules
        self.random = random.Random(seed)

        # Nombre de cartes normales dans le sabot
        self.initial_size = 52 * self.rules.num_decks

        self.cards: List[Card] = []
        self.cut_card_reached: bool = False

        self._build_and_shuffle()

    def _build_and_shuffle(self) -> None:
        """
        Reconstruit le sabot :
        - crée les cartes normales exactes
        - les mélange
        - insère la cut card à la profondeur définie par cut_card_penetration
        """
        normal_cards: List[Card] = []

        for _ in range(self.rules.num_decks):
            for suit in SUITS:
                for rank in RANKS:
                    normal_cards.append((rank, suit))

        self.random.shuffle(normal_cards)

        # Nombre de cartes normales consommées avant la cut card
        cards_before_cut = int(self.initial_size * self.rules.cut_card_penetration)

        # Sécurités de bornes
        cards_before_cut = max(0, min(cards_before_cut, self.initial_size))

        # La pioche se fait avec pop() à la fin de la liste.
        # Donc si on veut que la cut card sorte après "cards_before_cut" vraies cartes,
        # on l'insère à l'index :
        cut_index = self.initial_size - cards_before_cut

        self.cards = normal_cards[:]
        self.cards.insert(cut_index, CUT_CARD)

        self.cut_card_reached = False

    def draw(self) -> Card:
        """
        Pioche une vraie carte de jeu.

        Si la cut card est tirée :
        - on active le flag cut_card_reached
        - on continue immédiatement à piocher jusqu'à obtenir une vraie carte

        Si, pour une raison exceptionnelle, il n'y a plus rien après la cut card,
        on remélange pour éviter de casser la simulation.
        """
        while True:
            if not self.cards:
                raise RuntimeError("Le sabot est vide. Il faut reshuffle avant de continuer.")

            card = self.cards.pop()

            if card == CUT_CARD:
                self.cut_card_reached = True

                if not self.cards:
                    self.reshuffle()

                continue

            return card

    def needs_reshuffle(self) -> bool:
        """
        À vérifier après la fin d'une main.
        """
        return self.cut_card_reached

    def reshuffle(self) -> None:
        self._build_and_shuffle()

    def cards_remaining(self) -> int:
        return len(self.cards)

    def has_cut_card_remaining(self) -> bool:
        return CUT_CARD in self.cards

    def rank_frequencies(self) -> Counter:
        return Counter(rank for rank, suit in self.cards if rank != CUT_CARD[0])

    def suit_frequencies(self) -> Counter:
        return Counter(suit for rank, suit in self.cards if suit is not None)

    def card_frequencies(self) -> Counter:
        return Counter(card for card in self.cards if card != CUT_CARD)

    def cards_before_cut_remaining(self) -> int:
        """
        Nombre de cartes restantes à tirer avant d'atteindre la cut card.
        Utile pour debug.
        """
        if CUT_CARD not in self.cards:
            return 0

        cut_index = self.cards.index(CUT_CARD)
        return len(self.cards) - 1 - cut_index

    def __repr__(self) -> str:
        return (
            f"Shoe(remaining={self.cards_remaining()}, "
            f"cut_reached={self.cut_card_reached}, "
            f"cut_remaining={self.has_cut_card_remaining()}, "
            f"cards_before_cut_remaining={self.cards_before_cut_remaining()})"
        )