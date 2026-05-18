from dataclasses import dataclass
import pathlib
import sys
from typing import Final, Self


@dataclass(frozen=True, match_args=False, kw_only=True, slots=True)
class Vector:
    horizontal: int
    depth: int

    def __add__(self, other: Self) -> Self:
        return self.__class__(
            horizontal=self.horizontal + other.horizontal,
            depth=self.depth + other.depth,
        )

    def __rmul__(self, other: int) -> Self:
        return self.__class__(
            horizontal=self.horizontal * other,
            depth=self.depth * other,
        )


DIRECTION_VECTOR: Final[dict[str, Vector]] = {
    'forward': Vector(horizontal=+1, depth=0),
    'down': Vector(horizontal=0, depth=+1),
    'up': Vector(horizontal=0, depth=-1),
}


def parse_vectors(planned_course: str) -> list[Vector]:
    course_vectors: list[Vector] = []
    for line in planned_course.strip().split('\n'):
        direction, units = line.strip().split()
        course_vectors.append(int(units) * DIRECTION_VECTOR[direction])
    return course_vectors


def part_1(file: pathlib.Path) -> None:
    planned_course = file.read_text(encoding='ascii')
    course_vectors = parse_vectors(planned_course)
    start_vector = Vector(horizontal=0, depth=0)
    final_position = sum(course_vectors, start=start_vector)
    print('part 1:', final_position.horizontal * final_position.depth)


@dataclass(match_args=False, kw_only=True, slots=True)
class Submarine:
    horizontal: int
    depth: int
    aim: int


def chart_submarine_course(planned_course: str) -> Vector:
    submarine = Submarine(horizontal=0, depth=0, aim=0)

    for line in planned_course.strip().split('\n'):
        direction, units = line.strip().split()
        x = int(units)

        match direction:
            case 'down':
                submarine.aim += x
            case 'up':
                submarine.aim -= x
            case 'forward':
                submarine.horizontal += x
                submarine.depth += submarine.aim * x
            case _:
                raise RuntimeError(f'invalid direction {direction!r}')

    return Vector(horizontal=submarine.horizontal, depth=submarine.depth)


def part_2(file: pathlib.Path) -> None:
    planned_course = file.read_text(encoding='ascii')
    final_position = chart_submarine_course(planned_course)
    print('part 2:', final_position.horizontal * final_position.depth)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
