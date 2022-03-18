from typing import List, NewType

from pyrsistent import field, pvector_field
from pyrsistent import PClass
from pyrsistent.typing import PBag, PVector

from pharaoh.card import Suit, Card, Value
from pharaoh.rule import Move

Hand = NewType('Hand', PBag[Card])
Pile = NewType('Pile', PVector[Card])


class StateVariables(PClass):
    ace: int = field(type=int, mandatory=True, initial=0,
                     invariant=lambda x: (x >= 0, 'ace counter can not be negative'))
    suit: Suit = field(type=Suit, mandatory=True, initial=Suit.BELL)
    val: Value = field(type=Value, mandatory=True, initial=Value.X)
    cnt: int = field(type=int, mandatory=True, initial=1, invariant=lambda x: (x >= 0, 'draw count must be positive'))
    i: int = field(type=int, mandatory=True, initial=0, invariant=lambda x: (x >= 0, 'index must be non negative'))


class GameState(PClass):
    dp: Pile = pvector_field(Card)
    st: Pile = pvector_field(Card)
    lp: PVector[Hand] = pvector_field(PBag)
    sv: StateVariables = field(type=StateVariables, mandatory=True)
    mc: int = field(type=int, mandatory=True, initial=0)
    lp_mc: PVector[int] = pvector_field(int)
    __invariant__ = lambda s: ((len(s.dp) > 0, 'discard pile can not be empty'),
                               (len(s.lp) > 1, 'at least 2 players must play'),
                               (s.i < len(s.lp), 'index must be smaller than number of players'),
                               (len(s.lp_mc) == len(s.lp)), "size of LP_MC must match size of LP")


def start() -> GameState:
    raise NotImplementedError


def legal_moves(state: GameState) -> List[Move]:
    raise NotImplementedError


def next_state(state: GameState, rule: Move) -> GameState:
    raise NotImplementedError


def winners(state: GameState) -> List[int]:
    raise NotImplementedError
