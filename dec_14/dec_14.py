from collections import Counter, deque
import itertools
import pathlib
import sys
from typing import Final


def parse_input_string(input_string: str) -> tuple[str, dict[str, str]]:
    polymer_template_string, pair_insertion_rules_string = (
        input_string.strip().split('\n\n')
    )

    polymer_template = polymer_template_string.strip()

    pair_insertion_rules: dict[str, str] = {}
    for line in pair_insertion_rules_string.strip().split('\n'):
        element_pair, element_to_insert = line.strip().split(' -> ')
        pair_insertion_rules[element_pair.strip()] = element_to_insert.strip()

    return polymer_template, pair_insertion_rules


END_OF_POLYMER: Final[str] = ':'


def apply_pair_insertion_step(
    polymer: str, pair_insertion_rules: dict[str, str],
) -> str:
    if len(polymer) < 2:
        return polymer
    polymer_queue = deque(polymer)
    polymer_queue.append(END_OF_POLYMER)

    while polymer_queue[1] != END_OF_POLYMER:
        element_pair = polymer_queue[0] + polymer_queue[1]
        element_to_insert = pair_insertion_rules[element_pair]
        polymer_queue.rotate(-1)
        polymer_queue.append(element_to_insert)

    polymer_queue.rotate(-1)  # Move END_OF_POLYMER to the front of the queue
    assert polymer_queue.popleft() == END_OF_POLYMER
    return ''.join(polymer_queue)


NUMBER_OF_STEPS: Final[int] = 10


def part_1(file: pathlib.Path) -> None:
    input_string = file.read_text(encoding='ascii')
    polymer_template, pair_insertion_rules = parse_input_string(input_string)

    polymer = polymer_template
    for _ in range(NUMBER_OF_STEPS):
        polymer = apply_pair_insertion_step(polymer, pair_insertion_rules)

    quantities = Counter(polymer)
    quantities_sorted_descending = quantities.most_common()

    _, largest_quantity = quantities_sorted_descending[0]
    _, smallest_quantity = quantities_sorted_descending[-1]
    print('part 1:', largest_quantity - smallest_quantity)


def set_up_pair_counter(polymer: str) -> Counter[str]:
    if len(polymer) < 1:
        return Counter()
    pair_counter: Counter[str] = Counter()

    for left_element, right_element in itertools.pairwise(polymer):
        element_pair = left_element + right_element
        pair_counter[element_pair] += 1

    # This is important for making sure that every element is *consistently*
    # double-counted at the end
    pair_counter[polymer[0]] += 1
    pair_counter[polymer[-1]] += 1

    return pair_counter


def apply_pair_insertion_step_to_pair_counter(
    pair_counter: Counter[str], pair_insertion_rules: dict[str, str],
) -> Counter[str]:
    new_pair_counter: Counter[str] = Counter()

    for element_pair, count in pair_counter.items():

        if len(element_pair) == 1:
            new_pair_counter[element_pair] += count
            continue

        left_element, right_element = element_pair
        element_to_insert = pair_insertion_rules[element_pair]
        left_element_pair = left_element + element_to_insert
        right_element_pair = element_to_insert + right_element

        new_pair_counter[left_element_pair] += count
        new_pair_counter[right_element_pair] += count

    return new_pair_counter


def count_element_quantities(pair_counter: Counter[str]) -> Counter[str]:
    quantities: Counter[str] = Counter()

    for element_pair, count in pair_counter.items():
        for element in element_pair:
            quantities[element] += count

    # Every element is double-counted by the pair counter, so cut all the
    # quantities in half before returning
    for element in quantities:
        quantities[element] //= 2

    return quantities


LARGER_NUMBER_OF_STEPS: Final[int] = 40


def part_2(file: pathlib.Path) -> None:
    input_string = file.read_text(encoding='ascii')
    polymer_template, pair_insertion_rules = parse_input_string(input_string)

    # I really like the queue-based solution that I wrote for part 1, so I'm
    # not going to delete that code, but it just won't cut it for part 2. No
    # approach that needs to explicitly store the entire polymer in memory at
    # once has any hope of success with less than 1 TB of available RAM. I'll
    # use a dictionary subclass to carefully tally up the pairs instead.
    pair_counter = set_up_pair_counter(polymer_template)
    for _ in range(LARGER_NUMBER_OF_STEPS):
        pair_counter = apply_pair_insertion_step_to_pair_counter(
            pair_counter, pair_insertion_rules,
        )

    quantities = count_element_quantities(pair_counter)
    quantities_sorted_descending = quantities.most_common()

    _, largest_quantity = quantities_sorted_descending[0]
    _, smallest_quantity = quantities_sorted_descending[-1]
    print('part 2:', largest_quantity - smallest_quantity)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
