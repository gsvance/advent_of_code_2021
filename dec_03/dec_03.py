from collections.abc import Iterable, Iterator
import pathlib
import sys


def parse_bit_matrix(diagnostic_report: str) -> list[list[int]]:
    matrix: list[list[int]] = []
    for line in diagnostic_report.strip().split('\n'):
        row = [int(digit) for digit in line.strip()]
        matrix.append(row)
    return matrix


def matrix_n_cols(matrix: list[list[int]]) -> int:
    row_lengths = {len(row) for row in matrix}
    if len(row_lengths) != 1:
        raise ValueError('matrix has inconsistent row lengths')
    return row_lengths.pop()


def matrix_column(matrix: list[list[int]], c: int) -> Iterator[int]:
    for row in matrix:
        yield row[c]


def most_common_bit(
    bits: Iterable[int], *, if_tied: int | None = None,
) -> int:
    tally = {0: 0, 1: 0}
    for bit in bits:
        tally[bit] += 1

    if tally[0] > tally[1]:
        return 0
    if tally[1] > tally[0]:
        return 1

    if if_tied is None:
        raise ValueError('cannot resolve tie for most common bit')
    return if_tied


def least_common_bit(
    bits: Iterable[int], *, if_tied: int | None = None,
) -> int:
    tally = {0: 0, 1: 0}
    for bit in bits:
        tally[bit] += 1

    if tally[0] < tally[1]:
        return 0
    if tally[1] < tally[0]:
        return 1

    if if_tied is None:
        raise ValueError('cannot resolve tie for least common bit')
    return if_tied


def int_from_bits(bits: Iterable[int]) -> int:
    value = 0
    for bit in bits:
        if bit not in (0, 1):
            raise ValueError('invalid bit')
        value = (value << 1) | bit
    return value


def part_1(file: pathlib.Path) -> None:
    diagnostic_report = file.read_text(encoding='ascii')
    bit_matrix = parse_bit_matrix(diagnostic_report)
    n_cols = matrix_n_cols(bit_matrix)

    columns = (matrix_column(bit_matrix, c) for c in range(n_cols))
    gamma_rate_bits = map(most_common_bit, columns)
    gamma_rate = int_from_bits(gamma_rate_bits)

    columns = (matrix_column(bit_matrix, c) for c in range(n_cols))
    epsilon_rate_bits = map(least_common_bit, columns)
    epsilon_rate = int_from_bits(epsilon_rate_bits)

    power_consumption = gamma_rate * epsilon_rate
    print('part 1:', power_consumption)


def matrix_n_rows(matrix: list[list[int]]) -> int:
    return len(matrix)


def filter_rows_by_most_common_bit(
    matrix: list[list[int]], c: int,
) -> list[list[int]]:
    column = matrix_column(matrix, c)
    selected_bit = most_common_bit(column, if_tied=1)
    new_matrix = [row for row in matrix if row[c] == selected_bit]
    return new_matrix


def filter_rows_by_least_common_bit(
    matrix: list[list[int]], c: int,
) -> list[list[int]]:
    column = matrix_column(matrix, c)
    selected_bit = least_common_bit(column, if_tied=0)
    new_matrix = [row for row in matrix if row[c] == selected_bit]
    return new_matrix


def part_2(file: pathlib.Path) -> None:
    diagnostic_report = file.read_text(encoding='ascii')

    bit_matrix = parse_bit_matrix(diagnostic_report)
    c = -1
    while matrix_n_rows(bit_matrix) > 1:
        c += 1
        bit_matrix = filter_rows_by_most_common_bit(bit_matrix, c)
    oxygen_generator_rating = int_from_bits(bit_matrix.pop())

    bit_matrix = parse_bit_matrix(diagnostic_report)
    c = -1
    while matrix_n_rows(bit_matrix) > 1:
        c += 1
        bit_matrix = filter_rows_by_least_common_bit(bit_matrix, c)
    co2_scrubber_rating = int_from_bits(bit_matrix.pop())

    life_support_rating = oxygen_generator_rating * co2_scrubber_rating
    print('part 2:', life_support_rating)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
