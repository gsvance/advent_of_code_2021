import pathlib
import sys
from typing import Final, NamedTuple, Self


class CavesGraph:

    def __init__(self, edges: list[tuple[str, str]]) -> None:
        self.edges: dict[str, set[str]] = {}

        for cave_1, cave_2 in edges:
            if cave_1 not in self.edges:
                self.edges[cave_1] = set()
            if cave_2 not in self.edges:
                self.edges[cave_2] = set()
            self.edges[cave_1].add(cave_2)
            self.edges[cave_2].add(cave_1)

    @classmethod
    def parse(cls, rough_map_of_caves: str) -> Self:
        edges: list[tuple[str, str]] = []
        for line in rough_map_of_caves.strip().split('\n'):
            cave_1, cave_2 = line.strip().split('-')
            edges.append((cave_1, cave_2))
        return cls(edges)

    def neighbors(self, cave: str) -> frozenset[str]:
        return frozenset(self.edges[cave])


class Walker(NamedTuple):
    location: str
    small_caves_visited: frozenset[str]


def is_small_cave(cave: str) -> bool:
    if cave.islower():
        return True
    if cave.isupper():
        return False
    raise ValueError(f'cave {cave!r} is neither small nor big')


def take_a_step(walker: Walker, next_cave: str) -> Walker:
    if is_small_cave(next_cave):
        return Walker(
            location=next_cave,
            small_caves_visited=(
                walker.small_caves_visited | frozenset([next_cave])
            ),
        )
    return Walker(
        location=next_cave, small_caves_visited=walker.small_caves_visited,
    )


START: Final[str] = 'start'
END: Final[str] = 'end'


def count_paths(caves: CavesGraph) -> int:
    tally = 0
    queue = [
        Walker(location=START, small_caves_visited=frozenset([START])),
    ]

    while queue:
        walker = queue.pop()
        if walker.location == END:
            tally += 1
            continue
        possible_next_steps = (
            caves.neighbors(walker.location) - walker.small_caves_visited
        )
        for next_cave in possible_next_steps:
            next_walker = take_a_step(walker, next_cave)
            queue.append(next_walker)

    return tally


def part_1(file: pathlib.Path) -> None:
    rough_map_of_caves = file.read_text(encoding='ascii')
    caves = CavesGraph.parse(rough_map_of_caves)

    number_of_paths = count_paths(caves)

    print('part 1:', number_of_paths)


class RevisitingWalker(NamedTuple):
    location: str
    small_caves_visited: frozenset[str]
    revisited_a_small_cave: bool


def take_a_step_revisiting(
    walker: RevisitingWalker, next_cave: str,
) -> RevisitingWalker:
    if is_small_cave(next_cave) and walker.revisited_a_small_cave:
        return RevisitingWalker(
            location=next_cave,
            small_caves_visited=(
                walker.small_caves_visited | frozenset([next_cave])
            ),
            revisited_a_small_cave=True,
        )
    if is_small_cave(next_cave) and not walker.revisited_a_small_cave:
        return RevisitingWalker(
            location=next_cave,
            small_caves_visited=(
                walker.small_caves_visited | frozenset([next_cave])
            ),
            revisited_a_small_cave=(next_cave in walker.small_caves_visited),
        )
    return RevisitingWalker(
        location=next_cave,
        small_caves_visited=walker.small_caves_visited,
        revisited_a_small_cave=walker.revisited_a_small_cave,
    )


def count_paths_revisiting(caves: CavesGraph) -> int:
    tally = 0
    queue = [
        RevisitingWalker(
            location=START,
            small_caves_visited=frozenset([START]),
            revisited_a_small_cave=False,
        ),
    ]

    while queue:
        walker = queue.pop()
        if walker.location == END:
            tally += 1
            continue
        if walker.revisited_a_small_cave:
            possible_next_steps = (
                caves.neighbors(walker.location) - walker.small_caves_visited
            )
        else:
            possible_next_steps = (
                caves.neighbors(walker.location) - frozenset([START])
            )
        for next_cave in possible_next_steps:
            next_walker = take_a_step_revisiting(walker, next_cave)
            queue.append(next_walker)

    return tally


def part_2(file: pathlib.Path) -> None:
    rough_map_of_caves = file.read_text(encoding='ascii')
    caves = CavesGraph.parse(rough_map_of_caves)

    number_of_paths = count_paths_revisiting(caves)

    print('part 2:', number_of_paths)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
