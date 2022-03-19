from typing import List

from pharaoh.game_state import GameState
from pharaoh.rule import Move


def start() -> GameState:
    raise NotImplementedError


def legal_moves(state: GameState) -> List[Move]:
    raise NotImplementedError


def next_state(state: GameState, rule: Move) -> GameState:
    raise NotImplementedError


def winners(state: GameState) -> List[int]:
    raise NotImplementedError
