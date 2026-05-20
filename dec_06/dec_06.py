import pathlib
import sys
from typing import Final


def parse_fish_ages(ages_of_nearby_fish: str) -> list[int]:
    return list(map(int, ages_of_nearby_fish.strip().split(',')))


OLD_FISH_CYCLE_TIME: Final[int] = 7
NEW_FISH_EXTRA_TIME: Final[int] = 2


def initialize_fish_timer_counts(fish_ages: list[int]) -> dict[int, int]:
    fish_timer_counts = {
        timer: 0 for timer in range(OLD_FISH_CYCLE_TIME + NEW_FISH_EXTRA_TIME)
    }

    for fish_age in fish_ages:
        if fish_age < 1 or fish_age >= OLD_FISH_CYCLE_TIME:
            raise ValueError(f'not a valid initial fish age: {fish_age}')
        fish_timer_counts[fish_age] += 1

    return fish_timer_counts


def simulate_one_day(fish_timer_counts: dict[int, int]) -> dict[int, int]:
    number_of_new_fish = fish_timer_counts[0]

    new_fish_timer_counts = {
        (timer - 1): count for timer, count in fish_timer_counts.items()
    }
    del new_fish_timer_counts[-1]

    new_fish_timer_counts[OLD_FISH_CYCLE_TIME - 1] += fish_timer_counts[0]
    new_fish_timer_counts[OLD_FISH_CYCLE_TIME + NEW_FISH_EXTRA_TIME - 1] = (
        number_of_new_fish
    )

    if (
        frozenset(new_fish_timer_counts.keys())
        != frozenset(range(OLD_FISH_CYCLE_TIME + NEW_FISH_EXTRA_TIME))
    ):
        raise RuntimeError('new fish timer counts has incorrect set of keys')

    return new_fish_timer_counts


def part_1(file: pathlib.Path) -> None:
    ages_of_nearby_fish = file.read_text(encoding='ascii')
    fish_ages = parse_fish_ages(ages_of_nearby_fish)
    fish_timer_counts = initialize_fish_timer_counts(fish_ages)
    for _ in range(80):
        fish_timer_counts = simulate_one_day(fish_timer_counts)
    print('part 1:', sum(fish_timer_counts.values()))


def part_2(file: pathlib.Path) -> None:
    ages_of_nearby_fish = file.read_text(encoding='ascii')
    fish_ages = parse_fish_ages(ages_of_nearby_fish)
    fish_timer_counts = initialize_fish_timer_counts(fish_ages)
    for _ in range(256):
        fish_timer_counts = simulate_one_day(fish_timer_counts)
    print('part 2:', sum(fish_timer_counts.values()))


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
