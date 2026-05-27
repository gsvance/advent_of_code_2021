from dataclasses import dataclass
import itertools
import pathlib
import re
import sys
from typing import Final, Self


SEGMENT_LETTERS: Final[frozenset[str]] = frozenset('abcdefg')


@dataclass(init=False, repr=False, frozen=True, match_args=False, slots=True)
class Segments:
    letters: str

    def __init__(self, letters: str) -> None:
        unique_letters = frozenset(letters)
        if not unique_letters.issubset(SEGMENT_LETTERS):
            raise ValueError(f'invalid segment letters string: {letters!r}')
        sorted_letters = sorted(unique_letters)
        letters_string = ''.join(sorted_letters)
        object.__setattr__(self, 'letters', letters_string)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.letters!r})'

    def __len__(self) -> int:
        return len(self.letters)


PATTERNS_LENGTH: Final[int] = 10
OUTPUTS_LENGTH: Final[int] = 4


@dataclass(frozen=True, match_args=False, slots=True)
class NotesEntry:
    patterns: tuple[Segments, ...]
    outputs: tuple[Segments, ...]

    @classmethod
    def from_strings(cls, patterns_string: str, outputs_string: str) -> Self:
        patterns = tuple(map(Segments, patterns_string.strip().split()))
        outputs = tuple(map(Segments, outputs_string.strip().split()))
        return cls(patterns, outputs)

    def __post_init__(self) -> None:
        if len(self.patterns) != PATTERNS_LENGTH:
            raise ValueError(
                f'notes entry should have exactly {PATTERNS_LENGTH} patterns'
            )
        if len(self.outputs) != OUTPUTS_LENGTH:
            raise ValueError(
                f'notes entry should have exactly {OUTPUTS_LENGTH} outputs'
            )


NOTES_ENTRY_REGEX: Final[re.Pattern[str]] = re.compile(
    r''' ^(
        (?:[a-z]{1,7}\s*){10}
    ) \| (
        (?:\s*[a-z]{1,7}){4}
    )$ ''',
    re.ASCII | re.MULTILINE | re.VERBOSE,
)


def parse_notes_entries(my_notes: str) -> list[NotesEntry]:
    entries: list[NotesEntry] = []
    for match in NOTES_ENTRY_REGEX.finditer(my_notes):
        patterns_string = str(match.group(1))
        outputs_string = str(match.group(2))
        entry = NotesEntry.from_strings(patterns_string, outputs_string)
        entries.append(entry)
    return entries


SEGMENTS_FOR_DIGIT: Final[dict[int, Segments]] = {
    0: Segments('abcefg'),
    1: Segments('cf'),
    2: Segments('acdeg'),
    3: Segments('acdfg'),
    4: Segments('bcdf'),
    5: Segments('abdfg'),
    6: Segments('abdefg'),
    7: Segments('acf'),
    8: Segments('abcdefg'),
    9: Segments('abcdfg'),
}


def filter_to_unique_values[K, V](dictionary: dict[K, V]) -> dict[K, V]:
    value_counts: dict[V, int] = {}
    for value in dictionary.values():
        value_counts[value] = value_counts.get(value, 0) + 1

    filtered_dictionary = {
        key: value for key, value in dictionary.items()
        if value_counts[value] == 1
    }
    return filtered_dictionary


UNIQUE_SEGMENTS_LENGTHS: Final[dict[int, int]] = filter_to_unique_values({
    digit: len(segments) for digit, segments in SEGMENTS_FOR_DIGIT.items()
})


def part_1(file: pathlib.Path) -> None:
    my_notes = file.read_text(encoding='ascii')
    entries = parse_notes_entries(my_notes)

    if frozenset(UNIQUE_SEGMENTS_LENGTHS.keys()) != frozenset([1, 4, 7, 8]):
        raise RuntimeError('unique segments lengths has unexpected keyset')

    count_of_1_4_7_8 = 0
    for entry in entries:
        for segments in entry.outputs:
            if len(segments) in UNIQUE_SEGMENTS_LENGTHS.values():
                count_of_1_4_7_8 += 1

    print('part 1:', count_of_1_4_7_8)


def remap_signal_wires(
    segments: Segments, wire_mapping: dict[str, str],
) -> Segments:
    translation_table = str.maketrans(wire_mapping)
    new_letters = segments.letters.translate(translation_table)
    return Segments(new_letters)


def generate_lookup_table() -> dict[frozenset[Segments], dict[Segments, int]]:
    lookup_table: dict[frozenset[Segments], dict[Segments, int]] = {}
    sorted_letters = tuple(sorted(SEGMENT_LETTERS))

    for permutation in itertools.permutations(sorted_letters):
        wire_mapping = dict(zip(sorted_letters, permutation))
        patterns: set[Segments] = set()
        digit_mapping: dict[Segments, int] = {}

        for digit, segments in SEGMENTS_FOR_DIGIT.items():
            new_segments = remap_signal_wires(segments, wire_mapping)
            patterns.add(new_segments)
            digit_mapping[new_segments] = digit

        lookup_table[frozenset(patterns)] = digit_mapping

    return lookup_table


def decode_output_value(
    outputs: tuple[Segments, ...], digit_mapping: dict[Segments, int],
) -> int:
    output_value = 0
    for segments in outputs:
        output_value = 10 * output_value + digit_mapping[segments]
    return output_value


def part_2(file: pathlib.Path) -> None:
    my_notes = file.read_text(encoding='ascii')
    entries = parse_notes_entries(my_notes)

    # If I wrote messy bespoke checks for each digit individually, I could
    # probably come up with a working solution that runs pretty fast. However,
    # I would rather write something more generic that doesn't rely explicitly
    # on these particular 10 digits. Since there are only 7! (or about 5,000)
    # permutations of the mixed-up wires in the problem, just generate all of
    # them and then do a simple lookup for each notes entry.
    lookup_table = generate_lookup_table()

    sum_of_output_values = 0
    for entry in entries:
        digit_mapping = lookup_table[frozenset(entry.patterns)]
        output_value = decode_output_value(entry.outputs, digit_mapping)
        sum_of_output_values += output_value

    print('part 2:', sum_of_output_values)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
