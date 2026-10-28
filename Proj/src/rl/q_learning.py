import random
from collections import defaultdict


class QLearningAgent:
    def __init__(
        self,
        alpha: float = 0.05,
        gamma: float = 1.0,
        epsilon: float = 1.0,
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.999995,
        seed: int | None = None,
    ) -> None:
        self.alpha = alpha
        self.gamma = gamma
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

    def get_q(self, state_key, action: str) -> float:
        return self.q_table[state_key][action]

    def choose_action(self, state_key, actions: list[str]) -> str:
        if self.random.random() < self.epsilon:
            return self.random.choice(actions)

        action_values = self.q_table[state_key]
        best_value = max(action_values[a] for a in actions)
        best_actions = [a for a in actions if action_values[a] == best_value]
        return self.random.choice(best_actions)

    def update(
        self,
        state_key,
        action: str,
        reward: float,
        next_state_key,
        next_actions: list[str],
        done: bool,
    ) -> None:
        current_q = self.q_table[state_key][action]

        if done or next_state_key is None or not next_actions:
            target = reward
        else:
            next_max_q = max(self.q_table[next_state_key][a] for a in next_actions)
            target = reward + self.gamma * next_max_q

        self.q_table[state_key][action] = current_q + self.alpha * (target - current_q)

    def decay_epsilon(self) -> None:
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def greedy_policy(self):
        policy = {}
        for state_key, action_values in self.q_table.items():
            policy[state_key] = max(action_values, key=action_values.get)
        return policy