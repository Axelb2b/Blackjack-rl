from .optimal_strategy import OptimalStrategy


class HybridStrategy:
    def __init__(self, hard_table: dict[tuple[int, int], str]):
        self.hard_table = hard_table
        self.fallback = OptimalStrategy()

    def __call__(self, player_hand, dealer_upcard, can_double, can_split):
        # Pair
        if can_split and player_hand.can_split():
            return self.fallback(player_hand, dealer_upcard, can_double, can_split)

        # Soft
        if player_hand.is_soft():
            return self.fallback(player_hand, dealer_upcard, can_double, can_split)

        # Hard
        player_total = player_hand.value()
        dealer_value = self._dealer_value(dealer_upcard)

        action = self.hard_table.get((player_total, dealer_value))

        if action is None:
            return self.fallback(player_hand, dealer_upcard, can_double, can_split)

        if action == "double" and not can_double:
            return "hit"

        if action == "split":
            return self.fallback(player_hand, dealer_upcard, can_double, can_split)

        return action

    def _dealer_value(self, dealer_upcard):
        rank = dealer_upcard[0]
        if rank == "A":
            return 11
        return int(rank)