from collections import Counter, deque
import pathlib
import sys
from typing import Final


END_OF_POLYMER: Final[str] = ':'


def parse_input_string(
    input_string: str,
) -> tuple[deque[str], dict[tuple[str, str], str]]:
    polymer_template_string, pair_insertion_rules_string = (
        input_string.strip().split('\n\n')
    )

    polymer_template = deque(polymer_template_string)
    polymer_template.append(END_OF_POLYMER)

    pair_insertion_rules: dict[tuple[str, str], str] = {}
    for line in pair_insertion_rules_string.strip().split('\n'):
        element_pair, element_to_insert = line.strip().split(' -> ')
        left_element, right_element = element_pair
        pair_insertion_rules[left_element, right_element] = element_to_insert

    return polymer_template, pair_insertion_rules


def apply_step_of_pair_insertion(
    polymer: deque[str], pair_insertion_rules: dict[tuple[str, str], str],
) -> None:
    if polymer[-1] != END_OF_POLYMER:
        raise RuntimeError('polymer deque is in an unexpected state')

    while polymer[1] != END_OF_POLYMER:
        element_pair = (polymer[0], polymer[1])
        element_to_insert = pair_insertion_rules[element_pair]
        polymer.rotate(-1)
        polymer.append(element_to_insert)

    polymer.rotate(-2)  # Move END_OF_POLYMER back around to the end


NUMBER_OF_STEPS: Final[int] = 10


def part_1(file: pathlib.Path) -> None:
    input_string = file.read_text(encoding='ascii')
    polymer_template, pair_insertion_rules = parse_input_string(input_string)

    polymer = polymer_template.copy()
    for _ in range(NUMBER_OF_STEPS):
        apply_step_of_pair_insertion(polymer, pair_insertion_rules)

    quantities = Counter(polymer)
    del quantities[END_OF_POLYMER]
    quantities_sorted_descending = quantities.most_common()

    _, largest_quantity = quantities_sorted_descending[0]
    _, smallest_quantity = quantities_sorted_descending[-1]
    print('part 1:', largest_quantity - smallest_quantity)


def part_2(file: pathlib.Path) -> None:
    file.read_text(encoding='ascii')
    print('part 2:', )


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
