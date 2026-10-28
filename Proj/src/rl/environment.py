from Proj.src.blackjack.game import BlackjackGame, PlayerHandState
from Proj.src.blackjack.hand import Hand
from Proj.src.blackjack.rules import BlackjackRules
from Proj.src.blackjack.shoe import Shoe
from Proj.src.rl.state import RLState


class BlackjackRLEnvironment:
    """
    Environnement RL minimal pour le blackjack.

    Version V1 :
    - actions autorisées : hit / stand
    - pas encore de double
    - pas encore de split
    - 1 épisode = 1 main
    - récompense finale = payout
    """

    def __init__(self, rules: BlackjackRules, seed: int | None = None) -> None:
        self.rules = rules
        self.base_seed = seed
        self.episode_index = 0

        self.game: BlackjackGame | None = None
        self.shoe: Shoe | None = None
        self.player_hand: Hand | None = None
        self.dealer_hand: Hand | None = None
        self.done: bool = False

    def _dealer_upcard_value(self) -> int:
        assert self.dealer_hand is not None
        rank = self.dealer_hand.cards[0][0]

        if rank == "A":
            return 11
        if rank in {"10", "J", "Q", "K"}:
            return 10
        return int(rank)

    def _build_state(self) -> RLState:
        assert self.player_hand is not None
        return RLState(
            player_total=self.player_hand.value(),
            dealer_upcard=self._dealer_upcard_value(),
            is_soft=self.player_hand.is_soft(),
        )

    def _seed_for_episode(self) -> int | None:
        if self.base_seed is None:
            return None
        return self.base_seed + self.episode_index

    def reset(self) -> tuple[RLState | None, bool, float]:
        """
        Réinitialise une main.

        Retourne :
        - state : état initial, ou None si la main est déjà terminale
        - done : True si blackjack immédiat
        - reward : payout terminal si done, sinon 0.0
        """
        self.episode_index += 1

        self.shoe = Shoe(self.rules, seed=self._seed_for_episode())
        self.game = BlackjackGame(self.rules, self.shoe)

        self.player_hand, self.dealer_hand = self.game.deal_initial_hands()
        self.done = False

        initial_state = PlayerHandState(hand=self.player_hand)

        dealer_has_peek_blackjack = (
            self.game.dealer_may_peek(self.dealer_hand)
            and self.dealer_hand.is_blackjack()
        )

        if dealer_has_peek_blackjack or self.player_hand.is_blackjack():
            self.done = True
            result = self.game.resolve_hand(initial_state, self.dealer_hand)
            return None, True, result.payout

        return self._build_state(), False, 0.0

    def available_actions(self) -> list[str]:
        if self.done:
            return []
        return ["hit", "stand"]

    def step(self, action: str) -> tuple[RLState | None, float, bool]:
        """
        Exécute une action.

        Retourne :
        - next_state : état suivant, ou None si terminal
        - reward : 0.0 si non terminal, payout final sinon
        - done : fin de main ou non
        """
        if self.done:
            raise RuntimeError("L'épisode est déjà terminé. Appelle reset().")

        assert self.game is not None
        assert self.player_hand is not None
        assert self.dealer_hand is not None

        hand_state = PlayerHandState(hand=self.player_hand)

        if action == "hit":
            self.player_hand.add_card(self.shoe.draw())  # type: ignore[arg-type]

            if self.player_hand.is_bust():
                self.done = True
                result = self.game.resolve_hand(hand_state, self.dealer_hand)
                return None, result.payout, True

            return self._build_state(), 0.0, False

        if action == "stand":
            if not self.dealer_hand.is_blackjack():
                self.game.play_dealer_turn(self.dealer_hand)

            self.done = True
            result = self.game.resolve_hand(hand_state, self.dealer_hand)
            return None, result.payout, True

        raise ValueError(f"Action inconnue : {action}")