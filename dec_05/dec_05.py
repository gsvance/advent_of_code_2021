import pathlib
import sys
from typing import NamedTuple


class Point(NamedTuple):
    x: int
    y: int


def parse_point(point_string: str) -> Point:
    x_string, y_string = point_string.strip().split(',')
    x = int(x_string.strip())
    y = int(y_string.strip())
    return Point(x, y)


def sign(x: int) -> int:
    if x > 0:
        return +1
    if x < 0:
        return -1
    return 0


class Step(NamedTuple):
    dx: int
    dy: int


def compute_unit_step(from_point: Point, to_point: Point) -> Step:
    x_diff = to_point.x - from_point.x
    y_diff = to_point.y - from_point.y
    return Step(sign(x_diff), sign(y_diff))


def move_point(point: Point, step: Step) -> Point:
    return Point(point.x + step.dx, point.y + step.dy)


class Line(NamedTuple):
    p1: Point
    p2: Point


def parse_vent_lines(list_of_lines_of_vents: str) -> list[Line]:
    vent_lines: list[Line] = []
    for line_of_text in list_of_lines_of_vents.strip().split('\n'):
        p1_string, p2_string = line_of_text.strip().split('->')
        p1 = parse_point(p1_string)
        p2 = parse_point(p2_string)
        vent_lines.append(Line(p1, p2))
    return vent_lines


def is_horizontal(line: Line) -> bool:
    return line.p1.y == line.p2.y


def is_vertical(line: Line) -> bool:
    return line.p1.x == line.p2.x


def add_vents_to_diagram(diagram: dict[Point, int], vent_line: Line) -> None:
    step = compute_unit_step(vent_line.p1, vent_line.p2)
    vent = vent_line.p1
    diagram[vent] = diagram.get(vent, 0) + 1
    while vent != vent_line.p2:
        vent = move_point(vent, step)
        diagram[vent] = diagram.get(vent, 0) + 1


def part_1(file: pathlib.Path) -> None:
    list_of_lines_of_vents = file.read_text(encoding='ascii')
    vent_lines = parse_vent_lines(list_of_lines_of_vents)

    diagram: dict[Point, int] = {}
    for vent_line in vent_lines:
        if is_horizontal(vent_line) or is_vertical(vent_line):
            add_vents_to_diagram(diagram, vent_line)

    number_of_overlaps = sum(1 for number in diagram.values() if number >= 2)
    print('part 1:', number_of_overlaps)


def part_2(file: pathlib.Path) -> None:
    list_of_lines_of_vents = file.read_text(encoding='ascii')
    vent_lines = parse_vent_lines(list_of_lines_of_vents)

    diagram: dict[Point, int] = {}
    for vent_line in vent_lines:
        add_vents_to_diagram(diagram, vent_line)

    number_of_overlaps = sum(1 for number in diagram.values() if number >= 2)
    print('part 2:', number_of_overlaps)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
