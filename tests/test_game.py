"""Regression tests added for the portfolio publication.

These are intentionally limited to implemented behaviour: they do not certify
that every real-world blackjack rules variant is handled by the simulator.
"""

import pytest

from Proj.src.blackjack.game import BlackjackGame, PlayerHandState
from Proj.src.blackjack.hand import Hand
from Proj.src.blackjack.rules import BlackjackRules
from Proj.src.blackjack.shoe import Shoe
from Proj.src.analysis.simulation import simulate
from Proj.src.strategies.basic_strategy import NaiveStrategy


def hand(*ranks):
    return Hand([(rank, suit) for rank, suit in zip(ranks, ('♠', '♥', '♦', '♣'))])


def game(**kwargs):
    rules = BlackjackRules(**kwargs)
    return BlackjackGame(rules, Shoe(rules, seed=42))


def test_aces_are_valued_correctly():
    assert hand('A', '9').value() == 20
    assert hand('A', 'A', '9').value() == 21
    assert hand('A', 'A', '9', 'K').value() == 21
    assert hand('A', 'A', '9', 'K').is_soft() is False
    assert hand('A', '9').is_soft() is True


def test_natural_blackjack_gets_three_to_two_payout():
    g = game()
    result = g.resolve_hand(PlayerHandState(hand('A', 'K')), hand('10', '8'))
    assert result.outcome == 'player_blackjack'
    assert result.payout == pytest.approx(1.5)


def test_two_natural_blackjacks_push():
    g = game()
    result = g.resolve_hand(PlayerHandState(hand('A', 'K')), hand('A', 'J'))
    assert result.outcome == 'push'
    assert result.payout == 0


def test_split_hand_21_is_not_natural_blackjack():
    g = game()
    state = PlayerHandState(hand('A', 'K'), is_split_hand=True)
    result = g.resolve_hand(state, hand('10', '9'))
    assert result.outcome == 'player_win'
    assert result.payout == 1


def test_double_changes_stake():
    g = game()
    state = PlayerHandState(hand('5', '6'))
    results = g.apply_action(state, 'double', current_total_hands=1)
    assert len(results) == 1
    assert results[0].doubled is True
    assert results[0].final_bet == 2
    assert len(results[0].hand) == 3


def test_split_creates_two_hands():
    g = game()
    state = PlayerHandState(hand('8', '8'))
    result = g.apply_action(state, 'split', current_total_hands=1)
    assert len(result) == 2
    assert all(len(s.hand) == 2 and s.is_split_hand for s in result)


def test_shoe_has_correct_number_of_cards_and_is_seeded():
    a = Shoe(BlackjackRules(), seed=42)
    b = Shoe(BlackjackRules(), seed=42)
    assert a.initial_size == 312
    assert [a.draw() for _ in range(10)] == [b.draw() for _ in range(10)]


def test_simulation_is_reproducible_with_fixed_seed():
    stats1 = simulate(NaiveStrategy(), 400, BlackjackRules(), seed=42)
    stats2 = simulate(NaiveStrategy(), 400, BlackjackRules(), seed=42)
    assert stats1.total_payout == stats2.total_payout
    assert stats1.total_hands_played == stats2.total_hands_played


@pytest.mark.xfail(reason='Rules flag double_on_hard_9_10_11_only not enforced in can_double', strict=True)
def test_double_9_10_11_only_rule_not_yet_implemented():
    g = game(double_on_any_two_cards=False, double_on_hard_9_10_11_only=True)
    assert g.can_double(PlayerHandState(hand('9', '5'))) is False


@pytest.mark.xfail(reason='Split aces one-card-only restriction not implemented', strict=True)
def test_split_aces_one_card_only_rule_not_yet_implemented():
    g = game(allow_hit_split_aces=False, split_aces_receive_one_card_only=True)
    state = PlayerHandState(hand('A', '8'), is_split_hand=True)
    assert 'hit' not in g.get_legal_actions(state, current_total_hands=2)
