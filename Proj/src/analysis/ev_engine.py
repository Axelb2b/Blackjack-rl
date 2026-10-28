from dataclasses import dataclass
from typing import Iterable

from Proj.src.blackjack.game import BlackjackGame, PlayerHandState
from Proj.src.blackjack.hand import Hand
from Proj.src.blackjack.rules import BlackjackRules
from Proj.src.blackjack.shoe import Shoe
from Proj.src.blackjack.state import BlackjackState


@dataclass
class ActionEVs:
    stand: float
    hit: float
    double: float | None
    split: float | None


def create_hand_from_cards(cards: list[tuple[str, str]]) -> Hand:
    return Hand(cards)


def remove_known_cards_from_shoe(shoe: Shoe, known_cards: Iterable[tuple[str, str]]) -> None:
    """
    Retire du sabot les cartes déjà visibles/imposées dans l'état.
    On retire une occurrence exacte de chaque carte.
    """
    cards_list = list(shoe.cards)

    for target_card in known_cards:
        try:
            cards_list.remove(target_card)
        except ValueError as exc:
            raise ValueError(
                f"Impossible de retirer la carte {target_card} du sabot. "
                "Vérifie que l'état imposé est cohérent avec le nombre de decks."
            ) from exc

    shoe.cards = cards_list


def choose_specific_cards_for_state(state: BlackjackState) -> tuple[list[tuple[str, str]], tuple[str, str]]:
    """
    Attribue des couleurs arbitraires mais cohérentes aux cartes imposées.
    Les couleurs n'ont pas d'effet sur le blackjack standard, mais il faut
    des cartes concrètes pour pouvoir les retirer du sabot.
    """
    used_cards: list[tuple[str, str]] = []
    default_suits = ["♠", "♥", "♦", "♣"]

    for i, rank in enumerate(state.player_ranks):
        used_cards.append((rank, default_suits[i % len(default_suits)]))

    dealer_upcard = (state.dealer_upcard_rank, "♣")

    if dealer_upcard in used_cards:
        for suit in default_suits:
            candidate = (state.dealer_upcard_rank, suit)
            if candidate not in used_cards:
                dealer_upcard = candidate
                break

    return used_cards, dealer_upcard


def setup_game_from_state(
    state: BlackjackState,
    rules: BlackjackRules,
    seed: int | None = None,
) -> tuple[BlackjackGame, Hand, Hand]:
    """
    Construit un sabot cohérent avec l'état :
    - retire les cartes connues du joueur
    - retire l'upcard du dealer
    - laisse le reste du sabot inchangé
    """
    shoe = Shoe(rules, seed=seed)
    game = BlackjackGame(rules, shoe)

    player_cards, dealer_upcard = choose_specific_cards_for_state(state)

    remove_known_cards_from_shoe(
        shoe,
        known_cards=[*player_cards, dealer_upcard],
    )

    player_hand = create_hand_from_cards(player_cards)
    dealer_hand = Hand([dealer_upcard])

    return game, player_hand, dealer_hand


def dealer_has_peek_blackjack(game: BlackjackGame, dealer_hand: Hand) -> bool:
    """
    Vérifie si le dealer a blackjack dans une situation où il a le droit de peek.
    """
    return game.dealer_may_peek(dealer_hand) and dealer_hand.is_blackjack()


def evaluate_stand(
    state: BlackjackState,
    n_simulations: int,
    rules: BlackjackRules,
    strategy,
    seed: int | None = None,
) -> float:
    total_payout = 0.0

    for i in range(n_simulations):
        game, player_hand, dealer_hand = setup_game_from_state(
            state,
            rules,
            seed=(seed + i) if seed is not None else None,
        )

        dealer_hand.add_card(game.shoe.draw())
        hand_state = PlayerHandState(hand=player_hand)

        if not dealer_has_peek_blackjack(game, dealer_hand):
            game.play_dealer_turn(dealer_hand)

        result = game.resolve_hand(hand_state, dealer_hand)
        total_payout += result.payout

    return total_payout / n_simulations


def evaluate_hit(
    state: BlackjackState,
    n_simulations: int,
    rules: BlackjackRules,
    strategy,
    seed: int | None = None,
) -> float:
    total_payout = 0.0

    for i in range(n_simulations):
        game, player_hand, dealer_hand = setup_game_from_state(
            state,
            rules,
            seed=(seed + i) if seed is not None else None,
        )

        dealer_hand.add_card(game.shoe.draw())
        hand_state = PlayerHandState(hand=player_hand)

        # Si le dealer peek et a blackjack, le joueur ne joue pas.
        if dealer_has_peek_blackjack(game, dealer_hand):
            result = game.resolve_hand(hand_state, dealer_hand)
            total_payout += result.payout
            continue

        # Action imposée : hit
        hand_state.hand.add_card(game.shoe.draw())

        if hand_state.hand.is_bust():
            result = game.resolve_hand(hand_state, dealer_hand)
            total_payout += result.payout
            continue

        final_states = game.play_single_hand(
            hand_state=hand_state,
            dealer_hand=dealer_hand,
            strategy=strategy,
            current_total_hands=1,
        )

        if any(not hs.hand.is_bust() for hs in final_states):
            game.play_dealer_turn(dealer_hand)

        for hs in final_states:
            result = game.resolve_hand(hs, dealer_hand)
            total_payout += result.payout

    return total_payout / n_simulations


def evaluate_double(
    state: BlackjackState,
    n_simulations: int,
    rules: BlackjackRules,
    strategy,
    seed: int | None = None,
) -> float | None:
    if len(state.player_ranks) != 2 or not rules.allow_double:
        return None

    total_payout = 0.0

    for i in range(n_simulations):
        game, player_hand, dealer_hand = setup_game_from_state(
            state,
            rules,
            seed=(seed + i) if seed is not None else None,
        )

        dealer_hand.add_card(game.shoe.draw())

        hand_state = PlayerHandState(
            hand=player_hand,
            final_bet=2.0,
            doubled=True,
        )

        # Si le dealer peek et a blackjack, le joueur ne joue pas.
        if dealer_has_peek_blackjack(game, dealer_hand):
            result = game.resolve_hand(hand_state, dealer_hand)
            total_payout += result.payout
            continue

        # Action imposée : double
        hand_state.hand.add_card(game.shoe.draw())

        if not hand_state.hand.is_bust():
            game.play_dealer_turn(dealer_hand)

        result = game.resolve_hand(hand_state, dealer_hand)
        total_payout += result.payout

    return total_payout / n_simulations


def evaluate_split(
    state: BlackjackState,
    n_simulations: int,
    rules: BlackjackRules,
    strategy,
    seed: int | None = None,
) -> float | None:
    if len(state.player_ranks) != 2:
        return None

    test_hand = Hand([(state.player_ranks[0], "♠"), (state.player_ranks[1], "♥")])
    if not test_hand.can_split() or not rules.allow_split:
        return None

    total_payout = 0.0

    for i in range(n_simulations):
        game, player_hand, dealer_hand = setup_game_from_state(
            state,
            rules,
            seed=(seed + i) if seed is not None else None,
        )

        dealer_hand.add_card(game.shoe.draw())
        initial_state = PlayerHandState(hand=player_hand)

        # Si le dealer peek et a blackjack, pas de split joué.
        if dealer_has_peek_blackjack(game, dealer_hand):
            result = game.resolve_hand(initial_state, dealer_hand)
            total_payout += result.payout
            continue

        split_states = game.split_hand(initial_state)

        finished_states = []
        hands_to_play = split_states[:]

        while hands_to_play:
            current = hands_to_play.pop(0)
            current_total_hands = len(finished_states) + len(hands_to_play) + 1

            result_states = game.play_single_hand(
                hand_state=current,
                dealer_hand=dealer_hand,
                strategy=strategy,
                current_total_hands=current_total_hands,
            )

            if len(result_states) == 2:
                hands_to_play = result_states + hands_to_play
            else:
                finished_states.extend(result_states)

        if any(not hs.hand.is_bust() for hs in finished_states):
            game.play_dealer_turn(dealer_hand)

        for hs in finished_states:
            result = game.resolve_hand(hs, dealer_hand)
            total_payout += result.payout

    return total_payout / n_simulations


def evaluate_all_actions(
    state: BlackjackState,
    n_simulations: int,
    rules: BlackjackRules,
    strategy,
    seed: int | None = None,
) -> ActionEVs:
    stand_ev = evaluate_stand(state, n_simulations, rules, strategy, seed)
    hit_ev = evaluate_hit(state, n_simulations, rules, strategy, seed)
    double_ev = evaluate_double(state, n_simulations, rules, strategy, seed)
    split_ev = evaluate_split(state, n_simulations, rules, strategy, seed)

    return ActionEVs(
        stand=stand_ev,
        hit=hit_ev,
        double=double_ev,
        split=split_ev,
    )


def best_action(action_evs: ActionEVs) -> tuple[str, float]:
    candidates = {
        "stand": action_evs.stand,
        "hit": action_evs.hit,
    }

    if action_evs.double is not None:
        candidates["double"] = action_evs.double

    if action_evs.split is not None:
        candidates["split"] = action_evs.split

    action = max(candidates, key=candidates.get)
    return action, candidates[action]