import itertools
import random
from collections import defaultdict
from collections import deque
from typing import List, Callable, Dict, Optional, Tuple, Iterable, Deque

from pyrsistent.typing import PVector

from pharaoh.card import Value, Card, Suit
from pharaoh.game_state import GameState
from pharaoh.mcts import MCTS
from pharaoh.move import Move


class Player:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def play(self, state: GameState, legal_moves: List[Move]) -> Move:
        raise NotImplementedError

    def inform(self, move: Move) -> None:
        pass

    def __repr__(self):
        return f'{self.__class__.__name__}(name={self.name})'


class RandomPlayer(Player):
    def play(self, state: GameState, legal_moves: List[Move]) -> Move:
        return random.choice(legal_moves)


class BiggestTuplePlayer(Player):
    def play(self, state: GameState, legal_moves: List[Move]) -> Move:
        return max(legal_moves, key=lambda m: len(m.cards))


class SmallestTuplePlayer(Player):
    def play(self, state: GameState, legal_moves: List[Move]) -> Move:
        if len(legal_moves) == 1:
            return legal_moves[0]
        legal_moves = [m for m in legal_moves if len(m.cards)]
        values: Dict[Value, int] = defaultdict(int)
        for move in legal_moves:
            size: int = len(move.cards)
            for c in move.cards:
                values[c.value] = max(values[c.value], size)
        move = min(legal_moves, key=lambda mv: (values[mv.cards[0].value], -len(mv.cards)))
        return move


class HumanPlayer(Player):
    def __init__(self, name: str, load_move: Callable[[int], Tuple[PVector[Card], Optional[Suit]]]):
        super().__init__(name)
        self._load_move = load_move

    def play(self, state: GameState, legal_moves: List[Move]) -> Move:
        for i in itertools.count():
            cards_list, suit = self._load_move(i)
            moves2 = list(mv for mv in legal_moves if mv.cards == cards_list and mv.suit == suit)
            if moves2:
                return moves2[0]
        raise Exception()


class MCTSPlayer(Player):
    def __init__(self, name: str, moves: Iterable[Move], init_state: GameState):
        super().__init__(name)
        self._moves = moves
        self._unprocessed_moves: Deque[Move] = deque()
        self._mcts = MCTS(init_state, self._moves)
        self._mcts.search()

    def play(self, state: GameState, legal_moves: Iterable[Move]) -> Move:
        while self._unprocessed_moves and (move := self._unprocessed_moves.pop()):
            if not self._mcts.advance(move):
                break
        if self._unprocessed_moves:
            self._unprocessed_moves.clear()
            self._mcts.set_root(state)
        return self._mcts.search()

    def inform(self, move: Move) -> None:
        self._unprocessed_moves.appendleft(move)
