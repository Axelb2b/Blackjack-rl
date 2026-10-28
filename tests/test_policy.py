import json
from pathlib import Path

from Proj.src.blackjack.hand import Hand
from Proj.src.strategies.rl_strategy import RLStrategy

MODEL = Path(__file__).resolve().parents[1] / 'models' / 'selected_mc_policy.json'


def test_exported_json_model_contains_expected_shape():
    model = json.loads(MODEL.read_text(encoding='utf-8'))
    assert model['episodes'] == 1_000_000
    assert model['model_type'] == 'mc_initial_action_with_split_baseline'
    assert len(model['states']) == 340
    for row in model['states']:
        assert len(row['state']) == 4
        assert all(a in row['q_values'] for a in ('hit', 'stand', 'double', 'split'))


def test_policy_never_returns_illegal_action_on_simple_hand():
    model = json.loads(MODEL.read_text(encoding='utf-8'))
    q = {tuple(row['state']): row['q_values'] for row in model['states']}
    policy = RLStrategy(q)
    hand = Hand([('10', '♣'), ('6', '♦')])
    assert policy(hand, ('10', '♥'), can_double=False, can_split=False) in ('hit', 'stand')
