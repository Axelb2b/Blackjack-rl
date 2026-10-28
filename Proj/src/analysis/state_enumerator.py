from Proj.src.blackjack.state import BlackjackState


DEALER_UPCARDS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "A"]


def hard_state_from_total(total: int, dealer_upcard_rank: str) -> BlackjackState:
    """
    Représentation canonique d'un hard total en 2 cartes si possible.
    Exemples :
    16 -> (10,6)
    12 -> (10,2)
    8  -> (4,4) mais attention ça crée une paire ; on évite ces petits totals en V1.
    """
    if total < 5 or total > 21:
        raise ValueError(f"Total hard invalide : {total}")

    # Représentation simple qui évite les As
    if total <= 11:
        first = "2"
        second = str(total - 2)
        if second == "10":
            second = "10"
        return BlackjackState(player_ranks=(first, second), dealer_upcard_rank=dealer_upcard_rank)

    # Pour 12 à 20, représentation canonique 10 + x
    if total <= 20:
        second_val = total - 10
        second = str(second_val)
        return BlackjackState(player_ranks=("10", second), dealer_upcard_rank=dealer_upcard_rank)

    # 21 hard n'est pas très utile ici, mais on le rend possible
    return BlackjackState(player_ranks=("10", "A"), dealer_upcard_rank=dealer_upcard_rank)


def enumerate_hard_states(min_total: int = 5, max_total: int = 20) -> list[BlackjackState]:
    states = []
    for total in range(min_total, max_total + 1):
        for dealer in DEALER_UPCARDS:
            states.append(hard_state_from_total(total, dealer))
    return states