from dataclasses import dataclass

from Proj.src.blackjack.game import BlackjackGame, RoundResult
from Proj.src.blackjack.rules import BlackjackRules
from Proj.src.blackjack.shoe import Shoe


@dataclass
class SimulationStats:
    strategy_name: str
    n_rounds: int
    total_hands_played: int

    total_payout: float
    ev_per_round: float
    ev_per_hand: float

    player_wins: int
    dealer_wins: int
    pushes: int
    blackjacks: int

    doubled_hands: int
    split_hands: int
    rounds_with_split: int

    win_rate: float
    lose_rate: float
    push_rate: float
    blackjack_rate: float
    double_rate: float
    split_hand_rate: float
    split_round_rate: float


def simulate(strategy, n_rounds: int, rules: BlackjackRules, seed: int | None = None) -> SimulationStats:
    """
    Simule n_rounds manches de blackjack avec une stratégie donnée.
    """
    shoe = Shoe(rules, seed=seed)
    game = BlackjackGame(rules, shoe)

    total_payout = 0.0

    player_wins = 0
    dealer_wins = 0
    pushes = 0
    blackjacks = 0

    doubled_hands = 0
    split_hands = 0
    rounds_with_split = 0
    total_hands_played = 0

    for _ in range(n_rounds):
        round_result: RoundResult = game.play_round(strategy)
        total_payout += round_result.total_payout

        round_has_split = False

        for hand_result in round_result.hand_results:
            total_hands_played += 1

            if hand_result.outcome == "player_win":
                player_wins += 1
            elif hand_result.outcome == "dealer_win":
                dealer_wins += 1
            elif hand_result.outcome == "push":
                pushes += 1
            elif hand_result.outcome == "player_blackjack":
                player_wins += 1
                blackjacks += 1

            if hand_result.doubled:
                doubled_hands += 1

            if hand_result.is_split_hand:
                split_hands += 1
                round_has_split = True

        if round_has_split:
            rounds_with_split += 1

    ev_per_round = total_payout / n_rounds if n_rounds > 0 else 0.0
    ev_per_hand = total_payout / total_hands_played if total_hands_played > 0 else 0.0

    win_rate = player_wins / total_hands_played if total_hands_played > 0 else 0.0
    lose_rate = dealer_wins / total_hands_played if total_hands_played > 0 else 0.0
    push_rate = pushes / total_hands_played if total_hands_played > 0 else 0.0
    blackjack_rate = blackjacks / total_hands_played if total_hands_played > 0 else 0.0
    double_rate = doubled_hands / total_hands_played if total_hands_played > 0 else 0.0
    split_hand_rate = split_hands / total_hands_played if total_hands_played > 0 else 0.0
    split_round_rate = rounds_with_split / n_rounds if n_rounds > 0 else 0.0

    return SimulationStats(
        strategy_name=strategy.__class__.__name__,
        n_rounds=n_rounds,
        total_hands_played=total_hands_played,
        total_payout=total_payout,
        ev_per_round=ev_per_round,
        ev_per_hand=ev_per_hand,
        player_wins=player_wins,
        dealer_wins=dealer_wins,
        pushes=pushes,
        blackjacks=blackjacks,
        doubled_hands=doubled_hands,
        split_hands=split_hands,
        rounds_with_split=rounds_with_split,
        win_rate=win_rate,
        lose_rate=lose_rate,
        push_rate=push_rate,
        blackjack_rate=blackjack_rate,
        double_rate=double_rate,
        split_hand_rate=split_hand_rate,
        split_round_rate=split_round_rate,
    )