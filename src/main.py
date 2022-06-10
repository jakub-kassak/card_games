from random import shuffle
from typing import Tuple, List, Optional, Dict, Iterable

import yaml
from pyrsistent import pvector
from pyrsistent.typing import PVector

from pharaoh.card import GERMAN_CARDS_DECK, Card, Suit, Value, symbols
from pharaoh.game import finished, legal_moves, create_game, winners
from pharaoh.game_state import GameState
from pharaoh.move import Move
from pharaoh.player import Player, RandomPlayer, BiggestTuplePlayer, SmallestTuplePlayer, HumanPlayer, MCTSPlayer
from pharaoh.rule import standard_ruleset


CURSOR: str = '\033[32m>>>\033[m '


class ConsoleGameException(Exception):
    pass


class EndGame(Exception):
    pass


class ConsoleGame:
    def __init__(self, config: str = "config/config.yml"):
        self._players: List[Player] = []
        self._states: List[GameState] = []
        self._allowed_moves: Iterable[Move] = []
        self._moves_history: List[Move] = []
        self._config_file = config

    @property
    def _current_state(self) -> GameState:
        return self._states[-1]

    @property
    def _current_player(self) -> Player:
        return self._players[self._current_state.i]

    @property
    def _top_card(self):
        return self._current_state.dp[-1]

    @staticmethod
    def _print_cards(cards: List[Card]):
        print('Your cards are:')
        for j in range(len(cards)):
            print(f'\t[{j}] {cards[j]}')

    def _print_top_card(self):
        msg: str = f'top card: {self._top_card} '
        if self._top_card.value == Value.OVER and self._current_state.suit != self._top_card.suit:
            msg += "changed to: " + str(self._current_state.suit)
        elif self._top_card.value == Value.VII and self._current_state.cnt > 1:
            msg += "to draw: " + str(self._current_state.cnt)
        elif self._top_card.value == Value.ACE and self._current_state.ace != 0:
            msg += f"valid for next {self._current_state.ace} moves"
        print(msg)

    @staticmethod
    def _load_suit_from_console() -> Suit:
        table: Dict[str, Suit] = {
            "bell": Suit.BELL,
            "heart": Suit.HEART,
            "acorn": Suit.ACORN,
            "leaf": Suit.LEAF
        }
        while True:
            suit = input(f"Enter suit to which you want to change:\n{CURSOR}")
            if suit in table:
                return table[suit]
            elif suit == "help":
                for suit_in, suit_out in table.items():
                    print(f"enter '{suit_in}' for {repr(suit_out)}")
            else:
                print("unknown suit, enter 'help' for help")

    def _load_move_from_console(self, cnt: int) -> Tuple[PVector[Card], Optional[Suit]]:
        i = self._states[-1].i
        hand: List[Card] = list(self._states[-1].lp[i])
        hand.sort(key=lambda card: (card.value, card.suit))
        if cnt == 0:
            print("It's your turn.")
            self._print_cards(hand)
        else:
            print('Entered combination is invalid, enter valid combination of cards.')
        while True:
            command = input(CURSOR).split()
            if len(command) == 0:
                continue
            elif command[0] == 'play':
                try:
                    card_nums = [int(x) for x in command[1:]]
                    cards_list: PVector[Card] = pvector(hand[i] for i in card_nums)
                    if cards_list[-1].value == Value.OVER:
                        return cards_list, self._load_suit_from_console()
                    else:
                        return cards_list, cards_list[-1].suit
                except ValueError:
                    print('you have entered incorrect numbers')
                except IndexError:
                    print('please enter at least one number')
            elif command[0] == "draw" or command[0] == "skip":
                return pvector(), None
            elif command[0] == "enemies":
                player_stats = (f'{self._players[j].name}: {len(self._current_state.lp[j])}'
                                for j in range(len(self._players)))
                print(", ".join(player_stats))
            elif command[0] == "top":
                self._print_top_card()
            elif command[0] == "hand" or command[0] == "cards":
                self._print_cards(hand)
            elif command[0] == "help":
                pass
            elif command[0] == 'end':
                raise EndGame("Player wants to end the game")
            else:
                print("unknown command")

    def start_game(self):
        self._players = []
        with open(self._config_file, "r", encoding='utf8') as f:
            config = yaml.load(f.read(), Loader=yaml.Loader)
        if 'symbols' in config:
            symbols.update(config["symbols"])
        names = config["players"]["names"]
        types = config["players"]["types"]
        init_cards: int = config["init_cards"]
        state, self._allowed_moves = create_game(standard_ruleset, GERMAN_CARDS_DECK, len(names), init_cards)
        self._states = [state]
        self._moves_history = []
        for name, type_ in zip(names, types):
            if len(self._players) > 6:
                raise ConsoleGameException("too many players")
            if type_ == 'human':
                self._players.append(HumanPlayer(name, self._load_move_from_console))
            elif type_ == 'random':
                self._players.append(RandomPlayer(name))
            elif type_ == 'ai1':
                self._players.append(BiggestTuplePlayer(name))
            elif type_ == 'ai2':
                self._players.append(SmallestTuplePlayer(name))
            elif type_ == 'mcts':
                self._players.append(MCTSPlayer(name, self._allowed_moves, state))
            else:
                raise ConsoleGameException("Unsupported player type")
        if len(self._players) < 2:
            raise ConsoleGameException("not enough players")

    def play_game(self) -> Tuple[List[GameState], List[Move]]:
        self._print_top_card()
        while not finished(self._current_state):
            legal: List[Move] = legal_moves(self._current_state, self._allowed_moves)
            next_move: Move = self._current_player.play(self._current_state, legal)
            self._moves_history.append(next_move)
            name: str = self._current_player.name
            if next_move.cards == pvector():
                if self._current_state.cnt == 0:
                    print(f'{name}: SKIP')
                else:
                    print(f'{name}: DRAW {self._current_state.cnt}')
            elif next_move.cards[-1].value == Value.OVER:
                print(f'{name}: PLAY {", ".join(str(c) for c in next_move.cards)} CHANGES TO {next_move.suit}')
            else:
                print(f'{name}: PLAY {", ".join(str(c) for c in next_move.cards)}')
            i = self._current_state.i
            self._states.append(next_move.apply(self._current_state))
            for player in self._players:
                player.inform(next_move)
            if len(self._current_state.lp[i]) == 0:
                print(f'{name} finished.')
        return self._states, self._moves_history

    def game_results(self):
        result = winners(self._current_state)
        print("Result:")
        for position, index in zip(range(10), result):
            print(f'[{position}] {self._players[index].name}')

    def main(self):
        print("## CONSOLE PHARAOH ##")
        print(f"enter your commands behind '{CURSOR[:-1]}'")
        while True:
            command = input(CURSOR).split()
            if len(command) == 0:
                continue
            elif command[0] == 'play':
                self.start_game()
                try:
                    self.play_game()
                    self.game_results()
                except EndGame:
                    pass
            elif command[0] == 'help':
                print('enter "play", to start the game')
                print('enter "end", to end the game')
                print('enter "rules", to view game rules')
            elif command[0] == 'rules':
                pass
            elif command[0] == 'end':
                return
            else:
                print("unknown command")


def play_game(state: GameState, players: PVector[Player], moves: PVector[Move]) \
        -> Tuple[List[GameState], List[Move]]:
    if len(players) != len(state.lp):
        raise Exception('Incompatible game state: len(players) != len(state.lp)')

    state_history: List[GameState] = []
    move_history: List[Move] = []
    while not finished(state):
        state_history.append(state)
        legal: List[Move] = legal_moves(state, moves)
        next_move: Move = players[state.i].play(state_history[-1], legal)
        move_history.append(next_move)
        state = next_move.apply(state)
        if state.mc == 1000:
            break
    state_history.append(state)
    return state_history, move_history


def main():
    n = 5
    players: PVector[Player] = pvector(RandomPlayer(str(i)) for i in range(5))
    state, moves = create_game(standard_ruleset, GERMAN_CARDS_DECK, n, 5)
    state_history, move_history = play_game(state, players, moves)
    for i in range(len(state_history)):
        print(state_history[i], '\t', move_history[i] if i < len(move_history) else None)
    print(winners(state_history[-1]))


def main2():
    n = 6
    players: PVector[Player] = pvector(RandomPlayer('random' + str(i)) for i in range(2))
    players = players.extend(BiggestTuplePlayer('biggest' + str(i)) for i in range(2))
    players = players.extend(SmallestTuplePlayer('smallest' + str(i)) for i in range(2))

    stats = [0] * n
    length = 0
    m = 200
    players_numbers = [(players[i], i) for i in range(n)]
    for j in range(m):
        if j > 0 and j % 10 == 0:
            print(j)
        shuffle(players_numbers)
        positions = [0] * n
        for i in range(n):
            player, number = players_numbers[i]
            positions[i] = number
        players2 = pvector(x[0] for x in players_numbers)
        state, moves = create_game(standard_ruleset, GERMAN_CARDS_DECK, n, 5)
        state_history, move_history = play_game(state, players2, moves)
        result = [x - 1 for x in winners(state_history[-1])]
        for i in range(n):
            stats[positions[result[i]]] += i
        length += state_history[-1].mc
    print(stats)
    print(length / m / n)


def main3():
    game: ConsoleGame = ConsoleGame()
    game.main()


if __name__ == '__main__':
    main3()
