from typing import Tuple, Optional, List

from pyrsistent import pvector
from pyrsistent.typing import PVector

from pharaoh.card import GERMAN_CARDS_DECK
from pharaoh.game import finished, legal_moves, create_game
from pharaoh.game_state import GameState
from pharaoh.move import Move
from pharaoh.player import Player, RandomPlayer
from pharaoh.rule import standard_ruleset


def play_game(state: GameState, players: PVector[Player], moves: PVector[Move]) \
        -> List[Tuple[GameState, Optional[Move]]]:
    if len(players) != len(state.lp):
        raise Exception('Incompatible game state: len(players) != len(state.lp)')
    game_history: List[Tuple[GameState, Optional[Move]]] = []
    while not finished(state):
        legal: List[Move] = legal_moves(state, moves)
        next_move: Move = players[state.i].play(state, legal)
        game_history.append((state, next_move))
        state = next_move.apply(state)
        if state.mc == 1000:
            break
    game_history.append((state, None))
    return game_history


def main():
    n = 5
    players: PVector[Player] = pvector(RandomPlayer() for _ in range(5))
    state, moves = create_game(standard_ruleset, GERMAN_CARDS_DECK, n)
    for t in play_game(state, players, moves):
        print(t)


if __name__ == '__main__':
    main()
