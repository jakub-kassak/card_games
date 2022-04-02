from typing import List, Optional, Tuple, Callable

from pharaoh.card import Card, Value, Suit
from pharaoh.move import Move, Action, ChangeVariable


def ace_was_played(cards: Tuple[Card]) -> Optional[Action]:
    if cards[0].value == Value.ACE:
        return ChangeVariable('ace', lambda a1, a2=(len(cards) + 1): a1 + a2, f'ace += {len(cards) + 1}')
    return None


def leaves_under_as_first(cards: Tuple[Card]) -> Optional[Action]:
    if cards[0].value == Value.UNDER and cards[0].suit == Suit.LEAF:
        return ChangeVariable('cnt', lambda _: 1, 'cnt = 1')
    return None


def change_ace_counter(cards: Tuple[Card]) -> Optional[Action]:
    return ChangeVariable('ace', lambda ace: max(0, ace - 1), 'ace = max(0, ace - 1)')


def change_suit_to_top(cards: Tuple[Card]) -> Optional[Action]:
    if cards[0].value != Value.OVER:
        return ChangeVariable('suit', lambda _, s=cards[-1].suit: s, f'suit={cards[-1].suit}')
    return None


def change_val_to_top(cards: Tuple[Card]) -> Optional[Action]:
    return ChangeVariable('suit', lambda _, val=cards[-1].value: val, f'suit={cards[-1].value}')


game_mechanics_for_played_cards: List[Callable[[Tuple[Card]], Optional[Action]]] = [
    ace_was_played,
    leaves_under_as_first,
    change_ace_counter,
    change_suit_to_top,
    change_val_to_top
]


class Rule:
    def generate_moves(self, deck: List[Card]) -> List[Move]:
        raise NotImplementedError
