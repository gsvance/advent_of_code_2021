from collections.abc import Iterator
from enum import Enum
import functools
import pathlib
import sys
from typing import Final, NamedTuple, Self


def modulo_from_1(numerator: int, denominator: int) -> int:
    # Just like modulo, but return a value from the set {1, ..., denominator}
    # instead of from the set {0, ..., denominator-1}.
    return (numerator - 1) % denominator + 1


class Player(Enum):
    ONE = 1
    TWO = 2

    def get_opponent(self) -> Self:
        value = modulo_from_1(self.value + 1, len(self.__class__))
        return self.__class__(value)


class Space(Enum):
    SPACE_01 = 1
    SPACE_02 = 2
    SPACE_03 = 3
    SPACE_04 = 4
    SPACE_05 = 5
    SPACE_06 = 6
    SPACE_07 = 7
    SPACE_08 = 8
    SPACE_09 = 9
    SPACE_10 = 10

    def advance_by(self, number: int) -> Self:
        value = modulo_from_1(self.value + number, len(self.__class__))
        return self.__class__(value)


def parse_starting_spaces(starting_spaces: str) -> dict[Player, Space]:
    position: dict[Player, Space] = {}

    for line in starting_spaces.strip().split('\n'):
        player_part, space_part = (
            line.strip().removeprefix('Player ').split(' starting position: ')
        )
        player, space = Player(int(player_part)), Space(int(space_part))

        if player in position:
            raise ValueError('duplicate player line detected in input file')
        position[player] = space

    return position


DETERMINISTIC_DIE_MAX: Final[int] = 100


class DeterministicDie:

    __slots__ = ('next_value', 'times_rolled')

    def __init__(self) -> None:
        self.next_value: int = 1
        self.times_rolled: int = 0

    def roll(self) -> int:
        value = self.next_value
        self.next_value = modulo_from_1(
            self.next_value + 1, DETERMINISTIC_DIE_MAX,
        )
        self.times_rolled += 1
        return value

    def __next__(self) -> int:
        return self.roll()

    def __iter__(self) -> Iterator[int]:
        return self


WINNING_SCORE: Final[int] = 1_000


class GameState:

    __slots__ = ('position', 'score', 'up_next')

    def __init__(self) -> None:
        self.position: dict[Player, Space] = {
            Player.ONE: Space(1), Player.TWO: Space(1),
        }
        self.score: dict[Player, int] = {Player.ONE: 0, Player.TWO: 0}
        self.up_next: Player = Player.ONE

    def set_position(self, position: dict[Player, Space]) -> None:
        for player, space in position.items():
            self.position[player] = space

    def take_turn(self, die: Iterator[int]) -> None:
        player, self.up_next = self.up_next, self.up_next.get_opponent()
        roll = next(die) + next(die) + next(die)
        self.position[player] = self.position[player].advance_by(roll)
        self.score[player] += self.position[player].value

    def get_winner(self) -> Player | None:
        for player, score in self.score.items():
            if score >= WINNING_SCORE:
                return player
        return None

    def get_loser(self) -> Player | None:
        winner = self.get_winner()
        return None if winner is None else winner.get_opponent()


def part_1(file: pathlib.Path) -> None:
    starting_spaces = file.read_text(encoding='ascii')
    start_position = parse_starting_spaces(starting_spaces)
    die, game = DeterministicDie(), GameState()

    game.set_position(start_position)
    while game.get_winner() is None:
        game.take_turn(die)

    loser = game.get_loser()
    assert loser is not None
    answer = game.score[loser] * die.times_rolled
    print('part 1:', answer)


class FrozenUniverseState(NamedTuple):
    player_1_position: Space
    player_2_position: Space
    player_1_score: int
    player_2_score: int
    current_player: Player
    rolls_remaining: int
    roll_total: int


DIRAC_DIE_VALUES: Final[tuple[int, ...]] = (1, 2, 3)

DIRAC_WINNING_SCORE: Final[int] = 21


class UniverseState:

    __slots__ = (
        'position', 'score', 'current_player', 'rolls_remaining', 'roll_total',
    )

    def __init__(self) -> None:
        self.position: dict[Player, Space] = {
            Player.ONE: Space(1), Player.TWO: Space(1),
        }
        self.score: dict[Player, int] = {Player.ONE: 0, Player.TWO: 0}
        self.current_player: Player = Player.ONE
        self.rolls_remaining = 3
        self.roll_total = 0

    def set_position(self, position: dict[Player, Space]) -> None:
        for player, space in position.items():
            self.position[player] = space

    def freeze(self) -> FrozenUniverseState:
        return FrozenUniverseState(
            player_1_position=self.position[Player.ONE],
            player_2_position=self.position[Player.TWO],
            player_1_score=self.score[Player.ONE],
            player_2_score=self.score[Player.TWO],
            current_player=self.current_player,
            rolls_remaining=self.rolls_remaining,
            roll_total=self.roll_total,
        )

    def set_from_frozen(self, frozen: FrozenUniverseState) -> None:
        self.position[Player.ONE] = frozen.player_1_position
        self.position[Player.TWO] = frozen.player_2_position
        self.score[Player.ONE] = frozen.player_1_score
        self.score[Player.TWO] = frozen.player_2_score
        self.current_player = frozen.current_player
        self.rolls_remaining = frozen.rolls_remaining
        self.roll_total = frozen.roll_total

    def roll_dirac_die(self) -> list[FrozenUniverseState]:
        universes: list[FrozenUniverseState] = []
        player = self.current_player
        self.rolls_remaining -= 1
        for roll in DIRAC_DIE_VALUES:
            self.roll_total += roll
            saved_roll_total = self.roll_total
            if self.rolls_remaining == 0:
                self.position[player] = (
                    self.position[player].advance_by(self.roll_total)
                )
                self.score[player] += self.position[player].value
                self.current_player = player.get_opponent()
                self.rolls_remaining = 3
                self.roll_total = 0
            universes.append(self.freeze())
            if self.rolls_remaining == 3:
                self.roll_total = saved_roll_total
                self.rolls_remaining = 0
                self.current_player = player
                self.score[player] -= self.position[player].value
                self.position[player] = (
                    self.position[player].advance_by(-self.roll_total)
                )
            self.roll_total -= roll
        self.rolls_remaining += 1
        return universes

    def get_winner(self) -> Player | None:
        for player, score in self.score.items():
            if score >= DIRAC_WINNING_SCORE:
                return player
        return None


class UniverseTally(NamedTuple):
    player_1_wins: int
    player_2_wins: int


@functools.cache
def compute_universe_tally(state: FrozenUniverseState) -> UniverseTally:
    universe = UniverseState()
    universe.set_from_frozen(state)
    match universe.get_winner():
        case Player.ONE:
            return UniverseTally(player_1_wins=1, player_2_wins=0)
        case Player.TWO:
            return UniverseTally(player_1_wins=0, player_2_wins=1)
        case _:
            pass
    futures = universe.roll_dirac_die()
    future_tallies = [compute_universe_tally(future) for future in futures]
    return UniverseTally(
        player_1_wins=sum(
            future_tally.player_1_wins for future_tally in future_tallies
        ),
        player_2_wins=sum(
            future_tally.player_2_wins for future_tally in future_tallies
        ),
    )


def part_2(file: pathlib.Path) -> None:
    starting_spaces = file.read_text(encoding='ascii')
    start_position = parse_starting_spaces(starting_spaces)
    universe = UniverseState()

    universe.set_position(start_position)
    tally = compute_universe_tally(universe.freeze())

    print('part 2:', max(tally))


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
