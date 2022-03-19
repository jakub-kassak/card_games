from __future__ import annotations

from typing import Callable

from pyrsistent import v
from pyrsistent.typing import PVector

from pharaoh.card import Card, Value, Suit
from pharaoh.game_state import GameState, Hand


class Move:
    def __init__(self, cond: Condition, action: Action):
        self._cond = cond
        self._action = action

    def test(self, state: GameState) -> bool:
        return self._cond.test(state)

    class ConditionUnsatisfied(Exception):
        pass

    def apply(self, state: GameState) -> GameState:
        if not self.test(state):
            raise self.ConditionUnsatisfied
        return self._action.apply(state)

    def __repr__(self):
        return f'Move(cond={self._cond}, action={self._action})'


class Condition:
    def test(self, state: GameState) -> bool:
        raise NotImplementedError

    def _description(self) -> str:
        raise NotImplementedError

    def __repr__(self):
        return f'{self.__class__.__name__}({self._description()})'


class CondAnd(Condition):
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


class Action:
    def apply(self, state: GameState) -> GameState:
        raise NotImplementedError

    def _description(self) -> str:
        raise NotImplementedError

    def __repr__(self):
        return f'{self.__class__.__name__}({self._description()})'


class ActionList(Action):
    def __init__(self, actions: PVector[Action]):
        self._actions = actions

    def apply(self, state: GameState) -> GameState:
        for a in self._actions:
            state = a.apply(state)
        return state

    def _description(self) -> str:
        return ', '.join(repr(x) for x in self._actions)


class PlayCard(Action):
    def __init__(self, card: Card):
        self._card = card

    def apply(self, state: GameState) -> GameState:
        i = state.sv['i']
        hand = Hand(state.lp[i].bag.remove(self._card))
        lp = state.lp.set(i, hand)
        state = state.set(lp=lp)
        dp = state.dp.append(self._card)
        return state.set(dp=dp)

    def _description(self) -> str:
        return repr(self._card)


class ChangeVariable(Action):
    def __init__(self, variable: str, action: Callable[[Suit | Value | int], Suit | Value | int]):
        self._action = action
        self._variable = variable

    def apply(self, state: GameState) -> GameState:
        sv = state.sv
        current_val = sv[self._variable]
        sv = sv.set(self._variable, self._action(current_val))
        return state.set(sv=sv)

    def _description(self) -> str:
        return f'variable={self._variable}'  # , action={self._action}'


ace_is_zero_cond = VariableCondition('ace', lambda ace: ace == 0)
heart_ix_in_hand_cond = CardInHand(Card(Suit.HEART, Value.IX))
cond1 = CondAnd(v(ace_is_zero_cond, heart_ix_in_hand_cond))

play_heart_ix = PlayCard(Card(Suit.HEART, Value.IX))
increase_player_index = ChangeVariable('i', lambda x: (x + 1) % 2)
increase_mc = ChangeVariable('mc', lambda x: x + 1)
action1 = ActionList(v(play_heart_ix, increase_player_index, increase_mc))

move1 = Move(cond1, action1)
