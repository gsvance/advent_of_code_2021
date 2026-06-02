from pathlib import Path
from typing import Final


NEW_SCRIPT_CONTENTS: Final[str] = '''


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


'''.strip() + '\n'


def main() -> None:
    existing_folders = [
        item for item in Path('.').glob('dec_*') if item.is_dir()]
    existing_numbers = [
        int(folder.name.removeprefix('dec_')) for folder in existing_folders
    ]
    assert set(existing_numbers) == set(range(1, len(existing_numbers) + 1))

    next_number = len(existing_numbers) + 1
    if next_number > 25:
        print('Error: there are already 25 problem folders')
        return

    next_folder = Path('.', f'dec_{next_number:02d}')
    next_script = next_folder / f'{next_folder.name}.py'
    next_example_1 = next_folder / 'example_01.txt'
    next_input = next_folder / 'input.txt'

    next_folder.mkdir()
    next_script.write_text(NEW_SCRIPT_CONTENTS)
    next_example_1.write_text('')
    next_input.write_text('')

    print(f'New folder created: {next_folder.name!s}/')


if __name__ == '__main__':
    main()
