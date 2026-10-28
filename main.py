from Proj.src.blackjack.card_counting import HI_LO, count_state_from_seen_cards
from Proj.src.blackjack.game import BlackjackGame
from Proj.src.blackjack.rules import BlackjackRules
from Proj.src.blackjack.shoe import Shoe
from Proj.src.strategies.basic_strategy import NaiveStrategy
from Proj.src.strategies.optimal_strategy import OptimalStrategy
from Proj.src.strategies.player import PlayerStrategy
from Proj.src.strategies.random_strategy import RandomStrategy


def print_round_result(round_number: int, result, shoe: Shoe) -> None:
    print()
    print(f"================ Manche {round_number} ================")
    print("Main dealer :", result.dealer_hand.pretty_cards(), "| valeur =", result.dealer_hand.value())
    print()

    for i, hand_result in enumerate(result.hand_results, start=1):
        print(f"--- Main joueur {i} ---")
        print("Cartes      :", hand_result.player_hand.pretty_cards(), "| valeur =", hand_result.player_hand.value())
        print("Issue       :", hand_result.outcome)
        print("Split hand  :", hand_result.is_split_hand)
        print("Doublé      :", hand_result.doubled)
        print("Mise finale :", hand_result.final_bet)
        print("Payout      :", hand_result.payout)
        print()

    print("Payout total de la manche :", result.total_payout)
    print("Cartes restantes dans le sabot :", shoe.cards_remaining())
    print("Cut card atteinte pendant la manche :", result.cut_card_was_reached_this_round)
    print("Sabot remélangé après la manche    :", result.reshuffled_after_round)


def main() -> None:
    rules = BlackjackRules()
    shoe = Shoe(rules)
    game = BlackjackGame(rules, shoe)

    mode = input("Choisis une stratégie (player / naive / random / optimal) : ").strip().lower()

    if mode == "player":
        strategy = PlayerStrategy()
        max_rounds = None
    elif mode == "random":
        strategy = RandomStrategy()
        max_rounds = 100
    elif mode == "optimal":
        strategy = OptimalStrategy()
        max_rounds = 100
    else:
        strategy = NaiveStrategy()
        max_rounds = 100

    round_number = 1
    session_payout = 0.0
    seen_cards = []

    while True:
        result = game.play_round(strategy)
        session_payout += result.total_payout

        # Mise à jour des cartes vues
        for hand_result in result.hand_results:
            seen_cards.extend(hand_result.player_hand.cards)
        seen_cards.extend(result.dealer_hand.cards)

        print_round_result(round_number, result, shoe)

        # Calcul du count
        count_state = count_state_from_seen_cards(
            seen_cards=seen_cards,
            cards_remaining=shoe.cards_remaining(),
            system=HI_LO,
        )

        print("Running count :", count_state.running_count)
        print("True count    :", round(count_state.true_count, 2))
        print("Decks restants:", round(count_state.decks_remaining, 2))
        print("Système       :", count_state.system_name)
        print("Payout cumulé session :", session_payout)

        # Reset du count après reshuffle
        if result.reshuffled_after_round:
            seen_cards = []
            print(">>> Reshuffle détecté : reset du count")

        if mode == "player":
            choice = input("Rejouer ? (entrée = oui / q = quitter) : ").strip().lower()
            if choice == "q":
                break
        else:
            if max_rounds is not None and round_number >= max_rounds:
                print()
                print(f"Fin de session automatique après {max_rounds} manches.")
                break

        round_number += 1


if __name__ == "__main__":
    main()