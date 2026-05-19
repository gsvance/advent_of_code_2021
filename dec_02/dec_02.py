from dataclasses import dataclass
from enum import StrEnum
import pathlib
import sys
from typing import Self


class Direction(StrEnum):
    FORWARD = 'forward'
    DOWN = 'down'
    UP = 'up'


@dataclass(frozen=True, match_args=False, slots=True)
class Command:
    direction: Direction
    units: int

    @classmethod
    def parse(cls, command_string: str) -> Self:
        direction_string, units_string = command_string.strip().split()
        direction = Direction(direction_string)
        units = int(units_string)
        return cls(direction, units)


def parse_commands(planned_course: str) -> list[Command]:
    return list(map(Command.parse, planned_course.strip().split('\n')))


@dataclass(match_args=False, slots=True)
class Submarine:
    horizontal: int
    depth: int


def chart_course(commands: list[Command]) -> Submarine:
    submarine = Submarine(horizontal=0, depth=0)

    for command in commands:
        match command.direction:
            case Direction.FORWARD:
                submarine.horizontal += command.units
            case Direction.DOWN:
                submarine.depth += command.units
            case Direction.UP:
                submarine.depth -= command.units
            case _:
                raise RuntimeError(f'invalid command: {command!r}')

    return submarine


def part_1(file: pathlib.Path) -> None:
    planned_course = file.read_text(encoding='ascii')
    commands = parse_commands(planned_course)
    final_position = chart_course(commands)
    print('part 1:', final_position.horizontal * final_position.depth)


@dataclass(match_args=False, kw_only=True, slots=True)
class AimedSubmarine:
    horizontal: int
    depth: int
    aim: int


def chart_aimed_course(commands: list[Command]) -> AimedSubmarine:
    submarine = AimedSubmarine(horizontal=0, depth=0, aim=0)

    for command in commands:
        match command.direction:
            case Direction.FORWARD:
                submarine.horizontal += command.units
                submarine.depth += submarine.aim * command.units
            case Direction.DOWN:
                submarine.aim += command.units
            case Direction.UP:
                submarine.aim -= command.units
            case _:
                raise RuntimeError(f'invalid command: {command!r}')

    return submarine


def part_2(file: pathlib.Path) -> None:
    planned_course = file.read_text(encoding='ascii')
    commands = parse_commands(planned_course)
    final_position = chart_aimed_course(commands)
    print('part 2:', final_position.horizontal * final_position.depth)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
