import pathlib
import sys
from typing import Final


CHUNK_OPENERS: Final[frozenset[str]] = frozenset(['(', '[', '{', '<'])
CHUNK_CLOSERS: Final[frozenset[str]] = frozenset([')', ']', '}', '>'])

LEGAL_PAIRS: Final[frozenset[tuple[str, str]]] = frozenset([
    ('(', ')'), ('[', ']'), ('{', '}'), ('<', '>'),
])


def find_first_illegal_character(chunk_line: str) -> str | None:
    stack: list[str] = []

    for character in chunk_line:

        if character in CHUNK_OPENERS:
            stack.append(character)

        elif character in CHUNK_CLOSERS:
            opener = stack.pop()
            if (opener, character) not in LEGAL_PAIRS:
                return character

        else:
            raise ValueError(f'found unexpected character: {character!r}')

    return None


SYNTAX_ERROR_SCORING_TABLE: Final[dict[str | None, int]] = {
    ')': 3, ']': 57, '}': 1197, '>': 25137, None: 0,
}


def part_1(file: pathlib.Path) -> None:
    navigation_subsystem = file.read_text(encoding='ascii')
    chunk_lines = map(str.strip, navigation_subsystem.strip().split('\n'))

    syntax_error_score = 0

    for chunk_line in chunk_lines:
        first_illegal_character = find_first_illegal_character(chunk_line)
        points = SYNTAX_ERROR_SCORING_TABLE[first_illegal_character]
        syntax_error_score += points

    print('part 1:', syntax_error_score)


def is_not_corrupted(chunk_line: str) -> bool:
    return find_first_illegal_character(chunk_line) is None


MATCHING_CHUNK_CLOSER: Final[dict[str, str]] = dict(LEGAL_PAIRS)


def determine_completion_string(incomplete_line: str) -> str:
    stack: list[str] = []

    for character in incomplete_line:

        if character in CHUNK_OPENERS:
            stack.append(character)

        elif character in CHUNK_CLOSERS:
            opener = stack.pop()
            if (opener, character) not in LEGAL_PAIRS:
                raise ValueError('cannot complete a corrupted line')

        else:
            raise ValueError(f'found unexpected character: {character!r}')

    closers: list[str] = []
    while stack:
        opener = stack.pop()
        closer = MATCHING_CHUNK_CLOSER[opener]
        closers.append(closer)

    return ''.join(closers)


AUTOCOMPLETE_TOOL_SCORE_MULTIPLIER: Final[int] = 5

AUTOCOMPLETE_TOOL_SCORING_TABLE: Final[dict[str, int]] = {
    ')': 1, ']': 2, '}': 3, '>': 4,
}


def score_completion_string(completion_string: str) -> int:
    total_score = 0

    for character in completion_string:
        total_score *= AUTOCOMPLETE_TOOL_SCORE_MULTIPLIER
        total_score += AUTOCOMPLETE_TOOL_SCORING_TABLE[character]

    return total_score


def part_2(file: pathlib.Path) -> None:
    navigation_subsystem = file.read_text(encoding='ascii')
    chunk_lines = map(str.strip, navigation_subsystem.strip().split('\n'))

    incomplete_lines = filter(is_not_corrupted, chunk_lines)
    completion_strings = map(determine_completion_string, incomplete_lines)
    autocomplete_tool_scores = [
        score_completion_string(completion_string)
        for completion_string in completion_strings
    ]

    autocomplete_tool_scores.sort()
    middle_index = len(autocomplete_tool_scores) // 2
    middle_score = autocomplete_tool_scores[middle_index]
    print('part 2:', middle_score)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
