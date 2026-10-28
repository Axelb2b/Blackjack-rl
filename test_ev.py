from Proj.src.analysis.ev_engine import best_action, evaluate_all_actions
from Proj.src.blackjack.rules import BlackjackRules
from Proj.src.blackjack.state import BlackjackState
from Proj.src.strategies.optimal_strategy import OptimalStrategy


def print_action_evs(state: BlackjackState, action_evs) -> None:
    print()
    print(state.describe())
    print(f"EV(stand)  = {action_evs.stand:.6f}")
    print(f"EV(hit)    = {action_evs.hit:.6f}")

    if action_evs.double is not None:
        print(f"EV(double) = {action_evs.double:.6f}")

    if action_evs.split is not None:
        print(f"EV(split)  = {action_evs.split:.6f}")

    action, ev = best_action(action_evs)
    print(f"=> meilleure action : {action} ({ev:.6f})")


def main() -> None:
    rules = BlackjackRules()
    strategy = OptimalStrategy()
    n = 100000

    states = [
        BlackjackState(player_ranks=("10", "6"), dealer_upcard_rank="10"),
        BlackjackState(player_ranks=("10", "2"), dealer_upcard_rank="4"),
        BlackjackState(player_ranks=("5", "6"), dealer_upcard_rank="6"),
        BlackjackState(player_ranks=("8", "8"), dealer_upcard_rank="6"),
        BlackjackState(player_ranks=("A", "7"), dealer_upcard_rank="9"),
    ]

    for state in states:
        action_evs = evaluate_all_actions(
            state=state,
            n_simulations=n,
            rules=rules,
            strategy=strategy,
            seed=42,
        )
        print_action_evs(state, action_evs)


if __name__ == "__main__":
    main()