from collections.abc import Iterable, Iterator
import pathlib
import sys
from typing import Callable


def parse_bit_matrix(diagnostic_report: str) -> list[list[int]]:
    matrix_rows: list[list[int]] = []
    for line in diagnostic_report.strip().split('\n'):
        row = [int(digit) for digit in line.strip()]
        matrix_rows.append(row)
    return matrix_rows


def matrix_dimensions(matrix: list[list[int]]) -> tuple[int, int]:
    n_rows = len(matrix)
    row_lengths = {len(row) for row in matrix}
    if len(row_lengths) != 1:
        raise ValueError('matrix has inconsistent row lengths')
    n_cols = row_lengths.pop()
    return n_rows, n_cols


def matrix_column(matrix: list[list[int]], c: int) -> Iterator[int]:
    for row in matrix:
        yield row[c]


def int_from_bits(bits: Iterable[int]) -> int:
    value = 0
    for bit in bits:
        if bit not in (0, 1):
            raise ValueError('invalid bit')
        value <<= 1
        value |= bit
    return value


def part_1(file: pathlib.Path) -> None:
    diagnostic_report = file.read_text(encoding='ascii')
    bit_matrix = parse_bit_matrix(diagnostic_report)
    n_rows, n_cols = matrix_dimensions(bit_matrix)

    columns = (matrix_column(bit_matrix, c) for c in range(n_cols))
    averages = (sum(column) / n_rows for column in columns)

    gamma_rate_bits = (round(average) for average in averages)
    gamma_rate = int_from_bits(gamma_rate_bits)

    # Epsilon rate is just bitwise not of gamma rate (using n_rows bits)
    epsilon_rate = (~gamma_rate) & ((1 << n_cols) - 1)

    power_consumption = gamma_rate * epsilon_rate
    print('part 1:', power_consumption)


def most_common(bits: Iterable[int]) -> int:
    tally = {0: 0, 1: 0}
    for bit in bits:
        tally[bit] += 1
    return 0 if tally[0] > tally[1] else 1


def least_common(bits: Iterable[int]) -> int:
    tally = {0: 0, 1: 0}
    for bit in bits:
        tally[bit] += 1
    return 1 if tally[1] < tally[0] else 0


def filter_matrix_rows(
    matrix: list[list[int]],
    selector_function: Callable[[Iterable[int]], int],
    c: int,
) -> list[list[int]]:
    selected_bit = selector_function(matrix_column(matrix, c))
    new_rows = [row for row in matrix if row[c] == selected_bit]
    return new_rows


def part_2(file: pathlib.Path) -> None:
    diagnostic_report = file.read_text(encoding='ascii')

    bit_matrix = parse_bit_matrix(diagnostic_report)
    n_rows, n_cols = matrix_dimensions(bit_matrix)
    for c in range(n_cols):
        if n_rows == 1:
            break
        bit_matrix = filter_matrix_rows(bit_matrix, most_common, c)
        n_rows, n_cols = matrix_dimensions(bit_matrix)
    oxygen_generator_rating = int_from_bits(bit_matrix.pop())

    bit_matrix = parse_bit_matrix(diagnostic_report)
    n_rows, n_cols = matrix_dimensions(bit_matrix)
    for c in range(n_cols):
        if n_rows == 1:
            break
        bit_matrix = filter_matrix_rows(bit_matrix, least_common, c)
        n_rows, n_cols = matrix_dimensions(bit_matrix)
    co2_scrubber_rating = int_from_bits(bit_matrix.pop())

    life_support_rating = oxygen_generator_rating * co2_scrubber_rating
    print('part 2:', life_support_rating)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
