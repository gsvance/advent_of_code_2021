from collections import deque
from collections.abc import Iterator
import itertools
import pathlib
import sys
from typing import Final, NamedTuple, Self


class Point(NamedTuple):
    r: int
    c: int


def iter_adjacent_points(point: Point) -> Iterator[Point]:
    for dr in (-1, 0, +1):
        for dc in (-1, 0, +1):
            if not dr == dc == 0:
                yield Point(r=point.r + dr, c=point.c + dc)


MINIMUM_ENERGY_LEVEL: Final[int] = 0
FLASH_ENERGY_LEVEL: Final[int] = 9 + 1


class Octopuses:

    __slots__ = ('energy_levels', 'flashes_tally')

    def __init__(self, energy_levels: dict[Point, int]) -> None:
        self.energy_levels: dict[Point, int] = energy_levels
        self.flashes_tally: int = 0

    @classmethod
    def parse(cls, energy_levels_string: str) -> Self:
        energy_levels: dict[Point, int] = {}

        for r, line in enumerate(energy_levels_string.strip().split('\n')):
            for c, digit in enumerate(line.strip()):
                octopus, energy_level = Point(r=r, c=c), int(digit)
                energy_levels[octopus] = energy_level

        return cls(energy_levels)

    def simulate_step(self) -> None:
        event_queue = deque(self.energy_levels.keys())

        while event_queue:
            octopus = event_queue.popleft()
            try:
                self.energy_levels[octopus] += 1
            except KeyError:
                continue
            if self.energy_levels[octopus] == FLASH_ENERGY_LEVEL:
                event_queue.extend(iter_adjacent_points(octopus))

        for octopus, energy_level in self.energy_levels.items():
            if energy_level >= FLASH_ENERGY_LEVEL:
                self.energy_levels[octopus] = MINIMUM_ENERGY_LEVEL
                self.flashes_tally += 1


NUMBER_OF_STEPS: Final[int] = 100


def part_1(file: pathlib.Path) -> None:
    energy_levels_string = file.read_text(encoding='ascii')
    octopuses = Octopuses.parse(energy_levels_string)

    for _ in range(NUMBER_OF_STEPS):
        octopuses.simulate_step()

    print('part 1:', octopuses.flashes_tally)


class SynchronizingOctopuses(Octopuses):

    __slots__ = ('simultaneous_flash_just_happened',)

    def __init__(self, energy_levels: dict[Point, int]) -> None:
        super().__init__(energy_levels)
        self.simultaneous_flash_just_happened: bool = False

    def simulate_step(self) -> None:
        previous_flashes_tally = self.flashes_tally
        super().simulate_step()
        flashes_this_step = self.flashes_tally - previous_flashes_tally
        self.simultaneous_flash_just_happened = (
            flashes_this_step == len(self.energy_levels)
        )


def part_2(file: pathlib.Path) -> None:
    energy_levels_string = file.read_text(encoding='ascii')
    octopuses = SynchronizingOctopuses.parse(energy_levels_string)

    step_number = 0
    for step_number in itertools.count(start=1):
        octopuses.simulate_step()
        if octopuses.simultaneous_flash_just_happened:
            break

    print('part 2:', step_number)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
