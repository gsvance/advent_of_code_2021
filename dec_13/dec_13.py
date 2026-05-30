import pathlib
import sys
from typing import Final, NamedTuple


class Point(NamedTuple):
    x: int
    y: int


def parse_random_dots(random_dots_string: str) -> set[Point]:
    random_dots: set[Point] = set()

    for line in random_dots_string.strip().split('\n'):
        x_string, y_string = line.strip().split(',')
        dot = Point(int(x_string), int(y_string))
        random_dots.add(dot)

    return random_dots


type Instruction = tuple[str, int]


def parse_folding_instructions(
    folding_instructions_string: str,
) -> list[Instruction]:
    folding_instructions: list[Instruction] = []

    for line in folding_instructions_string.strip().split('\n'):
        x_or_y, value = line.strip().removeprefix('fold along ').split('=')
        instruction: Instruction = (x_or_y, int(value))
        folding_instructions.append(instruction)

    return folding_instructions


def parse_input_string(
    input_string: str,
) -> tuple[set[Point], list[Instruction]]:
    random_dots_string, folding_instructions_string = (
        input_string.strip().split('\n\n')
    )
    random_dots = parse_random_dots(random_dots_string)
    folding_instructions = parse_folding_instructions(
        folding_instructions_string,
    )
    return random_dots, folding_instructions


def complete_fold_instruction(
    random_dots: set[Point], instruction: Instruction,
) -> None:
    moving_dots: set[Point] = set()
    for dot in random_dots:
        match instruction:
            case ('x', x):
                dot_is_moving = dot.x > x
            case ('y', y):
                dot_is_moving = dot.y > y
            case _:
                raise ValueError(f'invalid instruction: {instruction!r}')
        if dot_is_moving:
            moving_dots.add(dot)

    for dot in moving_dots:
        random_dots.remove(dot)
        match instruction:
            case ('x', x):
                moved_dot = Point(2 * x - dot.x, dot.y)
            case ('y', y):
                moved_dot = Point(dot.x, 2 * y - dot.y)
            case _:
                raise ValueError(f'invalid instruction: {instruction!r}')
        random_dots.add(moved_dot)


NUMBER_OF_INITIAL_FOLDS: Final[int] = 1


def part_1(file: pathlib.Path) -> None:
    input_string = file.read_text(encoding='ascii')
    random_dots, folding_instructions = parse_input_string(input_string)

    for instruction in folding_instructions[:NUMBER_OF_INITIAL_FOLDS]:
        complete_fold_instruction(random_dots, instruction)

    print('part 1:', len(random_dots))


DOT: Final[str] = '#'
EMPTY: Final[str] = '.'


def render_output_string(random_dots: set[Point]) -> str:
    min_x = min(dot.x for dot in random_dots)
    max_x = max(dot.x for dot in random_dots)
    min_y = min(dot.y for dot in random_dots)
    max_y = max(dot.y for dot in random_dots)

    lines: list[str] = []

    for y in range(min_y, max_y + 1):
        characters: list[str] = []
        for x in range(min_x, max_x + 1):
            dot = Point(x, y)
            characters.append(DOT if dot in random_dots else EMPTY)
        lines.append(''.join(characters))

    return '\n'.join(lines)


def part_2(file: pathlib.Path) -> None:
    input_string = file.read_text(encoding='ascii')
    random_dots, folding_instructions = parse_input_string(input_string)

    for instruction in folding_instructions:
        complete_fold_instruction(random_dots, instruction)

    output_string = render_output_string(random_dots)
    print('part 2:', output_string, sep='\n')


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
