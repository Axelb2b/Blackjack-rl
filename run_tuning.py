from dataclasses import dataclass, asdict
from pathlib import Path
import pickle
from collections import defaultdict

from Proj.src.blackjack.game import BlackjackGame, PlayerHandState
from Proj.src.blackjack.rules import BlackjackRules
from Proj.src.blackjack.shoe import Shoe
from Proj.src.rl.state import RLState
from Proj.src.analysis.simulation import simulate
from Proj.src.strategies.rl_strategy import RLStrategy


# ============================================================
# Etat RL baseline stable
# ============================================================

def dealer_upcard_value(card) -> int:
    rank = card[0]
    if rank == "A":
        return 11
    if rank in {"10", "J", "Q", "K"}:
        return 10
    return int(rank)


def pair_rank_value(player_hand) -> int | None:
    if not player_hand.can_split():
        return None

    rank = player_hand.cards[0][0]

    if rank == "A":
        return 11
    if rank in {"10", "J", "Q", "K"}:
        return 10
    return int(rank)


def extract_state(player_hand, dealer_upcard):
    return RLState(
        player_total=player_hand.value(),
        dealer_upcard=dealer_upcard_value(dealer_upcard),
        is_soft=player_hand.is_soft(),
        pair_rank=pair_rank_value(player_hand),
    ).as_tuple()


# ============================================================
# Agent Monte Carlo
# ============================================================

class MonteCarloInitialActionAgent:
    def __init__(
        self,
        epsilon: float = 1.0,
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.999995,
        seed: int | None = None,
    ) -> None:
        import random

        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.random = random.Random(seed)

        self.q_table = defaultdict(
            lambda: {
                "hit": 0.0,
                "stand": 0.0,
                "double": 0.0,
                "split": 0.0,
            }
        )

        self.returns_sum = defaultdict(float)
        self.returns_count = defaultdict(int)

    def choose_action(self, state_key, actions: list[str]) -> str:
        if self.random.random() < self.epsilon:
            return self.random.choice(actions)

        values = self.q_table[state_key]
        best_value = max(values[a] for a in actions)
        best_actions = [a for a in actions if values[a] == best_value]
        return self.random.choice(best_actions)

    def update_first_visit(self, state_key, action: str, reward: float) -> None:
        sa_key = (state_key, action)
        self.returns_sum[sa_key] += reward
        self.returns_count[sa_key] += 1
        self.q_table[state_key][action] = (
            self.returns_sum[sa_key] / self.returns_count[sa_key]
        )

    def decay_epsilon(self) -> None:
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)


# ============================================================
# Politique de continuation fixe
# ============================================================

def continuation_policy(player_hand, dealer_upcard) -> str:
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


def play_hand_with_fixed_continuation(
    game: BlackjackGame,
    hand_state: PlayerHandState,
    dealer_hand,
) -> PlayerHandState:
    dealer_upcard = dealer_hand.cards[0]

    while not hand_state.hand.is_bust():
        action = continuation_policy(hand_state.hand, dealer_upcard)

        if action == "stand":
            return hand_state

        result_hands = game.apply_action(
            hand_state=hand_state,
            action="hit",
            current_total_hands=1,
        )
        hand_state = result_hands[0]

    return hand_state


# ============================================================
# Episode Monte Carlo
# ============================================================

def play_one_episode_initial_mc(
    game: BlackjackGame,
    agent: MonteCarloInitialActionAgent,
):
    player_hand, dealer_hand = game.deal_initial_hands()
    dealer_upcard = dealer_hand.cards[0]
    initial_hand_state = PlayerHandState(hand=player_hand)

    dealer_has_peek_blackjack = (
        game.dealer_may_peek(dealer_hand) and dealer_hand.is_blackjack()
    )

    if dealer_has_peek_blackjack or player_hand.is_blackjack():
        result = game.resolve_hand(initial_hand_state, dealer_hand)
        return None, None, result.payout

    state_key = extract_state(player_hand, dealer_upcard)

    legal_actions = game.get_legal_actions(
        hand_state=initial_hand_state,
        current_total_hands=1,
    )

    initial_action = agent.choose_action(state_key, legal_actions)

    if initial_action == "stand":
        final_hand_states = [initial_hand_state]

    elif initial_action == "double":
        result_hands = game.apply_action(
            hand_state=initial_hand_state,
            action="double",
            current_total_hands=1,
        )
        final_hand_states = result_hands

    elif initial_action == "hit":
        result_hands = game.apply_action(
            hand_state=initial_hand_state,
            action="hit",
            current_total_hands=1,
        )
        hand_state = result_hands[0]

        if not hand_state.hand.is_bust():
            hand_state = play_hand_with_fixed_continuation(
                game=game,
                hand_state=hand_state,
                dealer_hand=dealer_hand,
            )

        final_hand_states = [hand_state]

    elif initial_action == "split":
        result_hands = game.apply_action(
            hand_state=initial_hand_state,
            action="split",
            current_total_hands=1,
        )

        final_hand_states = []
        for split_hand_state in result_hands:
            final_state = play_hand_with_fixed_continuation(
                game=game,
                hand_state=split_hand_state,
                dealer_hand=dealer_hand,
            )
            final_hand_states.append(final_state)

    else:
        raise ValueError(f"Action initiale non gérée : {initial_action}")

    if any(not hs.hand.is_bust() for hs in final_hand_states):
        game.play_dealer_turn(dealer_hand)

    hand_results = [game.resolve_hand(hs, dealer_hand) for hs in final_hand_states]
    final_reward = sum(hr.payout for hr in hand_results)

    agent.update_first_visit(state_key, initial_action, final_reward)

    return state_key, initial_action, final_reward


# ============================================================
# Configuration tuning
# ============================================================

@dataclass(frozen=True)
class TuneConfig:
    name: str
    n_episodes: int
    epsilon: float
    epsilon_min: float
    epsilon_decay: float
    train_seed: int = 42
    eval_rounds: int = 200_000
    eval_seed: int = 42


@dataclass
class TuneResult:
    name: str
    n_episodes: int
    epsilon: float
    epsilon_min: float
    epsilon_decay: float
    train_ev: float
    eval_ev_per_round: float
    eval_ev_per_hand: float
    total_payout: float
    doubled_hands: int
    split_rounds: int
    model_path: str


# ============================================================
# Utilitaires
# ============================================================

def serialize_q_table(q_table) -> dict:
    return {
        state_key: dict(action_values)
        for state_key, action_values in q_table.items()
    }


def save_model(q_table, cfg: TuneConfig, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / f"{cfg.name}.pkl"

    model_data = {
        "q_table": serialize_q_table(q_table),
        "episodes": cfg.n_episodes,
        "epsilon": cfg.epsilon,
        "epsilon_min": cfg.epsilon_min,
        "epsilon_decay": cfg.epsilon_decay,
        "model_type": "mc_initial_action_with_split_baseline",
    }

    with open(model_path, "wb") as f:
        pickle.dump(model_data, f)

    return model_path


def train_one_config(cfg: TuneConfig, rules: BlackjackRules):
    agent = MonteCarloInitialActionAgent(
        epsilon=cfg.epsilon,
        epsilon_min=cfg.epsilon_min,
        epsilon_decay=cfg.epsilon_decay,
        seed=cfg.train_seed,
    )

    total_reward = 0.0

    for episode in range(1, cfg.n_episodes + 1):
        shoe = Shoe(rules, seed=cfg.train_seed + episode)
        game = BlackjackGame(rules, shoe)

        _, _, reward = play_one_episode_initial_mc(game, agent)
        total_reward += reward
        agent.decay_epsilon()

    train_ev = total_reward / cfg.n_episodes
    return agent, train_ev


def evaluate_q_table(q_table, cfg: TuneConfig, rules: BlackjackRules):
    strategy = RLStrategy(q_table)
    stats = simulate(
        strategy=strategy,
        n_rounds=cfg.eval_rounds,
        rules=rules,
        seed=cfg.eval_seed,
    )
    return stats


def print_result_table(results: list[TuneResult]) -> None:
    print()
    print("===== Classement tuning =====")
    header = (
        f"{'name':<22} "
        f"{'episodes':>10} "
        f"{'eps_min':>8} "
        f"{'decay':>12} "
        f"{'train_ev':>12} "
        f"{'eval_round':>12} "
        f"{'eval_hand':>12}"
    )
    print(header)
    print("-" * len(header))

    for r in sorted(results, key=lambda x: x.eval_ev_per_round, reverse=True):
        print(
            f"{r.name:<22} "
            f"{r.n_episodes:>10} "
            f"{r.epsilon_min:>8.3f} "
            f"{r.epsilon_decay:>12.6f} "
            f"{r.train_ev:>12.6f} "
            f"{r.eval_ev_per_round:>12.6f} "
            f"{r.eval_ev_per_hand:>12.6f}"
        )


# ============================================================
# Main
# ============================================================

def main():
    rules = BlackjackRules()
    output_dir = Path("Proj/models/rl/tuning_baseline_split")

    # On tune localement autour de la meilleure zone trouvée :
    # epsilon = 1.0
    # epsilon_min autour de 0.01
    # epsilon_decay autour de 0.999997
    configs = [
        TuneConfig(
            name="epsmin_0005_decay_999996",
            n_episodes=1_000_000,
            epsilon=1.0,
            epsilon_min=0.005,
            epsilon_decay=0.999996,
        ),
        TuneConfig(
            name="epsmin_0005_decay_999997",
            n_episodes=1_000_000,
            epsilon=1.0,
            epsilon_min=0.005,
            epsilon_decay=0.999997,
        ),
        TuneConfig(
            name="epsmin_0005_decay_999998",
            n_episodes=1_000_000,
            epsilon=1.0,
            epsilon_min=0.005,
            epsilon_decay=0.999998,
        ),
        TuneConfig(
            name="epsmin_0010_decay_999996",
            n_episodes=1_000_000,
            epsilon=1.0,
            epsilon_min=0.010,
            epsilon_decay=0.999996,
        ),
        TuneConfig(
            name="epsmin_0010_decay_999997",
            n_episodes=1_000_000,
            epsilon=1.0,
            epsilon_min=0.010,
            epsilon_decay=0.999997,
        ),
        TuneConfig(
            name="epsmin_0010_decay_999998",
            n_episodes=1_000_000,
            epsilon=1.0,
            epsilon_min=0.010,
            epsilon_decay=0.999998,
        ),
        TuneConfig(
            name="epsmin_0020_decay_999996",
            n_episodes=1_000_000,
            epsilon=1.0,
            epsilon_min=0.020,
            epsilon_decay=0.999996,
        ),
        TuneConfig(
            name="epsmin_0020_decay_999997",
            n_episodes=1_000_000,
            epsilon=1.0,
            epsilon_min=0.020,
            epsilon_decay=0.999997,
        ),
        TuneConfig(
            name="epsmin_0020_decay_999998",
            n_episodes=1_000_000,
            epsilon=1.0,
            epsilon_min=0.020,
            epsilon_decay=0.999998,
        ),
    ]

    results: list[TuneResult] = []

    for cfg in configs:
        print()
        print(f"===== Training {cfg.name} =====")
        print(asdict(cfg))

        agent, train_ev = train_one_config(cfg, rules)
        model_path = save_model(agent.q_table, cfg, output_dir)
        stats = evaluate_q_table(serialize_q_table(agent.q_table), cfg, rules)

        result = TuneResult(
            name=cfg.name,
            n_episodes=cfg.n_episodes,
            epsilon=cfg.epsilon,
            epsilon_min=cfg.epsilon_min,
            epsilon_decay=cfg.epsilon_decay,
            train_ev=train_ev,
            eval_ev_per_round=stats.ev_per_round,
            eval_ev_per_hand=stats.ev_per_hand,
            total_payout=stats.total_payout,
            doubled_hands=stats.doubled_hands,
            split_rounds=stats.rounds_with_split,
            model_path=str(model_path),
        )
        results.append(result)

        print(
            f"Résultat {cfg.name} | "
            f"train_ev={train_ev:.6f} | "
            f"eval_ev_round={stats.ev_per_round:.6f} | "
            f"eval_ev_hand={stats.ev_per_hand:.6f} | "
            f"doubles={stats.doubled_hands} | "
            f"split_rounds={stats.rounds_with_split}"
        )

    print_result_table(results)

    best = max(results, key=lambda x: x.eval_ev_per_round)

    print()
    print("===== Meilleure config =====")
    print(f"name           : {best.name}")
    print(f"eval_ev_round  : {best.eval_ev_per_round:.6f}")
    print(f"eval_ev_hand   : {best.eval_ev_per_hand:.6f}")
    print(f"model_path     : {best.model_path}")


if __name__ == "__main__":
    main()