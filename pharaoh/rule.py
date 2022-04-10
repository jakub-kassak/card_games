from __future__ import annotations

from itertools import permutations
from typing import List, Optional, Tuple, Callable, Dict, Iterator

from pyrsistent import v, pvector
from pyrsistent.typing import PVector

from pharaoh.card import Card, Value, Suit, Deck
from pharaoh.move import Move, Action, ChangeVariable, Condition, CondAnd, VariableCondition, CardInHand, PlayCards


def partial_permutations(cards: List[Card], size: Optional[int] = None):
    if size is None:
        size = len(cards)
    for i in range(size):
        for perm in permutations(cards, i + 1):
            yield perm


def ace_played(cards: Tuple[Card], _: int) -> List[Action]:
    if cards[0].value == Value.ACE:
        return [ChangeVariable('ace', lambda a1, a2=(len(cards) + 1): a1 + a2, f'ace += {len(cards) + 1}'),
                ChangeVariable('cnt', lambda _: 0, 'cnt = 0')]
    return []


def vii_played(cards: Tuple[Card], _: int) -> List[Action]:
    if cards[0].value == Value.VII:
        n = len(cards) * 3
        return [ChangeVariable('cnt', lambda cnt: n if cnt == 1 else cnt + n, 'cnt = n if cnt == 1 else cnt + n')]
    return []


def leaves_under_played_as_first(cards: Tuple[Card], _: int) -> List[Action]:
    if cards[0].value == Value.UNDER and cards[0].suit == Suit.LEAF:
        return [ChangeVariable('cnt', lambda _: 1, 'cnt = 1')]
    return []


def change_suit_to_top(cards: Tuple[Card], _: int) -> List[Action]:
    if cards[0].value != Value.OVER:
        return [ChangeVariable('suit', lambda _, s=cards[-1].suit: s, f'suit={cards[-1].suit}')]
    return []


def change_val_to_top(cards: Tuple[Card], _: int) -> List[Action]:
    return [ChangeVariable('val', lambda _, val=cards[-1].value: val, f'suit={cards[-1].value}')]


def change_ace_counter(_, __) -> List[Action]:
    return [ChangeVariable('ace', lambda ace: max(0, ace - 1), 'ace = max(0, ace - 1)')]


def increment_player_index(cards: Tuple[Card] | Tuple[()], player_count: int) -> List[Action]:
    if len(cards) < 4:
        return [ChangeVariable('i', lambda i, pc=player_count: (i + 1) % pc, f'(i + 1) % {player_count}')]
    return []


def increment_move_counter(_, __) -> List[Action]:
    return [ChangeVariable('mc', lambda mc: mc + 1, "mc += 1")]


game_mechanics_for_drawing: List[Callable[[Tuple[Card] | Tuple[()], int], List[Action]]] = [
    change_ace_counter,
    increment_player_index,
    increment_move_counter
]
game_mechanics_for_played_cards: List[Callable[[Tuple[Card], int], List[Action]]] = [
    ace_played,
    vii_played,
    leaves_under_played_as_first,
    change_suit_to_top,
    change_val_to_top,
    change_ace_counter,
    increment_player_index,
    increment_move_counter
]


class Rule:
    def generate_moves(self, deck: Deck) -> List[Move]:
        raise NotImplementedError


class PlayRule(Rule):
    def __init__(self, cond_generator: Optional[Callable[[Suit, Value], List[Condition]]] = None,
                 size: int = 0,
                 value_filter: Callable[[Value], bool] = lambda _: True,
                 move_generator: Optional[Callable[[List[Condition], List[Action], Deck], List[Move]]]
                 = None):
        self._cond_generator = cond_generator if cond_generator else lambda _, __: []
        self._size = size
        self._value_filter = value_filter
        self._move_generator = move_generator if move_generator else lambda c, a, _: [Move(pvector(c), pvector(a))]

    @staticmethod
    def _sort_deck(deck: Deck) -> Tuple[Dict[Suit, List[Card]], Dict[Value, List[Card]]]:
        s_dict: Dict[Suit, List[Card]] = {suit: [] for suit in deck.suits}
        v_dict: Dict[Value, List[Card]] = {val: [] for val in deck.values}
        for card in deck.cards:
            s_dict[card.suit].append(card)
            v_dict[card.value].append(card)
        return s_dict, v_dict

    def generate_moves(self, deck: Deck) -> List[Move]:
        s_dict, v_dict = self._sort_deck(deck)
        moves: List[Move] = []
        for val in filter(self._value_filter, deck.values):
            for perm in partial_permutations(v_dict[val], len(v_dict[val]) + self._size):
                suit: Suit = perm[0].suit
                conds: List[Condition] = self._cond_generator(suit, val)
                conds.extend(CardInHand(card) for card in perm)
                actions: List[Action] = [PlayCards(pvector(perm))]
                mechanics: Iterator[Optional[Action]] = (m(perm) for m in game_mechanics_for_played_cards)
                actions.extend(a for a in mechanics if a is not None)
                moves.extend(self._move_generator(conds, actions, deck))
        return moves


def play_over_move_generator(conds: List[Condition], actions: List[Action], deck: Deck) -> List[Move]:
    change_suit_list = [ChangeVariable('suit', lambda _, s=suit: s, f'suit={suit}') for suit in deck.suits]
    moves = []
    for change in change_suit_list:
        actions.append(change)
        moves.append(Move(pvector(conds), pvector(actions)))
        actions.pop()
    return moves


def f_generator(arg: Suit | Value) -> Callable[[PVector | int | Suit | Value], bool]:
    return lambda a: a == arg


regular_state_cond: Condition = CondAnd(v(
        VariableCondition('ace', lambda ace: ace == 0, 'ace == 0'),
        VariableCondition('cnt', lambda cnt: cnt == 1, 'cnt == 1')
))
suit_conds: Dict[Suit, Condition] = {
        suit: VariableCondition('suit', f_generator(suit), f'suit=={suit}')
        for suit in Suit
}
val_conds: Dict[Value, Condition] = {
        val: VariableCondition('val', f_generator(val), f'val=={val}')
        for val in Value
}
match_suit_rule: PlayRule = PlayRule(cond_generator=lambda suit, _: [suit_conds[suit], regular_state_cond])
match_value_rule: PlayRule = PlayRule(cond_generator=lambda _, val: [val_conds[val], regular_state_cond], size=-1)
play_over_rule: PlayRule = PlayRule(cond_generator=lambda _, __: [regular_state_cond],
                                    value_filter=lambda val: val == Value.OVER,
                                    move_generator=play_over_move_generator)
