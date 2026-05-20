import pathlib
import sys
from typing import Callable


def parse_crabs(crab_positions: str) -> dict[int, int]:
    crabs: dict[int, int] = {}
    for crab_position in crab_positions.strip().split(','):
        x_crab = int(crab_position)
        crabs[x_crab] = crabs.get(x_crab, 0) + 1
    return crabs


def fuel_spent(x: int, crabs: dict[int, int]) -> int:
    total_fuel_spent = 0
    for x_crab, tally in crabs.items():
        fuel_spent_per_crab = abs(x - x_crab)
        total_fuel_spent += fuel_spent_per_crab * tally
    return total_fuel_spent


def part_1(file: pathlib.Path) -> None:
    crab_positions = file.read_text(encoding='ascii')
    crabs = parse_crabs(crab_positions)

    # Since the fuel-spending function we're minimizing is made up of absolute
    # values, we only have to check the positions that *already* have at least
    # one crab. This property comes out of the derivative of |x|.
    positions_to_try = crabs.keys()
    fuel_spending_options = (fuel_spent(x, crabs) for x in positions_to_try)

    print('part 1:', min(fuel_spending_options))


def sum_from_0_to(n: int) -> int:
    return (n * (n + 1)) // 2


def quadratic_fuel_spent(x: int, crabs: dict[int, int]) -> int:
    total_fuel_spent = 0
    for x_crab, tally in crabs.items():
        fuel_spent_per_crab = sum_from_0_to(abs(x - x_crab))
        total_fuel_spent += fuel_spent_per_crab * tally
    return total_fuel_spent


def approximate_slope(function: Callable[[int], int], x: int) -> float:
    return (function(x + 1) - function(x - 1)) / 2.0


def find_min_using_bisection(
    function: Callable[[int], int], left: int, right: int,
) -> int:
    low, high = left, right
    slope_at_low = approximate_slope(function, low)
    slope_at_high = approximate_slope(function, high)

    if not (
        slope_at_low < 0.0 < slope_at_high
        or slope_at_high < 0.0 < slope_at_low
    ):
        raise ValueError('left and right do not bracket a minimum')

    while abs(high - low) > 1:
        middle = (low + high) // 2
        slope_at_middle = approximate_slope(function, middle)
        if slope_at_middle == 0.0:
            return function(middle)
        if slope_at_middle < 0.0:
            if slope_at_low < 0.0:
                low, slope_at_low = middle, slope_at_middle
            else:  # slope_at_high < 0.0
                high, slope_at_high = middle, slope_at_middle
        else:  # slope_at_middle > 0.0
            if slope_at_low > 0.0:
                low, slope_at_low = middle, slope_at_middle
            else:  # slope_at_high > 0.0
                high, slope_at_high = middle, slope_at_middle

    return min(function(low), function(high))


def part_2(file: pathlib.Path) -> None:
    crab_positions = file.read_text(encoding='ascii')
    crabs = parse_crabs(crab_positions)

    min_fuel_spent = find_min_using_bisection(
        lambda x: quadratic_fuel_spent(x, crabs),
        min(crabs.keys()), max(crabs.keys()),
    )

    print('part 2:', min_fuel_spent)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
