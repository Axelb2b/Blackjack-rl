from Proj.src.analysis.policy_improvement import improve_hard_table, pretty_print_hard_table
from Proj.src.blackjack.rules import BlackjackRules
from Proj.src.analysis.state_enumerator import enumerate_hard_states
from Proj.src.strategies.optimal_strategy import OptimalStrategy
from Proj.src.strategies.table_strategy import TableStrategy
from Proj.src.strategies.hybrid_strategy import HybridStrategy


def dealer_rank_to_value(rank: str) -> int:
    if rank == "A":
        return 11
    return int(rank)


def build_hard_table_from_optimal_strategy() -> dict[tuple[int, int], str]:
    """
    Construit une hard_table initiale en interrogeant l'OptimalStrategy actuelle
    sur tous les états hard.
    """
    strategy = OptimalStrategy()
    hard_table = {}

    states = enumerate_hard_states(min_total=5, max_total=20)

    for state in states:
        hand = state.to_hand()
        dealer_upcard = (state.dealer_upcard_rank, "♠")

        action = strategy(
            player_hand=hand,
            dealer_upcard=dealer_upcard,
            can_double=True,
            can_split=False,
        )

        dealer_value = dealer_rank_to_value(state.dealer_upcard_rank)
        hard_table[(state.player_value(), dealer_value)] = action

    return hard_table


def compare_hard_tables(
    old_table: dict[tuple[int, int], str],
    new_table: dict[tuple[int, int], str],
) -> list[tuple[tuple[int, int], str, str]]:
    changes = []

    all_keys = sorted(set(old_table.keys()) | set(new_table.keys()))
    for key in all_keys:
        old_action = old_table.get(key)
        new_action = new_table.get(key)

        if old_action != new_action:
            changes.append((key, old_action, new_action))

    return changes


def run_one_pass(
    pass_index: int,
    base_strategy,
    rules: BlackjackRules,
    n_simulations: int,
    seed: int,
):
    states = enumerate_hard_states(min_total=5, max_total=20)

    improved_table, decisions = improve_hard_table(
        base_strategy=base_strategy,
        rules=rules,
        states=states,
        n_simulations=n_simulations,
        seed=seed,
    )

    print()
    print(f"===== Hard table améliorée (passe {pass_index}) =====")
    pretty_print_hard_table(improved_table)

    return improved_table, decisions


def print_selected_decisions(decisions, interesting):
    print()
    print("===== Quelques décisions =====")
    for total, dealer_rank in interesting:
        matching = [
            d for d in decisions
            if d.state.player_value() == total and d.state.dealer_upcard_rank == dealer_rank
        ]
        if matching:
            d = matching[0]
            print(
                f"{d.state.describe()} -> {d.best_action} | "
                f"stand={d.all_evs.stand:.6f}, "
                f"hit={d.all_evs.hit:.6f}, "
                f"double={d.all_evs.double if d.all_evs.double is not None else None}"
            )


def main() -> None:
    rules = BlackjackRules()
    n_simulations = 10000
    seed = 42

    interesting_states = [
        (5, "2"),
        (12, "4"),
        (11, "6"),
        (10, "9"),
        (9, "3"),
        (16, "10"),
    ]

    # ----- Passe 0 : hard table issue de l'OptimalStrategy actuelle -----
    hard_table_pass_0 = build_hard_table_from_optimal_strategy()
    strategy_pass_0 = TableStrategy(hard_table=hard_table_pass_0)

    print()
    print("===== Hard table de départ (issue de OptimalStrategy) =====")
    pretty_print_hard_table(hard_table_pass_0)

    # ----- Passe 1 -----
    hard_table_pass_1, decisions_pass_1 = run_one_pass(
        pass_index=1,
        base_strategy=strategy_pass_0,
        rules=rules,
        n_simulations=n_simulations,
        seed=seed,
    )

    changes_0_to_1 = compare_hard_tables(hard_table_pass_0, hard_table_pass_1)

    print()
    print(f"===== Changements passe 0 -> passe 1 : {len(changes_0_to_1)} =====")
    for (player_total, dealer_value), old_action, new_action in changes_0_to_1:
        print(f"({player_total}, {dealer_value}) : {old_action} -> {new_action}")

    print_selected_decisions(decisions_pass_1, interesting_states)

    # ----- Passe 2 -----
    strategy_pass_1 = HybridStrategy(hard_table_pass_1)

    hard_table_pass_2, decisions_pass_2 = run_one_pass(
        pass_index=2,
        base_strategy=strategy_pass_1,
        rules=rules,
        n_simulations=n_simulations,
        seed=seed,
    )

    changes_1_to_2 = compare_hard_tables(hard_table_pass_1, hard_table_pass_2)

    print()
    print(f"===== Changements passe 1 -> passe 2 : {len(changes_1_to_2)} =====")
    for (player_total, dealer_value), old_action, new_action in changes_1_to_2:
        print(f"({player_total}, {dealer_value}) : {old_action} -> {new_action}")

    print_selected_decisions(decisions_pass_2, interesting_states)

    # ----- Passe 3 -----
    strategy_pass_2 = HybridStrategy(hard_table_pass_2)

    hard_table_pass_3, decisions_pass_3 = run_one_pass(
        pass_index=3,
        base_strategy=strategy_pass_2,
        rules=rules,
        n_simulations=n_simulations,
        seed=seed,
    )

    changes_2_to_3 = compare_hard_tables(hard_table_pass_2, hard_table_pass_3)

    print()
    print(f"===== Changements passe 2 -> passe 3 : {len(changes_2_to_3)} =====")
    for (player_total, dealer_value), old_action, new_action in changes_2_to_3:
        print(f"({player_total}, {dealer_value}) : {old_action} -> {new_action}")

    print_selected_decisions(decisions_pass_3, interesting_states)

    # ----- Bilan -----
    print()
    if len(changes_2_to_3) == 0:
        print("La hard table semble stable après 3 passes.")
    elif len(changes_2_to_3) <= 3:
        print("La hard table est presque stable après 3 passes.")
    else:
        print("La hard table change encore sensiblement : une passe 4 peut être utile.")


if __name__ == "__main__":
    main()