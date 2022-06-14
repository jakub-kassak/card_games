from __future__ import annotations
from dataclasses import dataclass, field
from math import sqrt, log
from random import choice as rand_choice
from typing import List, Optional, Iterable

from pharaoh.game import finished, legal_moves, winners
from pharaoh.game_state import GameState
from pharaoh.move import Move


class MonteCarloException(Exception):
    pass


@dataclass
class Node:
    state: GameState = field(repr=False)
    move: Optional[Move] = field(repr=False)
    parent: Optional[Node] = field(repr=False)
    children: List[Node] = field(default_factory=list, repr=False)
    visits: int = 0
    wins: int = 0

    UCT_MAX = 2 ** 64
    EXPL_CONST = sqrt(2)

    @property
    def _player_no(self) -> int:
        return (self.state.i - 1) % len(self.state.lp)

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    @property
    def is_terminal(self) -> bool:
        return finished(self.state)

    def _uct(self, child: Node) -> float:
        if child.is_terminal:
            return -1
        if child.visits == 0:
            return self.UCT_MAX
        return child.wins / child.visits + self.EXPL_CONST * sqrt(log(self.visits) / child.visits)

    def best_child(self) -> Node:
        return max(self.children, key=self._uct)

    def expand(self, children: Iterable[Node]) -> None:
        if not self.is_leaf:
            raise MonteCarloException("Can not expand - not a leaf node")
        if self.is_terminal:
            raise MonteCarloException("Can not expand - terminal node")
        self.children.extend(children)

    def update_score(self, result: Optional[List[int]]) -> None:
        self.visits += 1
        if result is None:
            return
        if result[0] == self._player_no:
            self.wins += 1
        elif result[-1] == self._player_no:
            self.wins -= 1


class MCTS:
    _root: Node
    _moves: Iterable[Move]
    ITERATIONS: int = 50
    DEPTH: int = 50

    def __init__(self, state: GameState, moves: Iterable[Move]):
        self._root = Node(state, None, None)
        self._moves = moves

    def search(self) -> Move:
        if len(legal_moves(self._root.state, self._moves)) == 1:
            return legal_moves(self._root.state, self._moves)[0]
        for i in range(self._root.visits, self.ITERATIONS):
            print(i, end=' ')
            leaf: Node = self._select_next()
            leaf.expand(Node(mv.apply(leaf.state), mv, leaf) for mv in legal_moves(leaf.state, self._moves))
            while len(leaf.children) == 1:
                leaf = leaf.children[0]
            simulation_result = self._random_playout(leaf)
            self._backpropagate(leaf, simulation_result)
        print()
        return self._best_move()

    def _select_next(self) -> Node:
        node: Node = self._root
        while not node.is_leaf:
            node = node.best_child()
        return node

    def _random_playout(self, leaf: Node) -> Optional[List[int]]:
        state: GameState = leaf.state
        cnt: int = 0
        while not finished(state) and cnt < self.DEPTH:
            cnt += 1
            move: Move = rand_choice(legal_moves(state, self._moves))
            state = move.apply(state)
        return winners(state)

    @staticmethod
    def _backpropagate(leaf: Node, result: Optional[List[int]]) -> None:
        node: Optional[Node] = leaf
        while node is not None:
            node.update_score(result)
            node = node.parent

    def _best_move(self) -> Move:
        best_node: Node = max(self._root.children, key=lambda node: node.visits)
        # print(f'best: {best_node.wins}, all: {list(node.wins for node in self._root.children)}')
        if best_node.move is None:
            raise MonteCarloException("Node's move is None")
        return best_node.move
