from random import shuffle
from typing import Tuple, List

from pyrsistent import pvector
from pyrsistent.typing import PVector

from pharaoh.card import GERMAN_CARDS_DECK
from pharaoh.game import finished, legal_moves, create_game, winners
from pharaoh.game_state import GameState
from pharaoh.move import Move
from pharaoh.player import Player, RandomPlayer, BiggestTuplePlayer, SmallestTuplePlayer
from pharaoh.rule import standard_ruleset


def play_game(state: GameState, players: PVector[Player], moves: PVector[Move]) \
        -> Tuple[List[GameState], List[Move]]:
    if len(players) != len(state.lp):
        raise Exception('Incompatible game state: len(players) != len(state.lp)')

    state_history: List[GameState] = []
    move_history: List[Move] = []
    while not finished(state):
        state_history.append(state)
        legal: List[Move] = legal_moves(state, moves)
        last_round = state_history[-len(state.lp):]
        next_move: Move = players[state.i].play(last_round, legal)
        move_history.append(next_move)
        state = next_move.apply(state)
        if state.mc == 1000:
            break
    state_history.append(state)
    return state_history, move_history


def main():
    n = 5
    players: PVector[Player] = pvector(RandomPlayer() for _ in range(5))
    state, moves = create_game(standard_ruleset, GERMAN_CARDS_DECK, n)
    state_history, move_history = play_game(state, players, moves)
    for i in range(len(state_history)):
        print(state_history[i], '\t', move_history[i] if i < len(move_history) else None)
    print(winners(state_history[-1]))


def main2():
    n = 6
    players: PVector[Player] = pvector(RandomPlayer() for _ in range(2))
    players = players.extend(BiggestTuplePlayer() for _ in range(2))
    players = players.extend(SmallestTuplePlayer() for _ in range(2))

    stats = [0] * n
    length = 0
    m = 200
    players_numbers = [(players[i], i) for i in range(n)]
    for j in range(m):
        if j % 10 == 9:
            print(j)
        shuffle(players_numbers)
        positions = [0] * n
        for i in range(n):
            player, number = players_numbers[i]
            positions[i] = number
        players2 = pvector(x[0] for x in players_numbers)
        state, moves = create_game(standard_ruleset, GERMAN_CARDS_DECK, n)
        state_history, move_history = play_game(state, players2, moves)
        result = [x-1 for x in winners(state_history[-1])]
        for i in range(n):
            stats[positions[result[i]]] += i
        length += state_history[-1].mc
    print(stats)
    print(length / m / n)


if __name__ == '__main__':
    main()
