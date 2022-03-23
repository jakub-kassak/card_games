from __future__ import annotations

from dataclasses import dataclass

from pyrsistent import field, pvector_field, PClass, b
from pyrsistent.typing import PBag, PVector

from pharaoh.card import Suit, Card, Value, GERMAN_CARDS_DECK

Pile = PVector[Card]


def pl(*args):
    return Player(b(*args))


@dataclass(frozen=True)
class Player:
    hand: PBag[Card]

    def __repr__(self):
        return f'Player({", ".join(str(x) for x in self.hand)})'


class GameState(PClass):
    dp: Pile = pvector_field(Card)
    st: Pile = pvector_field(Card)
    lp: PVector[Player] = pvector_field(Player)
    lp_mc: PVector[int] = pvector_field(int)
    ace: int = field(type=int, mandatory=True, invariant=lambda x: (x >= 0, 'ace counter can not be negative'))
    suit: Suit = field(type=Suit, mandatory=True)
    val: Value = field(type=Value, mandatory=True)
    cnt: int = field(type=int, mandatory=True, invariant=lambda x: (x >= 0, 'draw count must be positive'))
    i: int = field(type=int, mandatory=True, invariant=lambda x: (x >= 0, 'index can not be negative'))
    mc: int = field(type=int, mandatory=True)
    __invariant__ = lambda s: ((len(s.dp) > 0, 'discard pile can not be empty'),
                               (len(s.lp) > 1, 'at least 2 players must play'),
                               (s.i < len(s.lp), 'index must be smaller than number of players'),
                               (len(s.lp_mc) == len(s.lp), "size of LP_MC must match size of LP"),
                               (len(s.st) >= s.cnt, "draw count must be smaller/equal to the size of stock"))

    def __getitem__(self, name: str) -> Pile | PVector | int | Suit | Value:
        return self.__getattribute__(name)


deck = GERMAN_CARDS_DECK[:]
state1 = GameState(
    dp=(deck[0],),
    st=deck[11:],
    lp=(pl(*deck[1:6]), pl(*deck[6:11])),
    ace=0,
    suit=Suit.HEART,
    val=Value.VII,
    cnt=1,
    i=0,
    mc=0,
    lp_mc=(-1, -1)
)
