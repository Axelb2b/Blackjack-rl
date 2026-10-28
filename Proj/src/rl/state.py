from dataclasses import dataclass


@dataclass(frozen=True)
class RLState:
    player_total: int
    dealer_upcard: int
    is_soft: bool
    pair_rank: int | None

    def as_tuple(self) -> tuple[int, int, bool, int | None]:
        return (
            self.player_total,
            self.dealer_upcard,
            self.is_soft,
            self.pair_rank,
        )