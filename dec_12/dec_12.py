import pathlib
import sys
from typing import Final, NamedTuple, Self


class CavesGraph:

    def __init__(self, edges: list[tuple[str, str]]) -> None:
        self.adjacency_set: dict[str, set[str]] = {}

        for cave_1, cave_2 in edges:

            if cave_1 not in self.adjacency_set:
                self.adjacency_set[cave_1] = set()
            if cave_2 not in self.adjacency_set:
                self.adjacency_set[cave_2] = set()

            self.adjacency_set[cave_1].add(cave_2)
            self.adjacency_set[cave_2].add(cave_1)

    @classmethod
    def parse(cls, rough_map_of_caves: str) -> Self:
        edges: list[tuple[str, str]] = []

        for line in rough_map_of_caves.strip().split('\n'):
            cave_1, cave_2 = line.strip().split('-')
            edges.append((cave_1, cave_2))

        return cls(edges)

    def neighbors(self, cave: str) -> frozenset[str]:
        return frozenset(self.adjacency_set[cave])


class CaveWalker(NamedTuple):
    current_location: str
    small_caves_visited: frozenset[str]


def is_a_small_cave(cave: str) -> bool:
    if cave.islower():
        return True
    if cave.isupper():
        return False
    raise ValueError(f'cave {cave!r} is neither small nor big')


def take_a_step(walker: CaveWalker, next_cave: str) -> CaveWalker:
    if is_a_small_cave(next_cave):
        small_caves_visited = (
            walker.small_caves_visited | frozenset([next_cave])
        )
        return CaveWalker(
            current_location=next_cave,
            small_caves_visited=small_caves_visited,
        )

    # The next cave is a big cave
    return CaveWalker(
        current_location=next_cave,
        small_caves_visited=walker.small_caves_visited,
    )


START: Final[str] = 'start'
END: Final[str] = 'end'


def count_paths(caves: CavesGraph) -> int:
    paths_tally = 0
    active_walkers = [
        CaveWalker(
            current_location=START, small_caves_visited=frozenset([START]),
        ),
    ]

    while active_walkers:

        walker = active_walkers.pop()
        if walker.current_location == END:
            paths_tally += 1
            continue

        possible_next_steps = (
            caves.neighbors(walker.current_location)
            - walker.small_caves_visited
        )

        for next_cave in possible_next_steps:
            next_walker = take_a_step(walker, next_cave)
            active_walkers.append(next_walker)

    return paths_tally


def part_1(file: pathlib.Path) -> None:
    rough_map_of_caves = file.read_text(encoding='ascii')
    caves = CavesGraph.parse(rough_map_of_caves)
    number_of_paths = count_paths(caves)
    print('part 1:', number_of_paths)


class RevisitingCaveWalker(NamedTuple):
    current_location: str
    small_caves_visited: frozenset[str]
    revisited_a_small_cave: bool


def take_a_step_with_revisiting(
    walker: RevisitingCaveWalker, next_cave: str,
) -> RevisitingCaveWalker:
    if not is_a_small_cave(next_cave):
        return RevisitingCaveWalker(
            current_location=next_cave,
            small_caves_visited=walker.small_caves_visited,
            revisited_a_small_cave=walker.revisited_a_small_cave,
        )

    # The next cave is a small cave
    if walker.revisited_a_small_cave:
        small_caves_visited = (
            walker.small_caves_visited | frozenset([next_cave])
        )
        return RevisitingCaveWalker(
            current_location=next_cave,
            small_caves_visited=small_caves_visited,
            revisited_a_small_cave=True,
        )

    # The next cave is a small cave and we haven't revisited a small cave yet
    small_caves_visited = walker.small_caves_visited | frozenset([next_cave])
    revisited_a_small_cave = next_cave in walker.small_caves_visited
    return RevisitingCaveWalker(
        current_location=next_cave,
        small_caves_visited=small_caves_visited,
        revisited_a_small_cave=revisited_a_small_cave,
    )


def count_paths_with_revisiting(caves: CavesGraph) -> int:
    paths_tally = 0
    active_walkers = [
        RevisitingCaveWalker(
            current_location=START,
            small_caves_visited=frozenset([START]),
            revisited_a_small_cave=False,
        ),
    ]

    while active_walkers:

        walker = active_walkers.pop()
        if walker.current_location == END:
            paths_tally += 1
            continue

        if walker.revisited_a_small_cave:
            possible_next_steps = (
                caves.neighbors(walker.current_location)
                - walker.small_caves_visited
            )
        else:  # We haven't revisited a small cave yet
            possible_next_steps = (
                caves.neighbors(walker.current_location) - frozenset([START])
            )

        for next_cave in possible_next_steps:
            next_walker = take_a_step_with_revisiting(walker, next_cave)
            active_walkers.append(next_walker)

    return paths_tally


def part_2(file: pathlib.Path) -> None:
    rough_map_of_caves = file.read_text(encoding='ascii')
    caves = CavesGraph.parse(rough_map_of_caves)
    number_of_paths = count_paths_with_revisiting(caves)
    print('part 2:', number_of_paths)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
