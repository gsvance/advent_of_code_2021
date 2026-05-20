import matplotlib.pyplot as plt
import pathlib
import sys


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

    # Since the fuel-spending function we're minimizing is a sum of absolute
    # values, we only have to check the positions that *already* have at least
    # one crab. This property comes out of the derivative of |x|.
    positions_to_try = sorted(crabs.keys())
    fuel_spending_options = [fuel_spent(x, crabs) for x in positions_to_try]

    print('part 1:', min(fuel_spending_options))

    # Just for fun... go ahead and plot the function we're minimizing
    plt.plot(positions_to_try, fuel_spending_options)
    plt.title(f'part 1 ({file.stem})')
    plt.xlabel('horizontal position')
    plt.ylabel('fuel spent')
    plt.savefig('part_1.png')
    plt.close()


def sum_from_0_to(n: int) -> int:
    return (n * (n + 1)) // 2


def corrected_fuel_spent(x: int, crabs: dict[int, int]) -> int:
    total_fuel_spent = 0
    for x_crab, tally in crabs.items():
        fuel_spent_per_crab = sum_from_0_to(abs(x - x_crab))
        total_fuel_spent += fuel_spent_per_crab * tally
    return total_fuel_spent


def part_2(file: pathlib.Path) -> None:
    crab_positions = file.read_text(encoding='ascii')
    crabs = parse_crabs(crab_positions)

    # I was previously trying to do something much more clever here, but it's
    # just not necessary. The function isn't that expensive to compute and
    # there are only so many points to check. Even brute force runs quickly.
    positions_to_try = list(range(min(crabs.keys()), max(crabs.keys()) + 1))
    fuel_spending_options = [
        corrected_fuel_spent(x, crabs) for x in positions_to_try
    ]

    print('part 2:', min(fuel_spending_options))

    # Evaluating the function at every point also means we can make a plot
    plt.plot(positions_to_try, fuel_spending_options)
    plt.title(f'part 2 ({file.stem})')
    plt.xlabel('horizontal position')
    plt.ylabel('corrected fuel spent')
    plt.savefig('part_2.png')
    plt.close()


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
