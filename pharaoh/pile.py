from random import shuffle
from typing import Optional, Iterable, Tuple

from pyrsistent.typing import PVector
from pyrsistent import v

from pharaoh.card import Card


class Pile:
    def __init__(self, cards: PVector[Card]):
        self._cards = cards

    def __len__(self) -> int:
        return len(self._cards)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(cards={self._cards.__repr__()})'

    def draw(self) -> Optional[Tuple]:
        if len(self):
            card: Card = self._cards[0]
            return card, self.__class__(self._cards.delete(0))
        return None

    def put_all(self, cards: Iterable):
        cards = list(cards)
        shuffle(cards)
        return self.__class__(self._cards.extend(cards))

    def put(self, card: Card):
        return self.__class__(self._cards.append(card))

    def remove_cards(self) -> Tuple:
        return self._cards.delete(-1), self.__class__(v(self._cards[-1]))


class DiscardPile(Pile):
    class Empty(Exception):
        pass

    def __init__(self, cards: PVector):
        if len(cards) == 0:
            raise DiscardPile.Empty("Discard pile can not be empty.")
        super().__init__(cards)

    @property
    def top(self) -> Card:
        return self._cards[-1]

