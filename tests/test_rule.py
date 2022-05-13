import unittest
from itertools import product
from typing import Iterable, List, cast

from pyrsistent import PBag, pbag, pvector

from pharaoh.card import Deck, Card, Suit, Value, GERMAN_CARDS_DECK, SUITS
from pharaoh.game_state import GameState, Hand
from pharaoh.move import Move
from pharaoh.rule import match_suit_rule, match_value_rule, play_over_rule, DrawRule


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.called = 0
        Move.mix_cards = self.shuffle_replacement

    def shuffle_replacement(self, l1: List[Card]) -> None:
        self.assertEqual(list, l1.__class__)
        self.called += 1

    @staticmethod
    def create_deck(values: Iterable[Value], suits: Iterable[Suit]):
        cards: PBag[Card] = pbag(Card(suit, val) for suit, val in product(suits, values))
        return Deck(cards, pvector(suits), pvector(values))

    def assert_no_change(self, state1: GameState, state2: GameState, *args: str):
        for key in args:
            self.assertEqual(state1[key], state2[key])

    def assert_change(self, state: GameState, **kwargs):
        for key, value in kwargs.items():
            self.assertEqual(value, state[key])

    def assert_change_in_lp_dp_mc(self, state1: GameState, state2: GameState, move: Move):
        if move.cards:
            self.assertEqual(len(state1.lp[state1.i]) - len(move.cards), len(state2.lp[state1.i]))
        self.assertFalse(any(c in state2.lp[state1.i] for c in move.cards))
        self.assertTrue(all(c in state2.lp[state1.i] for c in state1.lp[state1.i] if c not in move.cards))
        self.assertEqual(state1.mc + 1, state2.mc)
        if self.called == 0:
            self.assertEqual(state1.dp.extend(move.cards), state2.dp)

    def assert_and_make_legal_moves(self, count: int, state: GameState, moves: List[Move]) -> List[Move]:
        legal_moves: List[Move] = [mv for mv in moves if mv.test(state)]
        self.assertEqual(count, len(legal_moves))
        return legal_moves

    def test_match_suit_small(self):
        deck: Deck = self.create_deck([Value(val) for val in range(Value.VII, Value.UNDER)], [Suit.HEART])
        cards_list: List[Card] = list(deck.cards)
        cards_list.sort()
        moves: List[Move] = match_suit_rule.generate_moves(deck, 2)
        self.assertEqual(4, len(moves))
        self.assertTrue(all(len(mv.cards) == 1 for mv in moves))
        self.assertTrue(all(mv.suit == Suit.HEART for mv in moves))
        state1 = GameState(
            dp=cards_list[0:1],
            st=cards_list[1:2],
            lp=(Hand(cards_list[2:3]), Hand(cards_list[3:])),
            ace=0,
            suit=Suit.HEART,
            val=cards_list[0].value,
            cnt=1,
            i=0,
            mc=0,
            lp_mc=(-1, -1),
            deck_size=len(deck.cards)
        )
        legal_moves: List[Move] = self.assert_and_make_legal_moves(1, state1, moves)

        next_mv = legal_moves[0]
        state2 = next_mv.apply(state1)
        self.assert_no_change(state1, state2, 'st', 'ace', 'suit', 'cnt')
        self.assert_change_in_lp_dp_mc(state1, state2, next_mv)
        self.assert_change(
            state2,
            val=next_mv.cards[0].value,
            i=1,
            lp_mc=[1, -1]
        )

        s_evolver = state1.evolver()
        s_evolver.ace = 1
        s_evolver.cnt = 0
        self.assert_and_make_legal_moves(0, cast(GameState, s_evolver.persistent()), moves)

        s_evolver = state1.evolver()
        s_evolver.cnt = 3
        self.assert_and_make_legal_moves(0, cast(GameState, s_evolver.persistent()), moves)

    def test_match_suit_medium(self):
        deck: Deck = self.create_deck([Value(val) for val in (Value.VII, Value.IX, Value.ACE)],
                                      [Suit(suit) for suit in (Suit.HEART, Suit.BELL)])
        cards_list: List[Card] = list(deck.cards)
        # HEART < BELL
        cards_list.sort()
        moves: List[Move] = match_suit_rule.generate_moves(deck, 2)
        self.assertEqual(2 * (3 + 3), len(moves))
        self.assertTrue(all(1 <= len(mv.cards) <= 2 for mv in moves))

        self.assertTrue(all(mv.suit == Suit.HEART or mv.suit == Suit.BELL for mv in moves))
        top = cards_list[0]  # (HEART, VII)
        state1 = GameState(
            dp=[top],
            st=cards_list[1:2],  # (HEART, IX)
            lp=(Hand(cards_list[2:-1]),  # (HEART, ACE), (BELL, VII), (BELL, IX)
                Hand(cards_list[-1:])),  # (BELL, ACE)
            ace=0,
            suit=top.suit,
            val=top.value,
            cnt=1,
            i=0,
            mc=0,
            lp_mc=(-1, -1),
            deck_size=len(deck.cards)
        )
        legal_moves: List[Move] = self.assert_and_make_legal_moves(1, state1, moves)
        next_mv = legal_moves[0]  # PLAY (HEART, ACE)
        state2 = next_mv.apply(state1)
        self.assert_no_change(state1, state2, 'st', 'suit', 'lp_mc')
        self.assert_change_in_lp_dp_mc(state1, state2, next_mv)
        self.assert_change(
            state2,
            ace=1,
            val=next_mv.cards[0].value,
            i=1,
            cnt=0
        )
        self.assert_and_make_legal_moves(0, state2, moves)

        s_evolver = state1.evolver()
        s_evolver.lp = state1.lp.set(0, Hand(cards_list[2:-2] + [top]))  # (HEART, VII), (HEART, ACE), (BELL, VII)
        s_evolver.cnt = 3
        state1 = cast(GameState, s_evolver.persistent())
        legal_moves: List[Move] = self.assert_and_make_legal_moves(2, state1, moves)
        next_mv = next(mv for mv in legal_moves if len(mv.cards) > 1)  # PLAY (HEART, VII), (BELL, VII)
        state2 = next_mv.apply(state1)
        self.assert_no_change(state1, state2, 'ace', 'val', 'lp_mc')
        self.assert_change_in_lp_dp_mc(state1, state2, next_mv)
        self.assertEqual(next_mv.cards[-1], state2.dp[-1])
        self.assert_change(
            state2,
            suit=next_mv.cards[-1].suit,
            cnt=9,
            i=1
        )

    def test_match_suit_big(self):
        deck: Deck = GERMAN_CARDS_DECK
        cards_list: List[Card] = list(deck.cards)
        cards_list.sort()
        moves: List[Move] = match_suit_rule.generate_moves(deck, 4)
        self.assertEqual(4 * (8 * 3 * 2 * 1 + 8 * 3 * 2 + 8 * 3 + 8), len(moves))
        top = Card(Suit.HEART, Value.VIII)
        state1 = GameState(
            dp=[top],
            st=[Card(Suit.HEART, Value.KING), Card(Suit.HEART, Value.ACE), Card(Suit.ACORN, Value.UNDER),
                Card(Suit.ACORN, Value.OVER), Card(Suit.ACORN, Value.KING), Card(Suit.ACORN, Value.ACE),
                Card(Suit.LEAF, Value.VII), Card(Suit.LEAF, Value.VIII), Card(Suit.LEAF, Value.X),
                Card(Suit.LEAF, Value.UNDER), Card(Suit.LEAF, Value.OVER), Card(Suit.BELL, Value.VIII),
                Card(Suit.BELL, Value.X), Card(Suit.BELL, Value.UNDER), Card(Suit.BELL, Value.OVER),
                Card(Suit.BELL, Value.KING), Card(Suit.BELL, Value.ACE), Card(Suit.HEART, Value.OVER),
                Card(Suit.ACORN, Value.VIII)],
            lp=(Hand([Card(Suit.HEART, Value.VII), Card(Suit.ACORN, Value.VII)]),
                Hand([Card(Suit.LEAF, Value.KING), Card(Suit.LEAF, Value.ACE), Card(Suit.BELL, Value.VII)]),
                Hand([]),
                Hand([Card(Suit.HEART, Value.IX), Card(Suit.HEART, Value.X), Card(Suit.HEART, Value.UNDER),
                      Card(Suit.BELL, Value.IX), Card(Suit.LEAF, Value.IX), Card(Suit.ACORN, Value.IX),
                      Card(Suit.ACORN, Value.X)])),
            ace=0,
            suit=top.suit,
            val=top.value,
            cnt=1,
            i=3,
            mc=11,
            lp_mc=(-1, -1, 4, -1),
            deck_size=len(deck.cards)
        )
        # 3 + 1*3*2*1 + 1*3*2 + 1*3 + 1*1 = 19
        legal_moves1: List[Move] = self.assert_and_make_legal_moves(19, state1, moves)
        next_mv1: Move = next(mv for mv in legal_moves1 if len(mv.cards) == 4 and mv.cards[-1].suit == Suit.ACORN)
        state2: GameState = next_mv1.apply(state1)
        self.assert_no_change(state1, state2, 'st', 'ace', 'cnt', 'i', 'lp_mc')
        self.assert_change_in_lp_dp_mc(state1, state2, next_mv1)
        self.assert_change(
            state2,
            suit=Suit.ACORN,
            val=Value.IX
        )

        legal_moves2: List[Move] = self.assert_and_make_legal_moves(2, state2, moves)
        next_mv2: Move = next(mv for mv in legal_moves2 if len(mv.cards) == 2)
        state3: GameState = next_mv2.apply(state2)
        self.assert_no_change(state2, state3, 'st', 'ace', 'cnt', 'lp_mc')
        self.assert_change_in_lp_dp_mc(state2, state3, next_mv2)
        self.assert_change(
            state3,
            suit=Suit.HEART,
            val=Value.X,
            i=0
        )

        legal_moves3: List[Move] = self.assert_and_make_legal_moves(2, state3, moves)
        next_mv3: Move = next(mv for mv in legal_moves3 if len(mv.cards) == 2)
        state4: GameState = next_mv3.apply(state3)
        self.assert_no_change(state3, state4, 'st', 'ace', )
        self.assert_change_in_lp_dp_mc(state3, state4, next_mv3)
        self.assert_change(
            state4,
            suit=Suit.ACORN,
            val=Value.VII,
            cnt=6,
            i=1,
            lp_mc=[14, -1, 4, -1]
        )
        self.assert_and_make_legal_moves(0, state4, moves)

    def test_match_value_small(self):
        deck: Deck = self.create_deck([Value.VIII], SUITS)
        cards_list: List[Card] = list(deck.cards)
        cards_list.sort()
        moves: List[Move] = match_value_rule.generate_moves(deck, 2)
        # 4*3*2 + 4*3 + 4 = 64
        self.assertEqual(40, len(moves))
        top = Card(Suit.HEART, Value.VIII)
        state1 = GameState(
            dp=[top],
            st=[Card(Suit.BELL, Value.VIII)],
            lp=(Hand([Card(Suit.LEAF, Value.VIII)]), Hand([Card(Suit.ACORN, Value.VIII)])),
            ace=0,
            suit=top.suit,
            val=top.value,
            cnt=1,
            i=0,
            mc=0,
            lp_mc=(-1, -1),
            deck_size=len(deck.cards)
        )
        legal_moves: List[Move] = self.assert_and_make_legal_moves(1, state1, moves)
        next_mv = legal_moves[0]
        state2 = next_mv.apply(state1)
        self.assert_no_change(state1, state2, 'st', 'ace', 'val', 'cnt')
        # self.assert_change_in_lp(state1, state2, next_mv)
        self.assert_change(
            state2,
            dp=state1.dp.extend(next_mv.cards),
            suit=next_mv.cards[-1].suit,
            i=1,
            mc=1,
            lp_mc=[1, -1]
        )

    def test_match_value_medium(self):
        deck: Deck = self.create_deck([Value.VIII, Value.IX, Value.ACE], SUITS)
        cards_list: List[Card] = list(deck.cards)
        cards_list.sort()
        moves: List[Move] = match_value_rule.generate_moves(deck, 2)
        # 3 * (4*3*2 + 4*3 + 4) = 120
        self.assertEqual(120, len(moves))

        top = Card(Suit.HEART, Value.ACE)
        state1 = GameState(
            dp=[top],
            st=[Card(Suit.HEART, Value.VIII), Card(Suit.HEART, Value.IX), Card(Suit.BELL, Value.VIII),
                Card(Suit.LEAF, Value.VIII), Card(Suit.LEAF, Value.IX)],
            lp=(Hand([Card(Suit.LEAF, Value.ACE)]),
                Hand([Card(Suit.BELL, Value.ACE), Card(Suit.ACORN, Value.ACE), Card(Suit.ACORN, Value.VIII),
                      Card(Suit.ACORN, Value.IX), Card(Suit.BELL, Value.IX)])),
            ace=0,
            suit=top.suit,
            val=top.value,
            cnt=1,
            i=1,
            mc=0,
            lp_mc=(-1, -1),
            deck_size=len(deck.cards)
        )
        legal_moves1: List[Move] = self.assert_and_make_legal_moves(4, state1, moves)
        next_mv1 = next(mv for mv in legal_moves1 if len(mv.cards) == 2 and mv.cards[-1].suit == Suit.ACORN)
        state2 = next_mv1.apply(state1)
        self.assert_no_change(state1, state2, 'st', 'val', 'lp_mc')
        self.assert_change_in_lp_dp_mc(state1, state2, next_mv1)
        self.assert_change(
            state2,
            ace=2,
            suit=next_mv1.suit,
            cnt=0,
            i=0,
        )

        s_evolver = state1.evolver()
        s_evolver.ace = 1
        s_evolver.cnt = 0
        state1b = cast(GameState, s_evolver.persistent())
        legal_moves1b: List[Move] = self.assert_and_make_legal_moves(4, state1b, moves)
        next_mv1b = next(mv for mv in legal_moves1b if len(mv.cards) == 2 and mv.cards[-1].suit == Suit.ACORN)
        state2b = next_mv1b.apply(state1b)
        self.assert_no_change(state2, state2b, 'st', 'dp', 'ace', 'suit', 'val', 'cnt', 'i', 'mc', 'lp_mc')
        self.assert_change_in_lp_dp_mc(state1, state2b, next_mv1b)

        legal_moves2: List[Move] = self.assert_and_make_legal_moves(1, state2, moves)
        next_mv2: Move = legal_moves2[0]
        state3: GameState = next_mv2.apply(state2)
        self.assert_no_change(state2, state3, 'st', 'val', 'ace', 'cnt')
        self.assert_change_in_lp_dp_mc(state1, state2, next_mv1)
        self.assert_change(
            state3,
            suit=next_mv2.suit,
            cnt=0,
            i=1,
            lp_mc=[2, -1]
        )
        self.assert_and_make_legal_moves(0, state3, moves)

    def test_play_over_small(self):
        deck: Deck = self.create_deck([Value.VIII, Value.OVER], [Suit.HEART, Suit.BELL])
        cards_list: List[Card] = list(deck.cards)
        cards_list.sort()
        moves: List[Move] = play_over_rule.generate_moves(deck, 2)
        self.assertEqual(8, len(moves))

        top = Card(Suit.HEART, Value.VIII)
        state1 = GameState(
            dp=[top],
            st=[Card(Suit.HEART, Value.OVER)],
            lp=(Hand([Card(Suit.BELL, Value.OVER)]),
                Hand([Card(Suit.BELL, Value.VIII)])),
            ace=0,
            suit=top.suit,
            val=top.value,
            cnt=1,
            i=0,
            mc=0,
            lp_mc=(-1, -1),
            deck_size=len(deck.cards)
        )
        legal_moves1: List[Move] = self.assert_and_make_legal_moves(2, state1, moves)
        next_mv1 = next(mv for mv in legal_moves1 if mv.suit == Suit.BELL)
        state2 = next_mv1.apply(state1)
        self.assert_no_change(state1, state2, 'st', 'ace', 'cnt')
        self.assert_change_in_lp_dp_mc(state1, state2, next_mv1)
        self.assert_change(
            state2,
            suit=next_mv1.suit,
            val=next_mv1.cards[0].value,
            i=1,
            lp_mc=[1, -1]
        )
        self.assert_and_make_legal_moves(0, state2, moves)

    def test_play_over_medium(self):
        deck: Deck = self.create_deck([Value.VIII, Value.OVER], SUITS)
        cards_list: List[Card] = list(deck.cards)
        cards_list.sort()
        moves: List[Move] = play_over_rule.generate_moves(deck, 2)
        # 4 * (4*3*2*1 + 4*3*2 + 4*3 + 4) = 256
        self.assertEqual(256, len(moves))

        top = Card(Suit.HEART, Value.VIII)
        state1 = GameState(
            dp=[top],
            st=[Card(Suit.ACORN, Value.VIII)],
            lp=(Hand([Card(Suit.LEAF, Value.OVER), Card(Suit.BELL, Value.OVER), Card(Suit.ACORN, Value.OVER),
                      Card(Suit.BELL, Value.VIII)]),
                Hand([Card(Suit.HEART, Value.OVER), Card(Suit.LEAF, Value.VIII)])),
            ace=0,
            suit=top.suit,
            val=top.value,
            cnt=1,
            i=0,
            mc=0,
            lp_mc=(-1, -1),
            deck_size=len(deck.cards)
        )
        # 4 * (3*2*1 + 3*2 + 3) = 60
        legal_moves1: List[Move] = self.assert_and_make_legal_moves(60, state1, moves)
        next_mv1 = next(mv for mv in legal_moves1 if len(mv.cards) == 3 and mv.suit == Suit.HEART)
        state2 = next_mv1.apply(state1)
        self.assert_no_change(state1, state2, 'st', 'ace', 'suit', 'cnt', 'lp_mc')
        self.assert_change_in_lp_dp_mc(state1, state2, next_mv1)
        self.assert_change(
            state2,
            val=Value.OVER,
            i=1,
        )

        legal_moves2: List[Move] = self.assert_and_make_legal_moves(4, state2, moves)
        next_mv2: Move = legal_moves2[0]
        state3: GameState = next_mv2.apply(state2)
        self.assert_no_change(state1, state2, 'st', 'ace', 'cnt', 'lp_mc')
        self.assert_change_in_lp_dp_mc(state1, state2, next_mv1)
        self.assert_change(
            state3,
            suit=next_mv2.suit,
            cnt=1,
            i=0,
            lp_mc=[-1, -1]
        )
        self.assert_and_make_legal_moves(0, state3, moves)

    def test_draw_big(self):
        deck: Deck = GERMAN_CARDS_DECK
        cards_list: List[Card] = list(deck.cards)
        cards_list.sort()
        moves: List[Move] = DrawRule().generate_moves(deck, 4)
        self.assertEqual(3, len(moves))
        top = Card(Suit.HEART, Value.ACE)
        state1 = GameState(
            dp=[Card(Suit.LEAF, Value.ACE), Card(Suit.BELL, Value.ACE), top],
            st=[Card(Suit.HEART, Value.KING), Card(Suit.HEART, Value.VIII), Card(Suit.ACORN, Value.UNDER),
                Card(Suit.ACORN, Value.OVER), Card(Suit.ACORN, Value.KING), Card(Suit.ACORN, Value.ACE),
                Card(Suit.LEAF, Value.VII), Card(Suit.LEAF, Value.VIII), Card(Suit.LEAF, Value.X),
                Card(Suit.LEAF, Value.UNDER), Card(Suit.LEAF, Value.OVER), Card(Suit.BELL, Value.VIII),
                Card(Suit.BELL, Value.X), Card(Suit.BELL, Value.UNDER), Card(Suit.BELL, Value.OVER),
                Card(Suit.BELL, Value.KING), Card(Suit.HEART, Value.OVER),
                Card(Suit.ACORN, Value.VIII)],
            lp=(Hand([Card(Suit.HEART, Value.VII), Card(Suit.ACORN, Value.VII)]),
                Hand([Card(Suit.LEAF, Value.KING), Card(Suit.BELL, Value.VII)]),
                Hand([]),
                Hand([Card(Suit.HEART, Value.IX), Card(Suit.HEART, Value.X), Card(Suit.HEART, Value.UNDER),
                      Card(Suit.BELL, Value.IX), Card(Suit.LEAF, Value.IX), Card(Suit.ACORN, Value.IX),
                      Card(Suit.ACORN, Value.X)])),
            ace=3,
            suit=top.suit,
            val=top.value,
            cnt=0,
            i=3,
            mc=11,
            lp_mc=(-1, -1, 4, -1),
            deck_size=len(deck.cards)
        )
        legal_moves1: List[Move] = self.assert_and_make_legal_moves(1, state1, moves)
        next_mv1 = legal_moves1[0]
        state2 = next_mv1.apply(state1)
        self.assert_no_change(state1, state2, 'dp', 'st', 'suit', 'val', 'cnt', 'lp_mc')
        self.assert_change_in_lp_dp_mc(state1, state2, next_mv1)
        self.assert_change(
            state2,
            ace=state1.ace - 1,
            i=0,
        )

        legal_moves2: List[Move] = self.assert_and_make_legal_moves(1, state2, moves)
        next_mv2 = legal_moves2[0]
        state3 = next_mv2.apply(state2)
        self.assert_no_change(state2, state3, 'dp', 'st', 'suit', 'val', 'cnt', 'lp_mc')
        self.assert_change_in_lp_dp_mc(state2, state3, next_mv1)
        self.assert_change(
            state3,
            ace=state2.ace - 1,
            i=1,
        )

        legal_moves3: List[Move] = self.assert_and_make_legal_moves(1, state3, moves)
        next_mv3 = legal_moves3[0]
        state4 = next_mv3.apply(state3)
        self.assert_no_change(state3, state4, 'dp', 'st', 'suit', 'val', 'lp_mc')
        self.assert_change_in_lp_dp_mc(state3, state4, next_mv1)
        self.assert_change(
            state4,
            ace=state3.ace - 1,
            i=3,
            cnt=1
        )

        legal_moves4: List[Move] = self.assert_and_make_legal_moves(1, state4, moves)
        next_mv4 = legal_moves4[0]
        state5 = next_mv4.apply(state4)
        self.assert_no_change(state4, state5, 'dp', 'ace', 'suit', 'val', 'cnt', 'lp_mc')
        self.assert_change_in_lp_dp_mc(state4, state5, next_mv1)
        self.assert_change(
            state5,
            st=state4.st.delete(0, state4.cnt),
            i=0
        )
        self.assertTrue(state4.st[0] in state5.lp[state4.i])

        top = Card(Suit.LEAF, Value.VII)
        state1 = GameState(
            dp=[Card(Suit.HEART, Value.VII), Card(Suit.ACORN, Value.VII), top],
            st=[Card(Suit.HEART, Value.KING), Card(Suit.HEART, Value.VIII), Card(Suit.ACORN, Value.UNDER),
                Card(Suit.ACORN, Value.OVER), Card(Suit.ACORN, Value.KING), Card(Suit.ACORN, Value.ACE),
                Card(Suit.LEAF, Value.VIII), Card(Suit.LEAF, Value.X), Card(Suit.HEART, Value.ACE),
                Card(Suit.LEAF, Value.UNDER), Card(Suit.LEAF, Value.OVER), Card(Suit.BELL, Value.VIII),
                Card(Suit.BELL, Value.X), Card(Suit.BELL, Value.UNDER), Card(Suit.BELL, Value.OVER),
                Card(Suit.BELL, Value.KING), Card(Suit.HEART, Value.OVER),
                Card(Suit.ACORN, Value.VIII)],
            lp=(Hand([Card(Suit.LEAF, Value.ACE), Card(Suit.BELL, Value.ACE)]),
                Hand([Card(Suit.LEAF, Value.KING), Card(Suit.BELL, Value.VII)]),
                Hand([]),
                Hand([Card(Suit.HEART, Value.IX), Card(Suit.HEART, Value.X), Card(Suit.HEART, Value.UNDER),
                      Card(Suit.BELL, Value.IX), Card(Suit.LEAF, Value.IX), Card(Suit.ACORN, Value.IX),
                      Card(Suit.ACORN, Value.X)])),
            ace=0,
            suit=top.suit,
            val=top.value,
            cnt=9,
            i=3,
            mc=11,
            lp_mc=(-1, -1, 4, -1),
            deck_size=len(deck.cards)
        )

        legal_moves1: List[Move] = self.assert_and_make_legal_moves(1, state1, moves)
        next_mv1 = legal_moves1[0]
        state2 = next_mv1.apply(state1)
        self.assert_no_change(state1, state2, 'dp', 'ace', 'suit', 'val', 'lp_mc')
        self.assert_change_in_lp_dp_mc(state1, state2, next_mv1)
        self.assert_change(
            state2,
            st=state1.st.delete(0, state1.cnt),
            cnt=1,
            i=0,
        )
        self.assertTrue(all(c in state2.lp[state1.i] for c in state1.st[0:state1.cnt]))


if __name__ == '__main__':
    unittest.main()
