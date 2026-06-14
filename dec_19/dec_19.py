from collections import Counter, deque
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
import pathlib
import sys
from typing import Final, Self


@dataclass(frozen=True, match_args=False, slots=True)
class Vector:
    x: int
    y: int
    z: int

    @classmethod
    def parse(cls, vector_string: str) -> Self:
        x_part, y_part, z_part = vector_string.strip().split(',')
        return cls(int(x_part), int(y_part), int(z_part))

    def __pos__(self) -> Self:
        return self

    def __neg__(self) -> Self:
        return self.__class__(-self.x, -self.y, -self.z)

    def __add__(self, other: Self) -> Self:
        return self.__class__(
            self.x + other.x, self.y + other.y, self.z + other.z,
        )

    def __sub__(self, other: Self) -> Self:
        return self.__class__(
            self.x - other.x, self.y - other.y, self.z - other.z,
        )

    def dot(self, other: Self) -> int:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: Self) -> Self:
        x = self.y * other.z - self.z * other.y
        y = self.z * other.x - self.x * other.z
        z = self.x * other.y - self.y * other.x
        return self.__class__(x, y, z)

    def manhattan(self) -> int:
        return abs(self.x) + abs(self.y) + abs(self.z)

    def is_zero(self) -> bool:
        return self.manhattan() == 0

    def is_unit(self) -> bool:
        return self.manhattan() == 1


I_HAT: Final[Vector] = Vector(+1, 0, 0)
J_HAT: Final[Vector] = Vector(0, +1, 0)
K_HAT: Final[Vector] = Vector(0, 0, +1)

UNIT_VECTORS: Final[tuple[Vector, ...]] = (
    +I_HAT, +J_HAT, +K_HAT, -I_HAT, -J_HAT, -K_HAT,
)


@dataclass(init=False, frozen=True, match_args=False, slots=True)
class Orientation:
    e_x: Vector
    e_y: Vector
    e_z: Vector

    def __init__(self, e_x: Vector, e_y: Vector) -> None:
        if not e_x.is_unit() or not e_y.is_unit():
            raise ValueError('orientation must be made from unit vectors')
        e_z = e_x.cross(e_y)
        if e_z.is_zero():
            raise ValueError('orientation vectors must be orthogonal')
        object.__setattr__(self, 'e_x', e_x)
        object.__setattr__(self, 'e_y', e_y)
        object.__setattr__(self, 'e_z', e_z)

    def __call__(self, vector: Vector) -> Vector:
        e_x_component = self.e_x.dot(vector)
        e_y_component = self.e_y.dot(vector)
        e_z_component = self.e_z.dot(vector)
        return Vector(e_x_component, e_y_component, e_z_component)


ALL_ORIENTATIONS: Final[tuple[Orientation, ...]] = tuple(
    Orientation(e_x, e_y) for e_x in UNIT_VECTORS for e_y in UNIT_VECTORS
    if e_x.cross(e_y).is_unit()
)


@dataclass(frozen=True, match_args=False, slots=True)
class Scanner:
    index: int
    beacons: frozenset[Vector]
    position: Vector = Vector(0, 0, 0)

    @classmethod
    def parse(cls, scanner_summary: str) -> Self:
        header_string, beacons_string = (
            scanner_summary.strip().split('\n', maxsplit=1)
        )
        index = int(
            header_string.removeprefix('--- scanner ').removesuffix(' ---')
        )
        beacons = frozenset(
            map(Vector.parse, beacons_string.strip().split('\n'))
        )
        return cls(index, beacons)

    def rotate(self, orientation: Orientation) -> Self:
        if not self.position.is_zero():
            raise ValueError('can only rotate scanner when it is the origin')
        rotated_beacons = frozenset(
            orientation(beacon) for beacon in self.beacons
        )
        return self.__class__(self.index, rotated_beacons)

    def translate(self, offset: Vector) -> Self:
        translated_beacons = frozenset(
            beacon + offset for beacon in self.beacons
        )
        translated_position = self.position + offset
        return self.__class__(
            self.index, translated_beacons, translated_position,
        )


def parse_scanners(situation_summary: str) -> list[Scanner]:
    return list(map(Scanner.parse, situation_summary.strip().split('\n\n')))


def paired_differences(
    set_a: Iterable[Vector], set_b: Iterable[Vector],
) -> Iterator[Vector]:
    for vector_a in set_a:
        for vector_b in set_b:
            yield vector_a - vector_b


BEACONS_THRESHOLD: Final[int] = 12


def find_scanner_alignment(
    aligned_scanner: Scanner, misaligned_scanner: Scanner,
) -> tuple[Orientation, Vector] | None:
    for orientation in ALL_ORIENTATIONS:
        rotated_scanner = misaligned_scanner.rotate(orientation)
        difference_tallies = Counter(paired_differences(
            aligned_scanner.beacons, rotated_scanner.beacons,
        ))
        offset, tally = difference_tallies.most_common(1).pop()
        if tally >= BEACONS_THRESHOLD:
            return orientation, offset
    return None


def align_scanner_beacons_data(scanners: list[Scanner]) -> list[Scanner]:
    aligned_scanners = [scanners[0]]
    misaligned_scanners = deque(scanners[1:])

    while misaligned_scanners:

        this_scanner = misaligned_scanners.popleft()
        newly_aligned: Scanner | None = None

        for aligned_scanner in aligned_scanners:
            alignment = find_scanner_alignment(aligned_scanner, this_scanner)
            if alignment is not None:
                orientation, offset = alignment
                newly_aligned = (
                    this_scanner.rotate(orientation).translate(offset)
                )
                break

        if newly_aligned is not None:
            aligned_scanners.append(newly_aligned)
        else:
            misaligned_scanners.append(this_scanner)

    aligned_scanners.sort(key=lambda scanner: scanner.index)
    return aligned_scanners


def part_1(file: pathlib.Path) -> None:
    situation_summary = file.read_text(encoding='ascii')
    scanners = parse_scanners(situation_summary)

    aligned_scanners = align_scanner_beacons_data(scanners)

    beacons_map = {
        beacon for scanner in aligned_scanners for beacon in scanner.beacons
    }
    print('part 1:', len(beacons_map))


def every_manhattan_distance(scanners: list[Scanner]) -> Iterator[int]:
    for scanner_1 in scanners:
        for scanner_2 in scanners:
            separation = scanner_1.position - scanner_2.position
            yield separation.manhattan()


def part_2(file: pathlib.Path) -> None:
    situation_summary = file.read_text(encoding='ascii')
    scanners = parse_scanners(situation_summary)

    aligned_scanners = align_scanner_beacons_data(scanners)

    largest_manhattan_distance = max(
        every_manhattan_distance(aligned_scanners)
    )
    print('part 2:', largest_manhattan_distance)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
