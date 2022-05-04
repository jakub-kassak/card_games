import contextlib
import os
import unittest

from main import ConsoleGame
from pharaoh.card import Value
from pharaoh.move import Move


class TestGame(unittest.TestCase):
    def prepare_test(self):
        game = ConsoleGame("./test_config.yml")
        Move.mix_cards = self.shuffle_replacement
        with open(os.devnull, 'w', encoding='UTF-8') as devnull:
            with contextlib.redirect_stdout(devnull):
                game.start_game()
                self.states, self.moves = game.play_game()
        self.first_state = self.states[0]

    def shuffle_replacement(self, *arg, **kwargs):
        pass

    @property
    def history_iterator(self):
        return zip(self.states[:-1], self.states[1:], self.moves)

    def assert_correct_move_saved(self):
        self.assertEqual(len(self.states), len(self.moves) + 1)
        for prev_state, next_state, move in self.history_iterator:
            self.assertTrue(move.test(prev_state))
            self.assertEqual(str(next_state), str(move.apply(prev_state)))

    def assert_cards_were_allowed(self):
        for prev_state, next_state, move in filter(lambda x: x[2].cards, self.history_iterator):
            top = prev_state.dp[-1]
            new = move.cards[0]
            if new.value == Value.OVER:
                pass
            elif top.value == Value.OVER:
                self.assertTrue(prev_state.suit == new.suit)
            else:
                self.assertTrue(top.value == new.value or top.suit == new.suit)
                self.assertTrue(top.suit == prev_state.suit)

    def assert_drawing(self):
        for prev_state, next_state, move in filter(lambda x: not x[2].cards, self.history_iterator):
            i = prev_state.i
            self.assertTrue(len(prev_state.lp[i]) + prev_state.cnt == len(next_state.lp[i])
                            or len(next_state.dp) == 1)
            self.assertTrue(next_state.cnt == 1 or next_state.ace > 0)

    def assert_cards_in_hand(self):
        for prev_state, next_state, move in filter(lambda x: x[2].cards, self.history_iterator):
            i = prev_state.i
            self.assertTrue(all(c in prev_state.lp[i] for c in move.cards))
            self.assertFalse(any(c in next_state.lp[i] for c in move.cards))
            top_dp_cards = next_state.dp[-len(move.cards):]
            self.assertTrue(move.cards == top_dp_cards or len(next_state.dp) < len(move.cards) and
                            all(c in top_dp_cards or c in next_state.st for c in move.cards))

    def assert_ace(self):
        for prev_state, next_state, move in self.history_iterator:
            n = len(move.cards)
            if n == 0 or move.cards[0].value != Value.ACE:
                continue
            if n == 4:
                self.assertEqual(1, next_state.cnt)
                self.assertEqual(0, next_state.ace)
            else:
                self.assertEqual(0, next_state.cnt)
                self.assertEqual(n + max(prev_state.ace - 1, 0), next_state.ace)

    def assert_vii(self):
        for prev_state, next_state, move in self.history_iterator:
            n = len(move.cards)
            if n == 0 or move.cards[0].value != Value.VII:
                continue
            if prev_state.cnt == 1:
                self.assertEqual(3 * n, next_state.cnt)
            else:
                self.assertEqual(prev_state.cnt + 3 * n, next_state.cnt)

    def test_game(self):
        for i in range(10):
            with self.subTest(f"run {i}", i=i):
                self.prepare_test()
                self.assert_correct_move_saved()
                self.assert_drawing()
                self.assert_cards_in_hand()
                self.assert_ace()
                self.assert_vii()


if __name__ == '__main__':
    unittest.main()
