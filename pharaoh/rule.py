from __future__ import annotations

from typing import List

from pharaoh.card import Deck
from pharaoh.move import Move


class Rule:
    def generate_moves(self, deck: Deck) -> List[Move]:
        raise NotImplementedError
