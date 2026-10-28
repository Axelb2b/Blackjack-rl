"""Reproducible benchmark of the supplied blackjack strategies.

Outputs empirical net payout per round with an approximate normal 95% CI.
The CI treats individual rounds as independent, an approximation because
successive rounds share the same shoe until the cut-card reshuffle.
"""
import argparse
import json
import math
from pathlib import Path

from Proj.src.blackjack.rules import BlackjackRules
from Proj.src.blackjack.shoe import Shoe
from Proj.src.blackjack.game import BlackjackGame
from Proj.src.strategies.basic_strategy import NaiveStrategy
from Proj.src.strategies.random_strategy import RandomStrategy
from Proj.src.strategies.optimal_strategy import OptimalStrategy
from Proj.src.strategies.rl_strategy import RLStrategy


def load_json_model(path):
    model = json.loads(Path(path).read_text(encoding='utf-8'))
    q_table = {}
    for record in model['states']:
        key = tuple(record['state'])
        if len(key) != 4:
            raise ValueError('Malformed state')
        q_table[key] = {key: float(value) for key, value in record['q_values'].items()}
    return q_table, model


def benchmark(runs, seed, model_path):
    q_table, metadata = load_json_model(model_path)
    policies = [
        ('Naive (hit to 17)', NaiveStrategy()),
        ('Random', RandomStrategy(seed=seed)),
        ('Rule-based reference', OptimalStrategy()),
        ('Monte Carlo policy', RLStrategy(q_table)),
    ]
    rows = []
    for name, strategy in policies:
        shoe = Shoe(BlackjackRules(), seed=seed)
        game = BlackjackGame(BlackjackRules(), shoe)
        n = 0
        total = 0.0
        total_sq = 0.0
        wins, losses, pushes, blackjacks = 0, 0, 0, 0
        doubles, splits, hands = 0, 0, 0
        for _ in range(runs):
            result = game.play_round(strategy)
            p = result.total_payout
            total += p
            total_sq += p * p
            n += 1
            for hr in result.hand_results:
                hands += 1
                if hr.outcome in {'player_win', 'player_blackjack'}: wins += 1
                if hr.outcome == 'dealer_win': losses += 1
                if hr.outcome == 'push': pushes += 1
                if hr.outcome == 'player_blackjack': blackjacks += 1
                if hr.doubled: doubles += 1
                if hr.is_split_hand: splits += 1
        mean = total / n
        variance = max((total_sq - n * mean * mean) / (n - 1), 0)
        se = math.sqrt(variance / n)
        row = dict(strategy=name, rounds=n, seed=seed, ev_per_round=mean,
                   ci95_low=mean - 1.96 * se, ci95_high=mean + 1.96 * se,
                   total_payout=total, hands=hands,
                   win_rate_hands=wins / hands,
                   loss_rate_hands=losses / hands,
                   push_rate_hands=pushes / hands,
                   natural_blackjacks=blackjacks,
                   double_rate_hands=doubles / hands,
                   split_rate_hands=splits / hands)
        print(f'{name:24} EV={mean:+.5f} units/round 95% approx CI [{row["ci95_low"]:+.5f}, {row["ci95_high"]:+.5f}]',flush=True)
        rows.append(row)
    return dict(description='Exploratory simulated policies benchmark. Not a gambling recommendation.',
                rules=vars(BlackjackRules()), model_type=metadata.get('model_type'),
                model_training_episodes=metadata.get('episodes'),
                model_state_count=len(q_table),
                methodology='Four policy evaluations with the same seed and rules, but different trajectories. Empirical CI is a normal approximation assuming independent rounds; reused shoe introduces dependence.',
                results=rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rounds',type=int,default=10000)
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--model',default='models/selected_mc_policy.json')
    parser.add_argument('--output',default=None)
    args=parser.parse_args()
    if args.rounds < 1: parser.error('--rounds must be positive')
    summary=benchmark(args.rounds,args.seed,args.model)
    if args.output:
        out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print(f'Wrote {out}')

if __name__=='__main__':main()
