from typing import List, Iterable, Tuple, Optional

from pyrsistent import pvector
from pyrsistent.typing import PVector

from pharaoh.card import Deck
from pharaoh.game_state import GameState
from pharaoh.rule import Move, Rule


def create_game(ruleset: Iterable[Rule], deck: Deck, player_count: int) -> Tuple[GameState, PVector[Move]]:
    moves: List[Move] = []
    for rule in ruleset:
        moves.extend(rule.generate_moves(deck, player_count))
    return GameState.init_state(deck, player_count), pvector(moves)


def legal_moves(state: GameState, moves: Iterable[Move]) -> List[Move]:
    return [mv for mv in moves if mv.test(state)]


def finished(state: GameState) -> bool:
    return 1 == sum(x == -1 for x in state.lp_mc)


def winners(state: GameState) -> Optional[List[int]]:
    if not finished(state):
        return None
    order = list(zip(state.lp_mc, range(1, 10)))
    order.sort()
    return [x[1] for x in order]
