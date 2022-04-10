from enum import Enum
from dataclasses import dataclass
from itertools import product
from typing import List

from pyrsistent import pvector, pbag
from pyrsistent.typing import PVector, PBag


class Suit(Enum):
    HEART = 1
    BELL = 2
    ACORN = 3
    LEAF = 4

    def __repr__(self):
        return self.name


class Value(Enum):
    VII = 7
    VIII = 8
    IX = 9
    X = 10
    UNDER = 11
    OVER = 12
    KING = 13
    ACE = 14

    def __repr__(self):
        return self.name


@dataclass(frozen=True)
class Card:
    suit: Suit
    value: Value

    def __repr__(self):
        return f'({repr(self.suit)}, {repr(self.value)})'


@dataclass(frozen=True)
class Deck:
    cards: PBag
    suits: PVector[Suit]
    values: PVector[Value]


SUITS: PVector[Suit] = pvector(s for s in Suit)
VALUES: PVector[Value] = pvector(v for v in Value)
GERMAN_CARDS: List[Card] = [Card(s, v) for s, v in product(SUITS, VALUES)]
GERMAN_CARDS_DECK: Deck = Deck(pbag(GERMAN_CARDS), SUITS, VALUES)
