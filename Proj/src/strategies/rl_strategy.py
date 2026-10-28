from Proj.src.rl.state import RLState


def dealer_upcard_value(card) -> int:
    rank = card[0]
    if rank == "A":
        return 11
    if rank in {"10", "J", "Q", "K"}:
        return 10
    return int(rank)


def pair_rank_value(player_hand) -> int | None:
    """
    Encode la paire si la main est splittable.
    """
    if not player_hand.can_split():
        return None

    rank = player_hand.cards[0][0]

    if rank == "A":
        return 11
    if rank in {"10", "J", "Q", "K"}:
        return 10
    return int(rank)


def continuation_policy(player_hand, dealer_upcard) -> str:
    """
    Politique fixe utilisée comme fallback si l'état n'a pas été vu.
    Elle est cohérente avec celle utilisée pendant l'entraînement.
    """
    total = player_hand.value()
    dealer = dealer_upcard_value(dealer_upcard)
    is_soft = player_hand.is_soft()

    if is_soft:
        if total >= 19:
            return "stand"
        if total == 18 and dealer in {2, 3, 4, 5, 6, 7, 8}:
            return "stand"
        return "hit"

    if total >= 17:
        return "stand"
    if total in {13, 14, 15, 16} and dealer in {2, 3, 4, 5, 6}:
        return "stand"
    if total == 12 and dealer in {4, 5, 6}:
        return "stand"
    return "hit"


class RLStrategy:
    """
    Stratégie inférée à partir du modèle RL Monte Carlo.

    Cette version :
    - gère hit / stand / double / split
    - reconstruit pair_rank pour distinguer les paires
    - utilise la Q-table quand l'état existe
    - utilise une politique fixe de secours sinon
    """

    def __init__(self, q_table):
        self.q_table = q_table

    def _extract_state(self, hand, dealer_upcard):
        return RLState(
            player_total=hand.value(),
            dealer_upcard=dealer_upcard_value(dealer_upcard),
            is_soft=hand.is_soft(),
            pair_rank=pair_rank_value(hand),
        ).as_tuple()

    def __call__(self, hand, dealer_upcard, can_double, can_split):
        state_key = self._extract_state(hand, dealer_upcard)

        actions = ["hit", "stand"]

        if can_double:
            actions.append("double")

        if can_split and hand.can_split():
            actions.append("split")

        # Etat jamais vu : fallback raisonnable
        if state_key not in self.q_table:
            fallback = continuation_policy(hand, dealer_upcard)

            if fallback in actions:
                return fallback
            return "stand"

        values = self.q_table[state_key]

        best_value = max(values[a] for a in actions)
        best_actions = [a for a in actions if values[a] == best_value]

        # tie-break simple et déterministe
        return best_actions[0]