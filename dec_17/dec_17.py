from dataclasses import dataclass
import pathlib
import sys
from typing import Final, Self


@dataclass(frozen=True, slots=True)
class Vector:
    x: int
    y: int

    def __add__(self, other: Self) -> Self:
        return self.__class__(self.x + other.x, self.y + other.y)


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
    def parse(cls, vector_bounds_string: str) -> Self:
        x_piece, y_piece = vector_bounds_string.strip().split(', ')
        x1, x2 = x_piece.removeprefix('x=').split('..')
        y1, y2 = y_piece.removeprefix('y=').split('..')
        return cls(int(x1), int(x2), int(y1), int(y2))

    @property
    def x_values(self) -> range:
        return range(self.min.x, self.max.x + 1)

    @property
    def y_values(self) -> range:
        return range(self.min.y, self.max.y + 1)

    def __contains__(self, point: Vector) -> bool:
        return (
            self.min.x <= point.x <= self.max.x
            and self.min.y <= point.y <= self.max.y
        )


def parse_target_area(target_area_string: str) -> VectorBounds:
    vector_bounds_string = (
        target_area_string.strip().removeprefix('target area: ')
    )
    return VectorBounds.parse(vector_bounds_string)


INITIAL_POSITION: Final[Vector] = Vector(0, 0)
GRAVITY: Final[Vector] = Vector(0, -1)


def compute_drag_in_x(velocity: Vector) -> Vector:
    match velocity:
        case Vector(vx, _) if vx > 0:
            return Vector(-1, 0)
        case Vector(vx, _) if vx < 0:
            return Vector(+1, 0)
        case Vector(0, _):
            return Vector(0, 0)
        case _:
            raise RuntimeError('unreachable code')


def decide_velocity_bounds(target_area: VectorBounds) -> VectorBounds:
    # First, verify a few basic assumptions about where the target area is
    # relative to the probe's starting position and how physics works.
    assert INITIAL_POSITION.x < target_area.min.x  # Target is rightward
    assert INITIAL_POSITION.y > target_area.max.y  # Target is downward
    assert GRAVITY.x == 0 and GRAVITY.y < 0  # Gravity pulls downward
    test_drag = compute_drag_in_x(velocity=Vector(+1, 0))
    assert test_drag.x < 0  # Drag resists rightward motion
    assert test_drag.y == 0  # Drag doesn't happen vertically

    # Here we establish very broad limits for the range of velocities we ought
    # to consider. The general heuristic here is "don't try anything with such
    # high velocity that it'll just skip past the target area in one step."
    vx_max = (target_area.max.x - INITIAL_POSITION.x) + 1
    vy_max_absolute = abs(target_area.min.y - INITIAL_POSITION.y) + 1

    # Use trial-and-error to figure out the minimum x velocity needed in order
    # to overcome drag and just reach the leftmost edge of the target area.
    vx_min: int | None = None
    for vx in range(vx_max + 1):
        x = INITIAL_POSITION.x
        while vx > 0:
            x += vx
            vx += compute_drag_in_x(Vector(vx, 0)).x
        if x >= target_area.min.x:
            vx_min = vx
            break

    assert vx_min is not None
    return VectorBounds(vx_min, vx_max, -vy_max_absolute, +vy_max_absolute)


@dataclass(match_args=False, slots=True)
class ProbeState:
    step: int
    position: Vector
    max_height: int
    velocity: Vector

    def simulate_one_step(self) -> None:
        self.step += 1
        self.position += self.velocity
        self.max_height = max(self.max_height, self.position.y)
        self.velocity += GRAVITY + compute_drag_in_x(self.velocity)


@dataclass(frozen=True, match_args=False, slots=True)
class ProbeReport:
    missed: bool
    max_height: int


def simulate_trajectory(
    initial_velocity: Vector, target_area: VectorBounds,
) -> ProbeReport:
    probe = ProbeState(
        step=0,
        position=INITIAL_POSITION,
        max_height=INITIAL_POSITION.y,
        velocity=initial_velocity,
    )

    while True:
        probe.simulate_one_step()

        if probe.position in target_area:
            return ProbeReport(missed=False, max_height=probe.max_height)
        if (
            probe.position.x > target_area.max.x
            or probe.position.y < target_area.min.y
        ):
            return ProbeReport(missed=True, max_height=probe.max_height)


def part_1(file: pathlib.Path) -> None:
    target_area_string = file.read_text(encoding='ascii')
    target_area = parse_target_area(target_area_string)

    velocity_bounds = decide_velocity_bounds(target_area)
    for vy in reversed(velocity_bounds.y_values):
        for vx in velocity_bounds.x_values:

            trajectory_report = simulate_trajectory(
                initial_velocity=Vector(vx, vy), target_area=target_area,
            )
            if not trajectory_report.missed:
                print('part 1:', trajectory_report.max_height)
                return

    raise RuntimeError('part 1 loop failed to find any max height')


def part_2(file: pathlib.Path) -> None:
    target_area_string = file.read_text(encoding='ascii')
    target_area = parse_target_area(target_area_string)

    acceptable_initial_velocities_tally = 0
    velocity_bounds = decide_velocity_bounds(target_area)
    for vy in reversed(velocity_bounds.y_values):
        for vx in velocity_bounds.x_values:

            trajectory_report = simulate_trajectory(
                initial_velocity=Vector(vx, vy), target_area=target_area,
            )
            if not trajectory_report.missed:
                acceptable_initial_velocities_tally += 1

    print('part 2:', acceptable_initial_velocities_tally)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
