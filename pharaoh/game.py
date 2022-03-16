from dataclasses import dataclass
from typing import List

from pharaoh.card import Suit
from pharaoh.rule import Move
from pharaoh.pile import Pile


class Hand:
    pass


@dataclass(frozen=True)
class StateVariables:
    a: int
    suit: Suit
    cnt: int


@dataclass(frozen=True)
class GameState:
    dp: Pile
    pp: Pile
    lp: List[Hand]
    i: int
    sv: StateVariables


def start() -> GameState:
    raise NotImplementedError


def legal_moves(state: GameState) -> List[Move]:
    raise NotImplementedError


def next_state(state: GameState, rule: Move) -> GameState:
    raise NotImplementedError


def winners(state: GameState) -> List[int]:
    raise NotImplementedError
