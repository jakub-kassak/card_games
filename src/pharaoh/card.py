from enum import IntEnum
from dataclasses import dataclass
from itertools import product
from typing import List, Dict

from pyrsistent import pvector, pbag
from pyrsistent.typing import PVector, PBag


class Suit(IntEnum):
    HEART = 1
    BELL = 2
    ACORN = 3
    LEAF = 4

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return symbols[self.name]


class Value(IntEnum):
    VII = 7
    VIII = 8
    IX = 9
    X = 10
    UNDER = 11
    OVER = 12
    KING = 13
    ACE = 14

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return symbols[self.name]


@dataclass(frozen=True, order=True)
class Card:
    suit: Suit
    value: Value

    def __repr__(self) -> str:
        return f'({repr(self.suit)}, {repr(self.value)})'

    def __str__(self) -> str:
        return f'{symbols["__PREFIX__"]}{self.suit}{symbols["__DELIMITER__"]}{self.value}{symbols["__SUFFIX__"]}'


@dataclass(frozen=True)
class Deck:
    cards: PBag
    suits: PVector[Suit]
    values: PVector[Value]


symbols: Dict[str, str] = {s.name: s.name for s in Suit} | {v.name: v.name for v in Value} | {
    "__PREFIX__": "(", "__SUFFIX__": ")", "__DELIMITER__": ", "}

SUITS: PVector[Suit] = pvector(s for s in Suit)
VALUES: PVector[Value] = pvector(v for v in Value)
GERMAN_CARDS: List[Card] = [Card(s, v) for s, v in product(SUITS, VALUES)]
GERMAN_CARDS_DECK: Deck = Deck(pbag(GERMAN_CARDS), SUITS, VALUES)
