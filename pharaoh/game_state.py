from dataclasses import dataclass

from pyrsistent import PClass
from pyrsistent import field, pvector_field, PRecord, b
from pyrsistent.typing import PBag, PVector

from pharaoh.card import Suit, Card, Value, GERMAN_CARDS_DECK

Pile = PVector[Card]


def h(*args):
    return Hand(b(*args))


@dataclass(frozen=True)
class Hand:
    bag: PBag[Card]

    def __repr__(self):
        return f'Hand({", ".join(str(x) for x in self.bag)})'


class StateVariables(PRecord):
    ace: int = field(type=int, mandatory=True, initial=0,
                     invariant=lambda x: (x >= 0, 'ace counter can not be negative'))
    suit: Suit = field(type=Suit, mandatory=True, initial=Suit.BELL)
    val: Value = field(type=Value, mandatory=True, initial=Value.X)
    cnt: int = field(type=int, mandatory=True, initial=1, invariant=lambda x: (x >= 0, 'draw count must be positive'))
    i: int = field(type=int, mandatory=True, initial=0, invariant=lambda x: (x >= 0, 'index must be non negative'))
    mc: int = field(type=int, mandatory=True)


class GameState(PClass):
    dp: Pile = pvector_field(Card)
    st: Pile = pvector_field(Card)
    lp: PVector[Hand] = pvector_field(Hand)
    sv: StateVariables = field(type=StateVariables, mandatory=True)
    lp_mc: PVector[int] = pvector_field(int)
    __invariant__ = lambda s: ((len(s.dp) > 0, 'discard pile can not be empty'),
                               (len(s.lp) > 1, 'at least 2 players must play'),
                               (s.sv.i < len(s.lp), 'index must be smaller than number of players'),
                               (len(s.lp_mc) == len(s.lp), "size of LP_MC must match size of LP"))


deck = GERMAN_CARDS_DECK[:]
state1 = GameState(
    dp=(deck[0],),
    st=deck[11:],
    lp=(h(*deck[1:6]), h(*deck[6:11])),
    sv=StateVariables(
        ace=0,
        suit=Suit.HEART,
        val=Value.VII,
        cnt=1,
        i=0,
        mc=0
    ),
    lp_mc=(-1, -1)
)
