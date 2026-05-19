from collections.abc import Iterator
import pathlib
import sys
from typing import Final, Self


BOARD_SIZE: Final[int] = 5


class Board:

    def __init__(self, rows: list[list[int]]) -> None:
        self.rows: list[list[int]] = rows
        if len(self.rows) != BOARD_SIZE:
            raise ValueError(f'board does not have {BOARD_SIZE} rows')
        for row in self.rows:
            if len(row) != BOARD_SIZE:
                raise ValueError(f'board does not have {BOARD_SIZE} columns')

        self.marked: list[list[bool]] = []
        for _ in range(BOARD_SIZE):
            self.marked.append([False] * BOARD_SIZE)

    @classmethod
    def parse(cls, board_string: str) -> Self:
        rows: list[list[int]] = []
        for line in board_string.strip().split('\n'):
            row = list(map(int, line.strip().split()))
            rows.append(row)
        return cls(rows)

    def coordinates(self) -> Iterator[tuple[int, int]]:
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                yield r, c

    def mark(self, number: int) -> None:
        times_marked = 0
        for r, c in self.coordinates():
            if self.rows[r][c] == number:
                self.marked[r][c] = True
                times_marked += 1
        if times_marked not in (0, 1):
            raise RuntimeError('number marked more than once on a board')

    def row_completely_marked(self, r: int) -> bool:
        return all(self.marked[r])

    def column_completely_marked(self, c: int) -> bool:
        return all(self.marked[r][c] for r in range(BOARD_SIZE))

    def wins(self) -> bool:
        for r in range(BOARD_SIZE):
            if self.row_completely_marked(r):
                return True
        for c in range(BOARD_SIZE):
            if self.column_completely_marked(c):
                return True
        return False

    def sum_of_unmarked_numbers(self) -> int:
        the_sum = 0
        for r, c in self.coordinates():
            if not self.marked[r][c]:
                the_sum += self.rows[r][c]
        return the_sum


def parse_boards(boards_string: str) -> list[Board]:
    return list(map(Board.parse, boards_string.strip().split('\n\n')))


def parse_numbers(numbers_string: str) -> list[int]:
    return list(map(int, numbers_string.strip().split(',')))


def parse_numbers_and_boards(
    bingo_subsystem_output: str,
) -> tuple[list[int], list[Board]]:
    numbers_string, boards_string = (
        bingo_subsystem_output.strip().split('\n', maxsplit=1)
    )
    numbers = parse_numbers(numbers_string)
    boards = parse_boards(boards_string)
    return numbers, boards


def part_1(file: pathlib.Path) -> None:
    bingo_subsystem_output = file.read_text(encoding='ascii')
    numbers, boards = parse_numbers_and_boards(bingo_subsystem_output)

    winning_number: int | None = None
    winning_boards: list[Board] = []
    for number in numbers:
        for board in boards:
            board.mark(number)
        for board in boards:
            if board.wins():
                winning_number = number
                winning_boards.append(board)
        if winning_number is not None:
            break

    if winning_number is None:
        raise RuntimeError('there was no winning number')
    if len(winning_boards) != 1:
        raise RuntimeError('number of winning boards was not 1')

    winning_board = winning_boards.pop()
    score = winning_board.sum_of_unmarked_numbers() * winning_number
    print('part 1:', score)


def part_2(file: pathlib.Path) -> None:
    bingo_subsystem_output = file.read_text(encoding='ascii')
    numbers, boards = parse_numbers_and_boards(bingo_subsystem_output)

    last_winning_number: int | None = None
    winning_boards: list[Board] = []
    for number in numbers:
        for board in boards:
            board.mark(number)
        for board in boards:
            if board not in winning_boards and board.wins():
                winning_boards.append(board)
        if len(winning_boards) >= len(boards):
            last_winning_number = number
            break

    if last_winning_number is None:
        raise RuntimeError('there was no last winning number')
    if len(winning_boards) != len(boards):
        raise RuntimeError(
            'number of winning boards does not match number of boards'
        )

    last_winning_board = winning_boards.pop()
    score = last_winning_board.sum_of_unmarked_numbers() * last_winning_number
    print('part 2:', score)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
