from __future__ import annotations

from random import shuffle
from typing import List, Iterable, Callable

from pyrsistent import field, pvector_field, PClass, pbag
from pyrsistent.typing import PBag, PVector

from pharaoh.card import Suit, Card, Value, Deck

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

    def __iter__(self):
        return self._bag.__iter__()

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
    deck_size: int = field(type=int, mandatory=True)
    __invariant__ = lambda s: ((len(s.dp) > 0, 'discard pile can not be empty'),
                               (len(s.lp) > 1, 'at least 2 players must play'),
                               (s.i < len(s.lp), 'index must be smaller than number of players'),
                               (len(s.lp_mc) == len(s.lp), "size of LP_MC must match size of LP"),
                               (s.cnt == 0 or len(s.st) > 0 or len(s.dp) == 1, "cnt==0 or len(st)>0 or len(dp)==1"),
                               (any(x == -1 for x in s.lp_mc), "at least one player must be in game"),
                               (not s.ace == 0 or s.cnt > 0, 'ace == 0 implies cnt > 0'),
                               (not s.ace > 0 or s.cnt == 0, 'ace > 0 implies cnt == 0'),
                               (s.deck_size == sum(map(len, s.lp)) + len(s.dp) + len(s.st), 'card disappeared'),
                               (s.lp_mc[s.i] == -1, 'finished player is on the move'))

    def __getitem__(self, name: str) -> Pile | PVector | int | Suit | Value:
        return self.__getattribute__(name)

    @classmethod
    def init_state(cls, deck: Deck, player_cnt: int, init_cards: int,
                   mix_cards: Callable[[List[Card]], None] = shuffle) -> GameState:
        cards_list: List[Card] = [*deck.cards]
        mix_cards(cards_list)
        top: Card = cards_list.pop()
        hands: List[List[Card]] = [[] for _ in range(player_cnt)]
        for i in range(player_cnt):
            for _ in range(init_cards):
                if len(cards_list) == 0:
                    raise Exception("not enough cards for everyone")
                hands[i].append(cards_list.pop())
        if top.value == Value.VII:
            cnt = 3
            ace = 0
        elif top.value == Value.ACE:
            cnt = 0
            ace = 1
        else:
            cnt = 1
            ace = 0
        return cls(
            dp=(top,),
            st=cards_list,
            lp=(Hand(h) for h in hands),
            ace=ace,
            suit=top.suit,
            val=top.value,
            cnt=cnt,
            i=0,
            mc=0,
            lp_mc=(-1,) * player_cnt,
            deck_size=len(deck.cards)
        )
