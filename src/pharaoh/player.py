import itertools
import random
from collections import defaultdict
from typing import List, Callable, Dict, Optional, Tuple

from pyrsistent.typing import PVector

from pharaoh.card import Value, Card, Suit
from pharaoh.game_state import GameState
from pharaoh.move import Move


class Player:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def play(self, state: GameState, legal_moves: List[Move]) -> Move:
        raise NotImplementedError

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
            return moves2[0]
        raise Exception()
