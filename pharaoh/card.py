from enum import Enum
from dataclasses import dataclass
from itertools import product
from typing import List


class Suit(Enum):
    HEART = 1
    BELL = 2
    ACORN = 3
    LEAF = 4


class Value(Enum):
    VII = 7
    VIII = 8
    IX = 9
    X = 10
    UNDER = 11
    OVER = 12
    KING = 13
    ACE = 14


@dataclass(frozen=True)
class Card:
    suit: Suit
    value: Value


SUITS: List[Suit] = [s for s in Suit]
VALUES: List[Value] = [v for v in Value]
GERMAN_CARDS_DECK: List[Card] = [Card(s, v) for s, v in product(SUITS, VALUES)]