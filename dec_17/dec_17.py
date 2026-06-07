from dataclasses import dataclass
import pathlib
import re
import sys
from typing import Any, Final, Self


@dataclass(frozen=True, slots=True)
class Vector:
    x: int
    y: int

    def __add__(self, other: Self) -> Self:
        return self.__class__(self.x + other.x, self.y + other.y)


VECTOR_BOUNDS_REGEX: Final[re.Pattern[str]] = re.compile(
    r'x=([0-9-]+)\.\.([0-9-]+), y=([0-9-]+)\.\.([0-9-]+)',
    re.ASCII | re.MULTILINE,
)


@dataclass(init=False, frozen=True, match_args=False, slots=True)
class VectorBounds:
    min: Vector
    max: Vector

    def __init__(self, x1: int, x2: int, y1: int, y2: int) -> None:
        min_vector = Vector(min(x1, x2), min(y1, y2))
        max_vector = Vector(max(x1, x2), max(y1, y2))
        object.__setattr__(self, 'min', min_vector)
        object.__setattr__(self, 'max', max_vector)

    @classmethod
    def parse(cls, target_area_string: str) -> Self:
        match = VECTOR_BOUNDS_REGEX.search(target_area_string)
        if not match:
            raise ValueError('got invalid vector bounds string')
        x1, x2 = int(match.group(1)), int(match.group(2))
        y1, y2 = int(match.group(3)), int(match.group(4))
        return cls(x1, x2, y1, y2)

    def __contains__(self, point: Vector) -> bool:
        return (
            self.min.x <= point.x <= self.max.x
            and self.min.y <= point.y <= self.max.y
        )


def decide_velocity_bounds(target_area: VectorBounds) -> VectorBounds:
    # This function establishes very broad limits for the range of velocities
    # we ought to consider. The general heuristic here is "don't try anything
    # with such high velocity that it'll just skip past the target area in one
    # step."
    assert target_area.min.x >= 0
    x_min = 0
    x_max = target_area.max.x + 1
    y_abs = max(abs(target_area.min.y), abs(target_area.max.y)) + 1
    return VectorBounds(x_min, x_max, -y_abs, +y_abs)


def drag_in_x(velocity: Vector) -> Vector:
    if velocity.x > 0:
        return Vector(-1, 0)
    if velocity.x < 0:
        return Vector(+1, 0)
    return Vector(0, 0)


GRAVITY: Final[Vector] = Vector(0, -1)


POSITION: Final[str] = 'position'
VELOCITY: Final[str] = 'velocity'
STEP: Final[str] = 'step'
MAX_HEIGHT: Final[str] = 'max_height'
MISSED: Final[str] = 'missed'


def simulate_trajectory(
    initial_velocity: Vector, target_area: VectorBounds,
) -> dict[str, Any]:
    state = {
        POSITION: Vector(0, 0),
        VELOCITY: initial_velocity,
        STEP: 0,
        MAX_HEIGHT: 0,
    }
    finished = False

    while not finished:

        state[STEP] += 1
        state[POSITION] += state[VELOCITY]
        state[MAX_HEIGHT] = max(state[MAX_HEIGHT], state[POSITION].y)
        state[VELOCITY] += GRAVITY + drag_in_x(state[VELOCITY])

        if state[POSITION] in target_area:
            state[MISSED] = False
            finished = True
        elif (
            state[POSITION].x > target_area.max.x
            or state[POSITION].y < target_area.min.y
        ):
            state[MISSED] = True
            finished = True

    return state


def part_1(file: pathlib.Path) -> None:
    target_area_string = file.read_text(encoding='ascii')
    target_area = VectorBounds.parse(target_area_string)

    velocity_bounds = decide_velocity_bounds(target_area)
    for vy in range(velocity_bounds.max.y, velocity_bounds.min.y - 1, -1):
        for vx in range(velocity_bounds.min.x, velocity_bounds.max.x + 1):

            initial_velocity = Vector(vx, vy)
            trajectory_report = simulate_trajectory(
                initial_velocity, target_area,
            )
            if not trajectory_report[MISSED]:
                print('part 1:', trajectory_report[MAX_HEIGHT])
                return

    raise RuntimeError('failed to find any best height')


def part_2(file: pathlib.Path) -> None:
    target_area_string = file.read_text(encoding='ascii')
    target_area = VectorBounds.parse(target_area_string)

    velocities_tally = 0
    velocity_bounds = decide_velocity_bounds(target_area)
    for vy in range(velocity_bounds.max.y, velocity_bounds.min.y - 1, -1):
        for vx in range(velocity_bounds.min.x, velocity_bounds.max.x + 1):

            initial_velocity = Vector(vx, vy)
            trajectory_report = simulate_trajectory(
                initial_velocity, target_area,
            )
            if not trajectory_report[MISSED]:
                velocities_tally += 1

    print('part 2:', velocities_tally)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
