from dataclasses import dataclass
from typing import Callable, Literal, Optional

from Proj.src.blackjack.hand import Hand
from Proj.src.blackjack.rules import BlackjackRules
from Proj.src.blackjack.shoe import Shoe


Action = Literal["hit", "stand", "double", "split"]


@dataclass
class PlayerHandState:
    hand: Hand
    final_bet: float = 1.0
    doubled: bool = False
    is_split_hand: bool = False


@dataclass
class HandResult:
    player_hand: Hand
    dealer_hand: Hand
    outcome: str
    payout: float
    final_bet: float
    doubled: bool
    is_split_hand: bool


@dataclass
class RoundResult:
    hand_results: list[HandResult]
    dealer_hand: Hand
    total_payout: float
    cut_card_was_reached_this_round: bool
    reshuffled_after_round: bool


class BlackjackGame:
    """
    Moteur V4 :
    - hit
    - stand
    - double
    - split
    - dealer peek
    - limite de split
    - resplit si autorisé par les règles
    - pas encore de surrender
    - pas encore d'assurance jouée
    """

    def __init__(self, rules: BlackjackRules, shoe: Shoe) -> None:
        self.rules = rules
        self.shoe = shoe

    def deal_initial_hands(self) -> tuple[Hand, Hand]:
        player_hand = Hand()
        dealer_hand = Hand()

        player_hand.add_card(self.shoe.draw())
        dealer_hand.add_card(self.shoe.draw())
        player_hand.add_card(self.shoe.draw())
        dealer_hand.add_card(self.shoe.draw())

        return player_hand, dealer_hand

    def dealer_upcard(self, dealer_hand: Hand):
        return dealer_hand.cards[0]

    def dealer_upcard_value(self, dealer_hand: Hand) -> int:
        rank = dealer_hand.cards[0][0]
        if rank in {"10", "J", "Q", "K"}:
            return 10
        if rank == "A":
            return 11
        return int(rank)

    def dealer_may_peek(self, dealer_hand: Hand) -> bool:
        """
        En pratique, le dealer peek uniquement si sa carte visible est A ou 10-value.
        """
        if not self.rules.dealer_peeks_for_blackjack:
            return False

        upcard_value = self.dealer_upcard_value(dealer_hand)
        return upcard_value in {10, 11}

    def can_double(self, hand_state: PlayerHandState) -> bool:
        if not self.rules.allow_double:
            return False

        if len(hand_state.hand) != 2:
            return False

        if hand_state.is_split_hand and not self.rules.allow_double_after_split:
            return False

        return True

    def can_split(
        self,
        hand_state: PlayerHandState,
        current_total_hands: int,
    ) -> bool:
        """
        Conditions de split :
        - split activé dans rules.py
        - 2 cartes identiques en rang
        - ne pas dépasser max_split_hands (dans rules aussi)
        - si la main vient déjà d'un split :
            - resplit seulement si autorisé
            - resplit des As seulement si autorisé (paramètre de rules)
        """
        if not self.rules.allow_split:
            return False

        if len(hand_state.hand) != 2:
            return False

        if not hand_state.hand.can_split():
            return False

        if current_total_hands >= self.rules.max_split_hands:
            return False

        if hand_state.is_split_hand:
            if not self.rules.allow_resplit:
                return False

            if hand_state.hand.cards[0][0] == "A" and not self.rules.allow_resplit_aces:
                return False

        return True

    def get_legal_actions(
        self,
        hand_state: PlayerHandState,
        current_total_hands: int,
    ) -> list[Action]:
        actions: list[Action] = ["hit", "stand"]

        if self.can_double(hand_state):
            actions.append("double")

        if self.can_split(hand_state, current_total_hands):
            actions.append("split")

        return actions

    def split_hand(self, hand_state: PlayerHandState) -> list[PlayerHandState]:
        """
        Transforme une paire en deux mains distinctes.
        Chaque nouvelle main reçoit immédiatement une carte.
        """
        first_card = hand_state.hand.cards[0]
        second_card = hand_state.hand.cards[1]

        first_hand = Hand([first_card])
        second_hand = Hand([second_card])

        first_hand.add_card(self.shoe.draw())
        second_hand.add_card(self.shoe.draw())

        return [
            PlayerHandState(
                hand=first_hand,
                final_bet=hand_state.final_bet,
                doubled=False,
                is_split_hand=True,
            ),
            PlayerHandState(
                hand=second_hand,
                final_bet=hand_state.final_bet,
                doubled=False,
                is_split_hand=True,
            ),
        ]

    def apply_action(
        self,
        hand_state: PlayerHandState,
        action: Action,
        current_total_hands: int,
    ) -> list[PlayerHandState]:
        legal_actions = self.get_legal_actions(hand_state, current_total_hands)

        if action not in legal_actions:
            raise ValueError(
                f"Action illégale demandée: {action}. "
                f"Actions autorisées: {legal_actions}"
            )

        if action == "stand":
            return [hand_state]

        if action == "hit":
            hand_state.hand.add_card(self.shoe.draw())
            return [hand_state]

        if action == "double":
            hand_state.final_bet *= 2.0
            hand_state.doubled = True
            hand_state.hand.add_card(self.shoe.draw())
            return [hand_state]

        if action == "split":
            return self.split_hand(hand_state)

        raise ValueError(f"Action inconnue : {action}")

    def play_single_hand(
        self,
        hand_state: PlayerHandState,
        dealer_hand: Hand,
        strategy: Callable[[Hand, tuple[str, Optional[str]], bool, bool], Action],
        current_total_hands: int,
    ) -> list[PlayerHandState]:
        """
        Joue une main joueur.

        Peut retourner :
        - une liste de 1 main si pas de split
        - une liste de 2 mains si split
        """
        upcard = self.dealer_upcard(dealer_hand)

        while not hand_state.hand.is_bust():
            legal_actions = self.get_legal_actions(hand_state, current_total_hands)

            action = strategy(
                hand_state.hand,
                upcard,
                "double" in legal_actions,
                "split" in legal_actions,
            )

            result_hands = self.apply_action(
                hand_state=hand_state,
                action=action,
                current_total_hands=current_total_hands,
            )

            if action == "hit":
                hand_state = result_hands[0]
                continue

            return result_hands

        return [hand_state]

    def play_all_player_hands(
        self,
        initial_hand: Hand,
        dealer_hand: Hand,
        strategy: Callable[[Hand, tuple[str, Optional[str]], bool, bool], Action],
    ) -> list[PlayerHandState]:
        """
        Gère la ou les mains joueur dans l'ordre.
        Si une main est splittée, ses deux sous-mains sont jouées ensuite.
        """
        hands_to_play: list[PlayerHandState] = [PlayerHandState(hand=initial_hand)]
        finished_hands: list[PlayerHandState] = []

        while hands_to_play:
            current_hand = hands_to_play.pop(0)

            current_total_hands = len(finished_hands) + len(hands_to_play) + 1

            result_hands = self.play_single_hand(
                current_hand,
                dealer_hand,
                strategy,
                current_total_hands,
            )

            if len(result_hands) == 2:
                hands_to_play = result_hands + hands_to_play
            else:
                finished_hands.extend(result_hands)

        return finished_hands

    def play_dealer_turn(self, dealer_hand: Hand) -> Hand:
        while True:
            value = dealer_hand.value()

            if value < 17:
                dealer_hand.add_card(self.shoe.draw())
                continue

            if value > 17:
                break

            if dealer_hand.is_soft() and not self.rules.dealer_stands_soft_17:
                dealer_hand.add_card(self.shoe.draw())
                continue

            break

        return dealer_hand

    def resolve_hand(
        self,
        hand_state: PlayerHandState,
        dealer_hand: Hand,
    ) -> HandResult:
        player_hand = hand_state.hand

        player_has_natural_blackjack = (
            player_hand.is_blackjack() and not hand_state.is_split_hand
        )
        dealer_has_natural_blackjack = dealer_hand.is_blackjack()

        if player_has_natural_blackjack and dealer_has_natural_blackjack:
            return HandResult(
                player_hand,
                dealer_hand,
                "push",
                0.0,
                hand_state.final_bet,
                hand_state.doubled,
                hand_state.is_split_hand,
            )

        if player_has_natural_blackjack:
            return HandResult(
                player_hand,
                dealer_hand,
                "player_blackjack",
                self.rules.blackjack_payout,
                hand_state.final_bet,
                hand_state.doubled,
                hand_state.is_split_hand,
            )

        if dealer_has_natural_blackjack:
            return HandResult(
                player_hand,
                dealer_hand,
                "dealer_win",
                -hand_state.final_bet,
                hand_state.final_bet,
                hand_state.doubled,
                hand_state.is_split_hand,
            )

        if player_hand.is_bust():
            return HandResult(
                player_hand,
                dealer_hand,
                "dealer_win",
                -hand_state.final_bet,
                hand_state.final_bet,
                hand_state.doubled,
                hand_state.is_split_hand,
            )

        if dealer_hand.is_bust():
            return HandResult(
                player_hand,
                dealer_hand,
                "player_win",
                hand_state.final_bet,
                hand_state.final_bet,
                hand_state.doubled,
                hand_state.is_split_hand,
            )

        player_value = player_hand.value()
        dealer_value = dealer_hand.value()

        if player_value > dealer_value:
            return HandResult(
                player_hand,
                dealer_hand,
                "player_win",
                hand_state.final_bet,
                hand_state.final_bet,
                hand_state.doubled,
                hand_state.is_split_hand,
            )

        if player_value < dealer_value:
            return HandResult(
                player_hand,
                dealer_hand,
                "dealer_win",
                -hand_state.final_bet,
                hand_state.final_bet,
                hand_state.doubled,
                hand_state.is_split_hand,
            )

        return HandResult(
            player_hand,
            dealer_hand,
            "push",
            0.0,
            hand_state.final_bet,
            hand_state.doubled,
            hand_state.is_split_hand,
        )

    def play_round(
        self,
        strategy: Callable[[Hand, tuple[str, Optional[str]], bool, bool], Action],
    ) -> RoundResult:
        initial_player_hand, dealer_hand = self.deal_initial_hands()

        if self.dealer_may_peek(dealer_hand) and dealer_hand.is_blackjack():
            hand_states = [PlayerHandState(hand=initial_player_hand)]
        elif initial_player_hand.is_blackjack():
            hand_states = [PlayerHandState(hand=initial_player_hand)]
        else:
            hand_states = self.play_all_player_hands(initial_player_hand, dealer_hand, strategy)

            if any(not hs.hand.is_bust() for hs in hand_states):
                self.play_dealer_turn(dealer_hand)

        hand_results = [self.resolve_hand(hs, dealer_hand) for hs in hand_states]
        total_payout = sum(hr.payout for hr in hand_results)

        cut_card_was_reached_this_round = self.shoe.needs_reshuffle()
        reshuffled_after_round = False

        if cut_card_was_reached_this_round:
            self.shoe.reshuffle()
            reshuffled_after_round = True

        return RoundResult(
            hand_results=hand_results,
            dealer_hand=dealer_hand,
            total_payout=total_payout,
            cut_card_was_reached_this_round=cut_card_was_reached_this_round,
            reshuffled_after_round=reshuffled_after_round,
        )