from Proj.src.blackjack.rules import BlackjackRules
from Proj.src.analysis.simulation import SimulationStats, simulate
from Proj.src.strategies.basic_strategy import NaiveStrategy
from Proj.src.strategies.optimal_strategy import OptimalStrategy
from Proj.src.strategies.random_strategy import RandomStrategy
from Proj.src.strategies.rl_strategy import RLStrategy
import pickle

from pathlib import Path

MODEL_PATH = Path("Proj/models/rl/tuning_baseline_split/epsmin_0005_decay_999996.pkl")


def pct(x: float) -> str:
    return f"{100 * x:.2f}%"


def print_stats(stats: SimulationStats) -> None:
    print()
    print(f"===== {stats.strategy_name} =====")
    print("Manches simulées        :", stats.n_rounds)
    print("Mains jouées            :", stats.total_hands_played)
    print("Payout total            :", round(stats.total_payout, 4))
    print("EV par manche           :", round(stats.ev_per_round, 6))
    print("EV par main             :", round(stats.ev_per_hand, 6))
    print()
    print("Wins                    :", stats.player_wins, f"({pct(stats.win_rate)})")
    print("Loses                   :", stats.dealer_wins, f"({pct(stats.lose_rate)})")
    print("Pushes                  :", stats.pushes, f"({pct(stats.push_rate)})")
    print("Blackjacks              :", stats.blackjacks, f"({pct(stats.blackjack_rate)})")
    print()
    print("Mains doublées          :", stats.doubled_hands, f"({pct(stats.double_rate)})")
    print("Mains issues d'un split :", stats.split_hands, f"({pct(stats.split_hand_rate)})")
    print("Manches avec split      :", stats.rounds_with_split, f"({pct(stats.split_round_rate)})")


def main() -> None:
    #Chargement agent rl
    with open(MODEL_PATH, "rb") as f:
        model_data = pickle.load(f)
    q_table = model_data["q_table"]
    rl_strategy = RLStrategy(q_table)

    rules = BlackjackRules()

    n_rounds = 1_000_000

    strategies = [
        NaiveStrategy(),
        RandomStrategy(seed=42),
        OptimalStrategy(),
        rl_strategy,
    ]

    for strategy in strategies:
        stats = simulate(
            strategy=strategy,
            n_rounds=n_rounds,
            rules=rules,
            seed=42,
        )
        print_stats(stats)


if __name__ == "__main__":
    main()