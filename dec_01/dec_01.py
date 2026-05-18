import pathlib
import sys


def part_1(file: pathlib.Path) -> None:
    file.read_text(encoding='ascii')
    print('part 1:', )


def part_2(file: pathlib.Path) -> None:
    file.read_text(encoding='ascii')
    print('part 2:', )


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
