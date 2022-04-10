import random
from typing import List

from pharaoh.game_state import GameState
from pharaoh.move import Move


class Player:
    def play(self, state: GameState, moves: List[Move]) -> Move:
        raise NotImplementedError


class RandomPlayer(Player):
    def play(self, state: GameState, moves: List[Move]) -> Move:
        return random.choice(moves)
