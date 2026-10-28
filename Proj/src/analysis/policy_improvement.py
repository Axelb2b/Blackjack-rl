from dataclasses import dataclass

from Proj.src.analysis.ev_engine import best_action, evaluate_all_actions
from Proj.src.blackjack.rules import BlackjackRules
from Proj.src.blackjack.state import BlackjackState
from Proj.src.strategies.table_strategy import TableStrategy


@dataclass
class ImprovedStateDecision:
    state: BlackjackState
    best_action: str
    best_ev: float
    all_evs: object


def improve_hard_table(
    base_strategy,
    rules: BlackjackRules,
    states: list[BlackjackState],
    n_simulations: int = 20000,
    seed: int | None = None,
) -> tuple[dict[tuple[int, int], str], list[ImprovedStateDecision]]:
    """
    Pour chaque état hard :
    - calcule EV des actions
    - choisit la meilleure
    - construit une hard_table
    """
    improved_table: dict[tuple[int, int], str] = {}
    decisions: list[ImprovedStateDecision] = []

    for idx, state in enumerate(states):
        action_evs = evaluate_all_actions(
            state=state,
            n_simulations=n_simulations,
            rules=rules,
            strategy=base_strategy,
            seed=(seed + idx * 100000) if seed is not None else None,
        )

        action, ev = best_action(action_evs)

        # On ne veut ici que la clé hard (total, dealer_value)
        player_total = state.player_value()
        dealer_value = 11 if state.dealer_upcard_rank == "A" else int(state.dealer_upcard_rank)
        improved_table[(player_total, dealer_value)] = action

        decisions.append(
            ImprovedStateDecision(
                state=state,
                best_action=action,
                best_ev=ev,
                all_evs=action_evs,
            )
        )

    return improved_table, decisions


def pretty_print_hard_table(hard_table: dict[tuple[int, int], str]) -> None:
    dealer_cols = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    header = "Tot | " + " ".join(f"{col:>6}" for col in dealer_cols)
    print(header)
    print("-" * len(header))

    for total in range(5, 21):
        row = [f"{total:>3} |"]
        for dealer in dealer_cols:
            action = hard_table.get((total, dealer), "")
            row.append(f"{action:>6}")
        print(" ".join(row))