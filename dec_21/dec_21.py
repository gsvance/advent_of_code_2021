from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
import functools
import pathlib
import sys
from typing import Final, Self


def modulo_base_1(numerator: int, denominator: int) -> int:
    # Just like modulo, but return a value from the set {1, ..., denominator}
    # instead of from the set {0, ..., denominator-1}.
    return (numerator - 1) % denominator + 1


class Player(Enum):
    ONE = 1
    TWO = 2

    def get_opponent(self) -> Self:
        value = modulo_base_1(self.value + 1, len(self.__class__))
        return self.__class__(value)


@dataclass(frozen=True, match_args=False, kw_only=True, slots=True)
class PlayerMapping[T]:
    player_1: T
    player_2: T

    @classmethod
    def from_dict(cls, player_dict: dict[Player, T]) -> Self:
        if frozenset(player_dict.keys()) != frozenset(Player):
            raise TypeError('invalid dict keyset for player mapping')
        return cls(
            player_1=player_dict[Player.ONE],
            player_2=player_dict[Player.TWO],
        )

    def __getitem__(self, player: Player) -> T:
        match player:
            case Player.ONE:
                return self.player_1
            case Player.TWO:
                return self.player_2
            case _:
                raise KeyError(player)

    def but_with(self, player: Player, new_value: T) -> Self:
        match player:
            case Player.ONE:
                return self.__class__(
                    player_1=new_value, player_2=self.player_2,
                )
            case Player.TWO:
                return self.__class__(
                    player_1=self.player_1, player_2=new_value,
                )
            case _:
                raise KeyError(player)

    def items(self) -> Iterator[tuple[Player, T]]:
        yield Player.ONE, self.player_1
        yield Player.TWO, self.player_2

    def values(self) -> Iterator[T]:
        yield self.player_1
        yield self.player_2


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
        value = modulo_base_1(self.value + number, len(self.__class__))
        return self.__class__(value)


def parse_starting_spaces(starting_spaces: str) -> PlayerMapping[Space]:
    position: dict[Player, Space] = {}

    for line in starting_spaces.strip().split('\n'):
        player_part, space_part = (
            line.strip().removeprefix('Player ').split(' starting position: ')
        )
        player, space = Player(int(player_part)), Space(int(space_part))

        if player in position:
            raise ValueError('duplicate player line detected in input file')
        position[player] = space

    return PlayerMapping.from_dict(position)


DETERMINISTIC_DIE_MAX: Final[int] = 100


class DeterministicDie:

    __slots__ = ('next_value', 'times_rolled')

    def __init__(self) -> None:
        self.next_value: int = 1
        self.times_rolled: int = 0

    def __next__(self) -> int:
        value = self.next_value
        self.next_value = modulo_base_1(
            self.next_value + 1, DETERMINISTIC_DIE_MAX,
        )
        self.times_rolled += 1
        return value

    def __iter__(self) -> Iterator[int]:
        return self


WINNING_SCORE: Final[int] = 1_000


@dataclass(frozen=True, match_args=False, kw_only=True, slots=True)
class GameState:
    position: PlayerMapping[Space]
    score: PlayerMapping[int] = PlayerMapping(player_1=0, player_2=0)
    up_next: Player = Player.ONE

    def take_turn(self, die: Iterator[int]) -> Self:
        player = self.up_next
        roll = next(die) + next(die) + next(die)
        new_position = self.position[player].advance_by(roll)
        new_score = self.score[player] + self.position[player].value

        return self.__class__(
            position=self.position.but_with(player, new_position),
            score=self.score.but_with(player, new_score),
            up_next=player.get_opponent(),
        )

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

    die = DeterministicDie()
    game = GameState(position=start_position)
    while game.get_winner() is None:
        game = game.take_turn(die)

    loser = game.get_loser()
    assert loser is not None
    answer = game.score[loser] * die.times_rolled
    print('part 1:', answer)


DIRAC_DIE_VALUES: Final[tuple[int, ...]] = (1, 2, 3)

DIRAC_WINNING_SCORE: Final[int] = 21


@dataclass(frozen=True, match_args=False, kw_only=True, slots=True)
class UniverseState:
    position: PlayerMapping[Space]
    score: PlayerMapping[int] = PlayerMapping(player_1=0, player_2=0)
    current_player: Player = Player.ONE
    rolls_remaining: int = 3
    roll_total: int = 0

    def roll_dirac_die(self) -> Iterator[Self]:
        player = self.current_player
        new_rolls_remaining = self.rolls_remaining - 1

        for roll in DIRAC_DIE_VALUES:
            new_roll_total = self.roll_total + roll

            if new_rolls_remaining > 0:
                yield self.__class__(
                    position=self.position,
                    score=self.score,
                    current_player=self.current_player,
                    rolls_remaining=new_rolls_remaining,
                    roll_total=new_roll_total,
                )

            else:  # rolls_remaining == 0
                old_position = self.position[player]
                new_position = old_position.advance_by(new_roll_total)
                new_score = self.score[player] + new_position.value
                yield self.__class__(
                    position=self.position.but_with(player, new_position),
                    score=self.score.but_with(player, new_score),
                    current_player=player.get_opponent(),
                )

    def get_winner(self) -> Player | None:
        for player, score in self.score.items():
            if score >= DIRAC_WINNING_SCORE:
                return player
        return None


@functools.cache
def compute_universe_tally(universe: UniverseState) -> PlayerMapping[int]:
    winner = universe.get_winner()
    if winner is not None:
        return PlayerMapping(player_1=0, player_2=0).but_with(winner, 1)

    running_tally = PlayerMapping(player_1=0, player_2=0)
    futures = universe.roll_dirac_die()
    for future_tally in map(compute_universe_tally, futures):
        running_tally = PlayerMapping(
            player_1=running_tally.player_1 + future_tally.player_1,
            player_2=running_tally.player_2 + future_tally.player_2,
        )

    return running_tally


def part_2(file: pathlib.Path) -> None:
    starting_spaces = file.read_text(encoding='ascii')
    start_position = parse_starting_spaces(starting_spaces)

    universe = UniverseState(position=start_position)
    tally = compute_universe_tally(universe)
    most_universes = max(tally.values())

    print('part 2:', most_universes)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
