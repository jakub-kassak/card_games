from __future__ import annotations

from random import shuffle
from typing import Callable, Union, Optional, Any, Iterable, List, cast

from pyrsistent import v, pbag, pvector
from pyrsistent.typing import PVector

from pharaoh.card import Card, Value, Suit
from pharaoh.game_state import GameState

ConditionCallable = Callable[[Union[PVector[Card], PVector[Any], int, Suit, Value]], bool]
ActionCallable = Union[Callable[[Suit], Suit], Callable[[Value], Value], Callable[[int], int]]


class MoveException(Exception):
    pass


class Move:
    def __init__(self, conditions: Iterable[Condition], actions: Iterable[Action],
                 mix_cards: Callable[[List[Card]], None] = shuffle):
        self._mix_cards = mix_cards
        self._conds = pvector(conditions)
        self._actions = pvector(actions)
        for a in actions:
            if isinstance(a, PlayCards):
                self._cards: PVector[Card] = a.cards
                break
        else:
            self._cards: PVector[Card] = pvector()

    @property
    def cards(self) -> PVector[Card]:
        return self._cards

    def test(self, state: GameState) -> bool:
        return all(c.test(state) for c in self._conds)

    def apply(self, state: GameState) -> GameState:
        if not self.test(state):
            raise MoveException()
        s_evolver = state.evolver()
        new_state: GameState = cast(GameState, s_evolver)
        for a in self._actions:
            a.apply(new_state)
        while new_state.lp_mc[new_state.i] != -1:
            new_state.i = (new_state.i + 1) % len(new_state.lp)
        if new_state.cnt > len(new_state.st):
            cards: List[Card] = list(new_state.dp[0:-1])
            self._mix_cards(cards)
            new_state.st = new_state.st.extend(cards)
            new_state.dp = new_state.dp.delete(0, -1)
        if len(new_state.lp[state.i]) == 0:
            new_state.lp_mc = new_state.lp_mc.set(state.i, new_state.mc)
        return cast(GameState, s_evolver.persistent())

    def __repr__(self) -> str:
        return f'Move(cond={self._conds}, actions={self._actions})'


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
        return self._card in state.lp[state.i]

    def _description(self) -> str:
        return repr(self._card)


class Action:
    def apply(self, s_evolver) -> None:
        raise NotImplementedError

    def _description(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._description()})'


class PlayCards(Action):
    def __init__(self, cards: PVector[Card]):
        self._cards = cards

    @property
    def cards(self) -> PVector[Card]:
        return self._cards

    def apply(self, s_evolver) -> None:
        current_hand = s_evolver.lp[s_evolver.i] - pbag(self._cards)
        s_evolver.lp = s_evolver.lp.set(s_evolver.i, current_hand)
        s_evolver.dp = s_evolver.dp.extend(self._cards)

    def _description(self) -> str:
        return repr(', '.join(map(repr, self._cards)))


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
        current_player = s_evolver.lp[s_evolver.i]
        current_player = current_player.update(cards)
        s_evolver.lp = s_evolver.lp.set(s_evolver.i, current_player)

    def _description(self) -> str:
        return ''


ace_is_zero_cond = VariableCondition('ace', lambda ace: ace == 0, 'ace == 0')
heart_ix_in_hand_cond = CardInHand(Card(Suit.HEART, Value.IX))
cond1 = CondAnd(v(ace_is_zero_cond, heart_ix_in_hand_cond))

play_heart_ix_x = PlayCards(v(Card(Suit.HEART, Value.X), Card(Suit.HEART, Value.IX)))
increase_player_index = ChangeVariable('i', lambda x: (x + 1) % 2, '(i + 1) % 2')
increase_mc = ChangeVariable('mc', lambda x: x + 1, 'mc + 1')
draw_card = DrawCards()

move1 = Move(v(cond1), v(play_heart_ix_x, increase_player_index, increase_mc))
move2 = Move(v(VariableCondition('cnt', lambda x: True, None)), v(draw_card))
