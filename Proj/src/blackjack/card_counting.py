from dataclasses import dataclass
from math import ceil
from typing import Dict

from Proj.src.blackjack.shoe import Card


@dataclass(frozen=True)
class CountingSystem:
    name: str
    rank_values: Dict[str, int]

    def card_value(self, card: Card) -> int:
        rank, _ = card
        return self.rank_values.get(rank, 0)


HI_LO = CountingSystem(
    name="Hi-Lo",
    rank_values={
        "2": 1,
        "3": 1,
        "4": 1,
        "5": 1,
        "6": 1,
        "7": 0,
        "8": 0,
        "9": 0,
        "10": -1,
        "J": -1,
        "Q": -1,
        "K": -1,
        "A": -1,
    },
)


KO = CountingSystem(
    name="KO",
    rank_values={
        "2": 1,
        "3": 1,
        "4": 1,
        "5": 1,
        "6": 1,
        "7": 1,
        "8": 0,
        "9": 0,
        "10": -1,
        "J": -1,
        "Q": -1,
        "K": -1,
        "A": -1,
    },
)


@dataclass
class CountState:
    running_count: int
    true_count: float
    decks_remaining: float
    system_name: str


def compute_running_count(seen_cards: list[Card], system: CountingSystem = HI_LO) -> int:
    return sum(system.card_value(card) for card in seen_cards)


def decks_remaining_from_cards(cards_remaining: int) -> float:
    """
    Nombre de decks restants estimé.
    On garde une borne basse pour éviter une division par zéro.
    """
    return max(cards_remaining / 52.0, 0.25)


def compute_true_count(running_count: int, decks_remaining: float) -> float:
    return running_count / decks_remaining


def compute_true_count_floor(running_count: int, decks_remaining: float) -> int:
    """
    Version arrondie 'casino style' simple.
    Ici on tronque vers 0 via int(...), ou on pourrait choisir floor/ceil.
    """
    return int(running_count / decks_remaining)


def count_state_from_seen_cards(
    seen_cards: list[Card],
    cards_remaining: int,
    system: CountingSystem = HI_LO,
) -> CountState:
    running_count = compute_running_count(seen_cards, system)
    decks_remaining = decks_remaining_from_cards(cards_remaining)
    true_count = compute_true_count(running_count, decks_remaining)

    return CountState(
        running_count=running_count,
        true_count=true_count,
        decks_remaining=decks_remaining,
        system_name=system.name,
    )