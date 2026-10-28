from collections import defaultdict

from Proj.src.blackjack.game import BlackjackGame, PlayerHandState
from Proj.src.blackjack.rules import BlackjackRules
from Proj.src.blackjack.shoe import Shoe
from Proj.src.rl.state import RLState


# ============================================================
# Représentation d'état
# ============================================================

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

    Pourquoi ce champ est indispensable ?
    Parce que :
    - 8,8
    - A,A
    - 6,6
    - 10,10
    ont des décisions de split très différentes.

    Un simple bool is_pair ne suffit pas.
    """
    if not player_hand.can_split():
        return None

    rank = player_hand.cards[0][0]

    if rank == "A":
        return 11
    if rank in {"10", "J", "Q", "K"}:
        return 10
    return int(rank)


def extract_state(player_hand, dealer_upcard):
    """
    Etat initial appris :
    - total joueur
    - upcard dealer
    - main soft ou non
    - pair_rank si la main initiale est une paire, sinon None
    """
    return RLState(
        player_total=player_hand.value(),
        dealer_upcard=dealer_upcard_value(dealer_upcard),
        is_soft=player_hand.is_soft(),
        pair_rank=pair_rank_value(player_hand),
    ).as_tuple()


# ============================================================
# Agent Monte Carlo sur première action uniquement
# ============================================================

class MonteCarloInitialActionAgent:
    """
    Monte Carlo first-visit sur la PREMIERE décision uniquement.

    On apprend Q(s0, a0) :
    - s0 = état initial de la main
    - a0 = première action choisie
    - reward = payout final de la manche

    Avec split :
    - si a0 = split, reward = somme des payouts des sous-mains
    """

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
# Filtrage des actions initiales
# ============================================================

def filter_initial_actions(legal_actions: list[str]) -> list[str]:
    """
    Dans cette version :
    - on garde hit / stand / double / split
    - donc plus de filtrage spécial
    """
    return legal_actions[:]


# ============================================================
# Politique fixe de continuation
# ============================================================

def continuation_policy(player_hand, dealer_upcard) -> str:
    """
    Politique fixe utilisée APRES la première décision apprise.

    Elle sert à terminer la main de façon stable, pour éviter que
    l'agent apprenne les états intermédiaires au lieu d'évaluer
    la décision initiale.

    Règles retenues :

    Hard hands:
    - stand à partir de 17
    - stand sur 13-16 contre 2-6
    - stand sur 12 contre 4-6
    - sinon hit

    Soft hands:
    - stand à partir de 19
    - stand sur soft 18 contre 2-8
    - sinon hit

    IMPORTANT :
    - pas de double supplémentaire dans la continuation
    - pas de split supplémentaire dans la continuation
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


def play_hand_with_fixed_continuation(
    game: BlackjackGame,
    hand_state: PlayerHandState,
    dealer_hand,
) -> PlayerHandState:
    """
    Termine UNE main avec la continuation fixe.

    Utilisée :
    - après un hit initial
    - sur chaque sous-main après split

    On n'apprend rien ici.
    On déroule simplement une politique stable.
    """
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
    """
    Joue une manche complète en apprenant uniquement la première action.

    Cas possibles pour l'action initiale :
    - stand
    - double
    - hit
    - split

    Pour split :
    - on laisse le moteur créer deux sous-mains
    - on joue ensuite chacune avec la continuation fixe
    - la reward finale est le payout total du round splitté
    """
    player_hand, dealer_hand = game.deal_initial_hands()
    dealer_upcard = dealer_hand.cards[0]
    initial_hand_state = PlayerHandState(hand=player_hand)

    dealer_has_peek_blackjack = (
        game.dealer_may_peek(dealer_hand) and dealer_hand.is_blackjack()
    )

    # Si aucune décision joueur n'est prise, on n'update rien
    if dealer_has_peek_blackjack or player_hand.is_blackjack():
        result = game.resolve_hand(initial_hand_state, dealer_hand)
        return None, None, result.payout

    state_key = extract_state(player_hand, dealer_upcard)

    legal_actions = game.get_legal_actions(
        hand_state=initial_hand_state,
        current_total_hands=1,
    )
    legal_actions = filter_initial_actions(legal_actions)

    initial_action = agent.choose_action(state_key, legal_actions)

    # --------------------------------------------------------
    # Cas 1 : STAND
    # --------------------------------------------------------
    if initial_action == "stand":
        final_hand_states = [initial_hand_state]

    # --------------------------------------------------------
    # Cas 2 : DOUBLE
    # --------------------------------------------------------
    elif initial_action == "double":
        result_hands = game.apply_action(
            hand_state=initial_hand_state,
            action="double",
            current_total_hands=1,
        )
        final_hand_states = result_hands

    # --------------------------------------------------------
    # Cas 3 : HIT
    # --------------------------------------------------------
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

    # --------------------------------------------------------
    # Cas 4 : SPLIT
    # --------------------------------------------------------
    elif initial_action == "split":
        result_hands = game.apply_action(
            hand_state=initial_hand_state,
            action="split",
            current_total_hands=1,
        )

        # On termine ensuite chaque sous-main avec la continuation fixe.
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

    # Dealer joue si au moins une main n'est pas bust
    if any(not hs.hand.is_bust() for hs in final_hand_states):
        game.play_dealer_turn(dealer_hand)

    # Reward finale = somme des payouts de toutes les mains
    hand_results = [game.resolve_hand(hs, dealer_hand) for hs in final_hand_states]
    final_reward = sum(hr.payout for hr in hand_results)

    # Mise à jour Monte Carlo sur la première action uniquement
    agent.update_first_visit(state_key, initial_action, final_reward)

    return state_key, initial_action, final_reward


# ============================================================
# Debug / affichage
# ============================================================

def best_action_for_state(agent: MonteCarloInitialActionAgent, actions: list[str], state_key) -> str:
    values = agent.q_table[state_key]
    best_value = max(values[a] for a in actions)
    best_actions = [a for a in actions if values[a] == best_value]
    return best_actions[0]


def print_selected_q_values(agent: MonteCarloInitialActionAgent) -> None:
    interesting_states = [
        (16, 10, False, None),
        (12, 4, False, None),
        (11, 6, False, None),
        (10, 9, False, None),
        (9, 6, False, None),
        (18, 9, True, None),
        (18, 3, True, None),
        (17, 6, True, None),
        (16, 6, False, 8),   # 8,8 vs 6
        (12, 6, True, 11),   # A,A vs 6
        (18, 7, False, 9),   # 9,9 vs 7
        (20, 6, False, 10),  # 10,10 vs 6
    ]

    print()
    print("===== Quelques Q-values =====")
    for state_key in interesting_states:
        values = agent.q_table[state_key]

        actions = ["hit", "stand", "double"]
        if state_key[3] is not None:
            actions.append("split")

        best_action = best_action_for_state(agent, actions, state_key)
        split_text = f"{values['split']:.6f}" if "split" in actions else "N/A"

        print(
            f"{state_key} -> "
            f"hit={values['hit']:.6f}, "
            f"stand={values['stand']:.6f}, "
            f"double={values['double']:.6f}, "
            f"split={split_text}, "
            f"best={best_action}"
        )


def print_hard_policy(agent: MonteCarloInitialActionAgent, min_total: int = 5, max_total: int = 20) -> None:
    dealer_cols = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    print()
    print("===== Politique MC avec split (hard hands non pair) =====")
    header = "Tot | " + " ".join(f"{col:>6}" for col in dealer_cols)
    print(header)
    print("-" * len(header))

    for total in range(min_total, max_total + 1):
        row = [f"{total:>3} |"]
        for dealer in dealer_cols:
            state_key = (total, dealer, False, None)
            best_action = best_action_for_state(
                agent,
                ["hit", "stand", "double"],
                state_key,
            )
            row.append(f"{best_action:>6}")
        print(" ".join(row))


def print_soft_policy(agent: MonteCarloInitialActionAgent, min_total: int = 13, max_total: int = 20) -> None:
    dealer_cols = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    print()
    print("===== Politique MC avec split (soft hands non pair) =====")
    header = "Tot | " + " ".join(f"{col:>6}" for col in dealer_cols)
    print(header)
    print("-" * len(header))

    for total in range(min_total, max_total + 1):
        row = [f"{total:>3} |"]
        for dealer in dealer_cols:
            state_key = (total, dealer, True, None)
            best_action = best_action_for_state(
                agent,
                ["hit", "stand", "double"],
                state_key,
            )
            row.append(f"{best_action:>6}")
        print(" ".join(row))


def print_pair_policy(agent: MonteCarloInitialActionAgent) -> None:
    dealer_cols = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    pair_rows = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    print()
    print("===== Politique MC avec split (pairs) =====")
    header = "Pr | " + " ".join(f"{col:>6}" for col in dealer_cols)
    print(header)
    print("-" * len(header))

    for pair_rank in pair_rows:
        if pair_rank == 11:
            total = 12
            is_soft = True
        else:
            total = pair_rank * 2
            is_soft = False

        row = [f"{pair_rank:>2} |"]
        for dealer in dealer_cols:
            state_key = (total, dealer, is_soft, pair_rank)
            best_action = best_action_for_state(
                agent,
                ["hit", "stand", "double", "split"],
                state_key,
            )
            row.append(f"{best_action:>6}")
        print(" ".join(row))


# ============================================================
# Main
# ============================================================

def main():
    import pickle
    from pathlib import Path

    rules = BlackjackRules()

    agent = MonteCarloInitialActionAgent(
        epsilon=1.0,
        epsilon_min=0.05,
        epsilon_decay=0.999995,
        seed=42,
    )

    n_episodes = 1_000_000
    total_reward = 0.0

    for episode in range(1, n_episodes + 1):
        shoe = Shoe(rules, seed=42 + episode)
        game = BlackjackGame(rules, shoe)

        _, _, reward = play_one_episode_initial_mc(game, agent)
        total_reward += reward

        agent.decay_epsilon()

        if episode % 100000 == 0:
            print(
                f"Episode {episode} | "
                f"epsilon={agent.epsilon:.4f} | "
                f"avg={total_reward / episode:.6f}"
            )

    print("\n===== FIN =====")
    print(f"Episodes      : {n_episodes}")
    print(f"Epsilon final : {agent.epsilon:.6f}")
    print(f"EV moyen      : {total_reward / n_episodes:.6f}")

    print_selected_q_values(agent)
    print_hard_policy(agent)
    print_soft_policy(agent)
    print_pair_policy(agent)

    MODEL_PATH = Path("Proj/models/rl/rl_model.pkl")
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    serializable_q_table = {
        state_key: dict(action_values)
        for state_key, action_values in agent.q_table.items()
    }

    model_data = {
        "q_table": serializable_q_table,
        "episodes": n_episodes,
        "epsilon_final": agent.epsilon,
        "model_type": "mc_initial_action_with_split",
    }

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model_data, f)

    print(f"Modèle sauvegardé → {MODEL_PATH}")


if __name__ == "__main__":
    main()