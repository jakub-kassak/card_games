from __future__ import annotations

from typing import Iterable

from pyrsistent import field, pvector_field, PClass, pbag
from pyrsistent.typing import PBag, PVector

from pharaoh.card import Suit, Card, Value, GERMAN_CARDS

Pile = PVector[Card]


class Hand:
    def __init__(self, cards: Iterable[Card]):
        self._bag: PBag[Card] = pbag(cards)

    def __contains__(self, elt) -> bool:
        return self._bag.__contains__(elt)

    def __sub__(self, other) -> Hand:
        return self.__class__(self._bag.__sub__(other))

    def update(self, iterable) -> Hand:
        return self.__class__(self._bag.update(iterable))

    def __len__(self):
        return len(self._bag)

    def __repr__(self):
        return f'{self.__class__.__name__}({", ".join(str(x) for x in self._bag)})'


class GameState(PClass):
    dp: Pile = pvector_field(Card)
    st: Pile = pvector_field(Card)
    lp: PVector[Hand] = pvector_field(Hand)
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


cards = [*GERMAN_CARDS]
state1 = GameState(
    dp=(cards[0],),
    st=cards[11:],
    lp=(Hand(cards[1:6]), Hand(cards[6:11])),
    ace=0,
    suit=Suit.HEART,
    val=Value.VII,
    cnt=1,
    i=0,
    mc=0,
    lp_mc=(-1, -1)
)
