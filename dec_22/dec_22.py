from dataclasses import dataclass
from enum import Enum
import itertools
import pathlib
import sys
from typing import Final, Self


class OnOff(Enum):
    ON = 'on'
    OFF = 'off'

    def is_on(self) -> bool:
        match self:
            case self.__class__.ON:
                return True
            case self.__class__.OFF:
                return False
            case _:
                raise RuntimeError('unreachable code')


def nonnegative_width(lower: int, upper: int) -> int:
    return upper - lower + 1 if lower <= upper else 0


@dataclass(init=False, repr=False, frozen=True, match_args=False, slots=True)
class Cuboid:
    x1: int
    x2: int
    y1: int
    y2: int
    z1: int
    z2: int

    def __init__(
        self, x: tuple[int, int], y: tuple[int, int], z: tuple[int, int],
    ) -> None:
        (x1, x2), (y1, y2), (z1, z2) = x, y, z
        object.__setattr__(self, 'x1', x1)
        object.__setattr__(self, 'x2', x2)
        object.__setattr__(self, 'y1', y1)
        object.__setattr__(self, 'y2', y2)
        object.__setattr__(self, 'z1', z1)
        object.__setattr__(self, 'z2', z2)

    def __repr__(self) -> str:
        x, y, z = (self.x1, self.x2), (self.y1, self.y2), (self.z1, self.z2)
        return f'{self.__class__.__name__}({x=}, {y=}, {z=})'

    @classmethod
    def parse(cls, cuboid_string: str) -> Self:
        x_piece, y_piece, z_piece = cuboid_string.strip().split(',')
        x1, x2 = x_piece.removeprefix('x=').split('..')
        y1, y2 = y_piece.removeprefix('y=').split('..')
        z1, z2 = z_piece.removeprefix('z=').split('..')
        return cls(
            x=(int(x1), int(x2)), y=(int(y1), int(y2)), z=(int(z1), int(z2)),
        )

    def contains(self, other: Self) -> bool:
        return (
            self.x1 <= other.x1 <= self.x2
            and self.x1 <= other.x2 <= self.x2
            and self.y1 <= other.y1 <= self.y2
            and self.y1 <= other.y2 <= self.y2
            and self.z1 <= other.z1 <= self.z2
            and self.z1 <= other.z2 <= self.z2
        )

    def overlaps_with(self, other: Self) -> bool:
        return not (
            other.x1 <= other.x2 < self.x1 <= self.x2
            or self.x1 <= self.x2 < other.x1 <= other.x2
            or other.y1 <= other.y2 < self.y1 <= self.y2
            or self.y1 <= self.y2 < other.y1 <= other.y2
            or other.z1 <= other.z2 < self.z1 <= self.z2
            or self.z1 <= self.z2 < other.z1 <= other.z2
        )

    @property
    def size(self) -> int:
        return (
            nonnegative_width(self.x1, self.x2)
            * nonnegative_width(self.y1, self.y2)
            * nonnegative_width(self.z1, self.z2)
        )

    def intersection(self, other: Self) -> Self:
        if self.size == 0 or other.size == 0:
            raise ValueError('intersection with a cuboid of size zero')
        x1, x2 = max(self.x1, other.x1), min(self.x2, other.x2)
        y1, y2 = max(self.y1, other.y1), min(self.y2, other.y2)
        z1, z2 = max(self.z1, other.z1), min(self.z2, other.z2)
        return self.__class__(x=(x1, x2), y=(y1, y2), z=(z1, z2))

    def shatter_around(self, other: Self) -> list[Self]:
        if not self.contains(other):
            raise ValueError('cuboid must be contained to shatter around')

        x_spans = (
            (self.x1, other.x1 - 1),
            (other.x1, other.x2),
            (other.x2 + 1, self.x2),
        )
        y_spans = (
            (self.y1, other.y1 - 1),
            (other.y1, other.y2),
            (other.y2 + 1, self.y2),
        )
        z_spans = (
            (self.z1, other.z1 - 1),
            (other.z1, other.z2),
            (other.z2 + 1, self.z2),
        )

        shattered_pieces: list[Self] = []
        for x, y, z in itertools.product(x_spans, y_spans, z_spans):
            new_piece = self.__class__(x, y, z)
            if new_piece != other and new_piece.size != 0:
                shattered_pieces.append(new_piece)
        return shattered_pieces


@dataclass(frozen=True, match_args=False, slots=True)
class RebootStep:
    on_off: OnOff
    cuboid: Cuboid


def parse_reboot_steps(puzzle_input: str) -> list[RebootStep]:
    reboot_steps: list[RebootStep] = []
    for line in puzzle_input.strip().split('\n'):
        on_off_piece, cuboid_piece = line.strip().split()
        on_off = OnOff(on_off_piece)
        cuboid = Cuboid.parse(cuboid_piece)
        reboot_steps.append(RebootStep(on_off, cuboid))
    return reboot_steps


def delete_cuboid_region(
    active_cuboids: list[Cuboid], delete_region: Cuboid,
) -> list[Cuboid]:
    new_active_cuboids: list[Cuboid] = []
    for cuboid in active_cuboids:
        if not cuboid.overlaps_with(delete_region):
            new_active_cuboids.append(cuboid)
            continue
        intersection = cuboid.intersection(delete_region)
        shattered_cuboid_pieces = cuboid.shatter_around(intersection)
        new_active_cuboids.extend(shattered_cuboid_pieces)
    return new_active_cuboids


def number_of_cubes_turned_on(reboot_steps: list[RebootStep]) -> int:
    active_cuboids: list[Cuboid] = []
    for step in reboot_steps:
        active_cuboids = delete_cuboid_region(active_cuboids, step.cuboid)
        if step.on_off.is_on():
            active_cuboids.append(step.cuboid)
    return sum(cuboid.size for cuboid in active_cuboids)


INITIALIZATION_REGION: Final[Cuboid] = Cuboid.parse(
    'x=-50..50,y=-50..50,z=-50..50'
)


def part_1(file: pathlib.Path) -> None:
    puzzle_input = file.read_text(encoding='ascii')
    reboot_steps = parse_reboot_steps(puzzle_input)
    initialization_steps = [
        step for step in reboot_steps
        if INITIALIZATION_REGION.contains(step.cuboid)
    ]
    cube_count = number_of_cubes_turned_on(initialization_steps)
    print('part 1:', cube_count)


def part_2(file: pathlib.Path) -> None:
    puzzle_input = file.read_text(encoding='ascii')
    reboot_steps = parse_reboot_steps(puzzle_input)
    full_cube_count = number_of_cubes_turned_on(reboot_steps)
    print('part 2:', full_cube_count)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
