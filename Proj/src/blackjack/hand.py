from typing import List, Optional, Tuple


Rank = str
Suit = Optional[str]
Card = Tuple[Rank, Suit]

CARD_VALUES = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 10,
    "Q": 10,
    "K": 10,
    "A": 11,
}


class Hand:
    """
    Main de blackjack contenant des cartes de type (rank, suit).
    """

    def __init__(self, cards: List[Card] | None = None) -> None:
        self.cards: List[Card] = cards[:] if cards else []

    def add_card(self, card: Card) -> None:
        self.cards.append(card)

    def ranks(self) -> List[Rank]:
        return [rank for rank, _ in self.cards]

    def hard_value(self) -> int:
        total = 0
        for rank, _ in self.cards:
            if rank == "A":
                total += 1
            else:
                total += CARD_VALUES[rank]
        return total

    def value(self) -> int:
        total = self.hard_value()
        aces = sum(1 for rank, _ in self.cards if rank == "A")

        while aces > 0 and total + 10 <= 21:
            total += 10
            aces -= 1

        return total

    def is_soft(self) -> bool:
        if "A" not in self.ranks():
            return False
        return self.value() != self.hard_value()

    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.value() == 21

    def is_bust(self) -> bool:
        return self.value() > 21

    def can_split(self) -> bool:
        return len(self.cards) == 2 and self.cards[0][0] == self.cards[1][0]

    def pretty_cards(self) -> str:
        return " ".join(f"{rank}{suit}" for rank, suit in self.cards)

    def __len__(self) -> int:
        return len(self.cards)

    def __repr__(self) -> str:
        return (
            f"Hand(cards={self.pretty_cards()}, value={self.value()}, "
            f"soft={self.is_soft()}, blackjack={self.is_blackjack()})"
        )