from dataclasses import dataclass
import functools
import itertools
import operator
import pathlib
import sys
from typing import Final, Self


OPEN_BRACKET: Final[str] = '['
COMMA: Final[str] = ','
CLOSE_BRACKET: Final[str] = ']'

PAIR_PUNCTUATION: Final[tuple[str, str, str]] = (
    OPEN_BRACKET, COMMA, CLOSE_BRACKET,
)


NESTING_THRESHOLD: Final[int] = 4
SPLIT_THRESHOLD: Final[int] = 10


@dataclass(repr=False, frozen=True, match_args=False, slots=True)
class SnailfishNumber:
    pair: list[str | int]

    @classmethod
    def parse(cls, string: str) -> Self:
        pair: list[str | int] = []
        for character in string.strip():
            if character in PAIR_PUNCTUATION:
                pair.append(character)
            elif character.isdigit():
                pair.append(int(character))
            else:
                raise ValueError(f'parsed invalid character: {character!r}')
        return cls(pair)

    def __str__(self) -> str:
        return ''.join(map(str, self.pair))

    def check_explode_criteria(self) -> int | None:
        levels_nested = 0
        for index, value in enumerate(self.pair):
            if value == OPEN_BRACKET:
                levels_nested += 1
            elif value == CLOSE_BRACKET:
                levels_nested -= 1
            if levels_nested > NESTING_THRESHOLD:
                return index
        return None

    def explode(self, index: int) -> None:
        end_index = index + 5
        bracket_1, left, comma, right, bracket_2 = self.pair[index:end_index]
        assert (bracket_1, comma, bracket_2) == PAIR_PUNCTUATION
        assert isinstance(left, int) and isinstance(right, int)

        # Seek leftward for an int we can add the left value onto
        seek_index = index - 1
        while seek_index >= 0:
            value = self.pair[seek_index]
            if isinstance(value, int):
                self.pair[seek_index] = value + left
                break
            seek_index -= 1

        # Seek rightward for an int we can add the right value onto
        seek_index = end_index
        while seek_index < len(self.pair):
            value = self.pair[seek_index]
            if isinstance(value, int):
                self.pair[seek_index] = value + right
                break
            seek_index += 1

        self.pair[index:end_index] = [0]

    def check_split_criteria(self) -> int | None:
        for index, value in enumerate(self.pair):
            if isinstance(value, int) and value >= SPLIT_THRESHOLD:
                return index
        return None

    def split(self, index: int) -> None:
        value = self.pair[index]
        assert isinstance(value, int)
        left = value // 2  # Half rounded down
        right = value - left  # Half rounded up
        new_pair: list[str | int] = [
            OPEN_BRACKET, left, COMMA, right, CLOSE_BRACKET,
        ]
        self.pair[index:index+1] = new_pair

    def reduce(self) -> None:
        reduced = False
        while not reduced:

            index_to_explode = self.check_explode_criteria()
            if index_to_explode is not None:
                self.explode(index_to_explode)
                continue

            index_to_split = self.check_split_criteria()
            if index_to_split is not None:
                self.split(index_to_split)
                continue

            reduced = True

    def __add__(self, other: Self) -> Self:
        sum_pair: list[str | int] = []
        sum_pair.append(OPEN_BRACKET)
        sum_pair.extend(self.pair)
        sum_pair.append(COMMA)
        sum_pair.extend(other.pair)
        sum_pair.append(CLOSE_BRACKET)

        number = self.__class__(sum_pair)
        number.reduce()
        return number

    def get_elements(self) -> tuple[list[str | int], list[str | int]]:
        levels_nested = 0
        for index, value in enumerate(self.pair):
            if value == OPEN_BRACKET:
                levels_nested += 1
            elif value == CLOSE_BRACKET:
                levels_nested -= 1

            # Split the pair on the central comma that's at the first level.
            elif value == COMMA and levels_nested == 1:
                bracket_1, *left_element, comma = self.pair[:index+1]
                assert (bracket_1, comma) == PAIR_PUNCTUATION[:2]
                comma, *right_element, bracket_2 = self.pair[index:]
                assert (comma, bracket_2) == PAIR_PUNCTUATION[-2:]
                return left_element, right_element

        raise RuntimeError('failed to get elements from snailfish number')


def parse_snailfish_numbers(homework_assignment: str) -> list[SnailfishNumber]:
    return list(
        map(SnailfishNumber.parse, homework_assignment.strip().split('\n'))
    )


MAGNITUDE_LEFT_MULTIPLIER: Final[int] = 3
MAGNITUDE_RIGHT_MULTIPLIER: Final[int] = 2


def magnitude(number: SnailfishNumber) -> int:
    left, right = number.get_elements()
    magnitude_sum = 0

    match left:
        case [value] if isinstance(value, int):
            left_magnitude = value
        case _:
            left_magnitude = magnitude(SnailfishNumber(left))
    magnitude_sum += MAGNITUDE_LEFT_MULTIPLIER * left_magnitude

    match right:
        case [value] if isinstance(value, int):
            right_magnitude = value
        case _:
            right_magnitude = magnitude(SnailfishNumber(right))
    magnitude_sum += MAGNITUDE_RIGHT_MULTIPLIER * right_magnitude

    return magnitude_sum


def part_1(file: pathlib.Path) -> None:
    homework_assignment = file.read_text(encoding='ascii')
    snailfish_numbers = parse_snailfish_numbers(homework_assignment)
    final_sum = functools.reduce(operator.add, snailfish_numbers)
    print('part 1:', magnitude(final_sum))


def part_2(file: pathlib.Path) -> None:
    homework_assignment = file.read_text(encoding='ascii')
    snailfish_numbers = parse_snailfish_numbers(homework_assignment)

    snailfish_number_pairs = itertools.product(snailfish_numbers, repeat=2)
    snailfish_number_pair_sums = itertools.starmap(
        operator.add, snailfish_number_pairs,
    )
    largest_magnitude = max(map(magnitude, snailfish_number_pair_sums))

    print('part 2:', largest_magnitude)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
