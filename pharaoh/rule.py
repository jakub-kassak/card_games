from __future__ import annotations

from typing import Callable

from pyrsistent.typing import PVector

from pharaoh.card import Card, Value, Suit
from pharaoh.game_state import GameState


class Condition:
    def test(self, state: GameState) -> bool:
        raise NotImplementedError

    def _description(self) -> str:
        raise NotImplementedError

    def __repr__(self):
        return f'{self.__class__.__name__}({self._description()})'


class ConditionAnd(Condition):
    def __init__(self, conditions: PVector[Condition]):
        self._conditions = conditions

    def test(self, state: GameState) -> bool:
        return all(c.test(state) for c in self._conditions)

    def _description(self) -> str:
        return ', '.join(repr(x) for x in self._conditions)


class VariableCondition(Condition):
    def __init__(self, variable: str, condition: Callable[[Suit | Value | int], bool]):
        self._variable = variable
        self._cond = condition

    def test(self, state: GameState) -> bool:
        return self._cond(state.sv[self._variable])

    def _description(self) -> str:
        return f'variable={self._variable}'  # , test={self._cond}'


class CardInHand(Condition):
    def __init__(self, card: Card):
        self._card = card

    def test(self, state: GameState) -> bool:
        return self._card in state.lp[state.sv['i']].bag

    def _description(self) -> str:
        return repr(self._card)
