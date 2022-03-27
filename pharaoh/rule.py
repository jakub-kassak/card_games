from __future__ import annotations

from typing import List, Callable, Union, Optional

from pyrsistent import v
from pyrsistent.typing import PVector

from pharaoh.card import Card, Value, Suit
from pharaoh.game_state import GameState, Player

ConditionCallable = Union[Callable[[Suit], bool], Callable[[Value], bool], Callable[[int], bool]]
ActionCallable = Union[Callable[[Suit], Suit], Callable[[Value], Value], Callable[[int], int]]


class Rule:
    def generate_moves(self, deck: List[Card]) -> List[Move]:
        raise NotImplementedError


class Move:
    def __init__(self, cond: Condition, action: Action):
        self._cond = cond
        self._action = action

    def test(self, state: GameState) -> bool:
        return self._cond.test(state)

    class ConditionUnsatisfied(Exception):
        pass

    def apply(self, state: GameState):
        if not self.test(state):
            raise self.ConditionUnsatisfied

        state_evolver = state.evolver()
        state_evolver.dp = state.dp.evolver()
        state_evolver.st = state.st.evolver()
        state_evolver.lp = state.lp.evolver()

        self._action.apply(state_evolver)

        state_evolver.dp = state_evolver.dp.persistent()
        state_evolver.st = state_evolver.st.persistent()
        state_evolver.lp = state_evolver.lp.persistent()
        return state_evolver.persistent()

    def __repr__(self) -> str:
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
    def __init__(self, variable: str, condition: ConditionCallable, description: Optional[str]):
        self._desc = description if description else 'unknown'
        self._var = variable
        self._cond = condition

    def test(self, state: GameState) -> bool:
        return self._cond(state[self._var])

    def _description(self) -> str:
        return f'variable={self._var}, cond=<{self._desc}>'


class CardInHand(Condition):
    def __init__(self, card: Card):
        self._card = card

    def test(self, state: GameState) -> bool:
        return self._card in state.lp[state['i']].hand

    def _description(self) -> str:
        return repr(self._card)


class Action:
    def apply(self, s_evolver) -> None:
        raise NotImplementedError

    def _description(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._description()})'


class ActionList(Action):
    def __init__(self, actions: PVector[Action]):
        self._actions = actions

    def apply(self, s_evolver) -> None:
        for a in self._actions:
            a.apply(s_evolver)

    def _description(self) -> str:
        return ', '.join(repr(x) for x in self._actions)


class PlayCard(Action):
    def __init__(self, card: Card):
        self._card = card

    def apply(self, s_evolver) -> None:
        current_player = s_evolver.lp[s_evolver.i].hand
        s_evolver.lp[s_evolver.i] = Player(current_player.remove(self._card))
        s_evolver.dp = s_evolver.dp.append(self._card)

    def _description(self) -> str:
        return repr(self._card)


class ChangeVariable(Action):
    def __init__(self, variable: str, action: ActionCallable, description: Optional[str]):
        self._action = action
        self._desc = description if description else 'unknown'
        self._var = variable

    def apply(self, s_evolver) -> None:
        s_evolver[self._var] = self._action(s_evolver[self._var])

    def _description(self) -> str:
        return f'variable={self._var}, action=<{self._desc}>'


class DrawCards(Action):
    def apply(self, s_evolver) -> None:
        cards = []
        for _ in range(s_evolver.cnt):
            cards.append(s_evolver.st[0])
            s_evolver.st.delete(0)
        current_player = s_evolver.lp[s_evolver.i].hand
        s_evolver.lp[s_evolver.i] = Player(current_player.update(cards))

    def _description(self) -> str:
        return ''


ace_is_zero_cond = VariableCondition('ace', lambda ace: ace == 0, 'ace == 0')
heart_ix_in_hand_cond = CardInHand(Card(Suit.HEART, Value.IX))
cond1 = CondAnd(v(ace_is_zero_cond, heart_ix_in_hand_cond))

play_heart_ix = PlayCard(Card(Suit.HEART, Value.IX))
increase_player_index = ChangeVariable('i', lambda x: (x + 1) % 2, '(i + 1) % 2')
increase_mc = ChangeVariable('mc', lambda x: x + 1, 'mc + 1')
draw_card = DrawCards()
action1 = ActionList(v(play_heart_ix, increase_player_index, increase_mc))

move1 = Move(cond1, action1)
move2 = Move(VariableCondition('cnt', lambda x: True, None), draw_card)
