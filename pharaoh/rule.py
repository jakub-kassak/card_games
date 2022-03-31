from __future__ import annotations

from typing import List, Callable, Union, Optional, Any

from pyrsistent import v
from pyrsistent.typing import PVector

from pharaoh.card import Card, Value, Suit
from pharaoh.game_state import GameState, Player

ConditionCallable = Callable[[Union[PVector[Card], PVector[Any], int, Suit, Value]], bool]
ActionCallable = Union[Callable[[Suit], Suit], Callable[[Value], Value], Callable[[int], int]]


class Rule:
    def generate_moves(self, deck: List[Card]) -> List[Move]:
        raise NotImplementedError


class Move:
    def __init__(self, cond: Condition, actions: PVector[Action]):
        self._cond = cond
        self._actions = actions

    def test(self, state: GameState) -> bool:
        return self._cond.test(state)

    class ConditionUnsatisfied(Exception):
        pass

    def apply(self, state: GameState):
        if not self.test(state):
            raise self.ConditionUnsatisfied

        state_evolver = state.evolver()
        for a in self._actions:
            a.apply(state_evolver)
        return state_evolver.persistent()

    def __repr__(self) -> str:
        return f'Move(cond={self._cond}, actions={self._actions})'


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
        return self._card in state.lp[state.i].hand

    def _description(self) -> str:
        return repr(self._card)


class Action:
    def apply(self, s_evolver) -> None:
        raise NotImplementedError

    def _description(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._description()})'


class PlayCard(Action):
    def __init__(self, card: Card):
        self._card = card

    def apply(self, s_evolver) -> None:
        current_player = s_evolver.lp[s_evolver.i].hand
        s_evolver.lp = s_evolver.lp.set(s_evolver.i, Player(current_player.remove(self._card)))
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
        cards = s_evolver.st[:s_evolver.cnt]
        s_evolver.st = s_evolver.st.delete(0, s_evolver.cnt)
        current_player = s_evolver.lp[s_evolver.i].hand
        current_player = Player(current_player.update(cards))
        s_evolver.lp = s_evolver.lp.set(s_evolver.i, current_player)

    def _description(self) -> str:
        return ''


ace_is_zero_cond = VariableCondition('ace', lambda ace: ace == 0, 'ace == 0')
heart_ix_in_hand_cond = CardInHand(Card(Suit.HEART, Value.IX))
cond1 = CondAnd(v(ace_is_zero_cond, heart_ix_in_hand_cond))

play_heart_ix = PlayCard(Card(Suit.HEART, Value.IX))
increase_player_index = ChangeVariable('i', lambda x: (x + 1) % 2, '(i + 1) % 2')
increase_mc = ChangeVariable('mc', lambda x: x + 1, 'mc + 1')
draw_card = DrawCards()

move1 = Move(cond1, v(play_heart_ix, increase_player_index, increase_mc))
move2 = Move(VariableCondition('cnt', lambda x: True, None), v(draw_card))
