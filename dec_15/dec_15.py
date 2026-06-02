from collections.abc import Iterator
from dataclasses import dataclass, field
import heapq
import pathlib
import sys
from typing import Final, NamedTuple, Self


class Point(NamedTuple):
    r: int
    c: int


def iter_neighbors(point: Point) -> Iterator[Point]:
    for dr, dc in ((+1, 0), (-1, 0), (0, +1), (0, -1)):
        yield Point(r=point.r + dr, c=point.c + dc)


class RiskLevelMap:

    def __init__(self, map_rows: list[list[int]]) -> None:
        self.map_rows: list[list[int]] = map_rows
        self.n_rows: int = len(self.map_rows)
        row_lengths = {len(row) for row in self.map_rows}
        if len(row_lengths) != 1:
            raise TypeError('map has inconsistent number of columns')
        self.n_cols: int = row_lengths.pop()

    @classmethod
    def parse(cls, chiton_density_scan: str) -> Self:
        map_rows: list[list[int]] = []
        for line in chiton_density_scan.strip().split('\n'):
            map_row = [int(digit) for digit in line.strip()]
            map_rows.append(map_row)
        return cls(map_rows)

    def iter_points(self) -> Iterator[Point]:
        for r in range(self.n_rows):
            for c in range(self.n_cols):
                yield Point(r=r, c=c)

    def get_risk_level(self, point: Point) -> int | None:
        if point.r not in range(self.n_rows):
            return None
        if point.c not in range(self.n_cols):
            return None
        return self.map_rows[point.r][point.c]


@dataclass(order=True, match_args=False, slots=True)
class PriorityQueueEntry[T]:
    priority: int
    item: T = field(compare=False)
    removed: bool = field(default=False, compare=False)


class PriorityQueue[T]:

    __slots__ = ('heap', 'entry_finder')

    def __init__(self) -> None:
        self.heap: list[PriorityQueueEntry[T]] = []
        self.entry_finder: dict[T, PriorityQueueEntry[T]] = {}

    def remove(self, item: T) -> None:
        entry = self.entry_finder.pop(item)
        entry.removed = True

    def add_with_priority(self, item: T, priority: int) -> None:
        if item in self.entry_finder:
            self.remove(item)
        entry = PriorityQueueEntry(priority, item)
        self.entry_finder[item] = entry
        heapq.heappush(self.heap, entry)

    def pop_min_priority(self) -> T:
        while self.heap:
            entry = heapq.heappop(self.heap)
            if not entry.removed:
                del self.entry_finder[entry.item]
                return entry.item
        raise IndexError('pop min priority with empty priority queue')

    def is_empty(self) -> bool:
        return not bool(self.entry_finder)


def risk_heuristic(point_a: Point, point_b: Point) -> int:
    abs_dr = abs(point_b.r - point_a.r)
    abs_dc = abs(point_b.c - point_a.c)
    return abs_dr + abs_dc  # Taxicab distance


HUGE: Final[int] = 2 ** 63 - 1


def find_least_risky_path(
    cavern_map: RiskLevelMap, start: Point, finish: Point,
) -> int:
    known_risk_so_far: dict[Point, int] = {}
    frontier_queue: PriorityQueue[Point] = PriorityQueue()

    known_risk_so_far[start] = 0
    frontier_queue.add_with_priority(start, risk_heuristic(start, finish))

    while not frontier_queue.is_empty():

        current = frontier_queue.pop_min_priority()
        if current == finish:
            return known_risk_so_far[finish]

        for neighbor in iter_neighbors(current):
            risk_level = cavern_map.get_risk_level(neighbor)
            if risk_level is None:
                continue
            new_risk_level = known_risk_so_far[current] + risk_level
            if new_risk_level < known_risk_so_far.get(neighbor, HUGE):
                known_risk_so_far[neighbor] = new_risk_level
                priority = new_risk_level + risk_heuristic(neighbor, finish)
                frontier_queue.add_with_priority(neighbor, priority)

    raise RuntimeError('path finding terminated without finding a path')


def part_1(file: pathlib.Path) -> None:
    chiton_density_scan = file.read_text(encoding='ascii')
    cavern_map = RiskLevelMap.parse(chiton_density_scan)

    start = Point(r=0, c=0)
    finish = Point(r=cavern_map.n_rows - 1, c=cavern_map.n_cols - 1)
    lowest_total_risk = find_least_risky_path(cavern_map, start, finish)

    print('part 1:', lowest_total_risk)


RISK_LEVEL_MODULUS: Final[int] = 9


def wrap_risk_level(risk_level: int) -> int:
    return (risk_level - 1) % RISK_LEVEL_MODULUS + 1


def expand_cavern_map(cavern_map: RiskLevelMap, factor: int) -> RiskLevelMap:
    expanded_map_rows: list[list[int]] = []

    for expanded_r in range(factor * cavern_map.n_rows):
        expanded_row: list[int] = []

        for expanded_c in range(factor * cavern_map.n_cols):
            wrapped_point = Point(
                r=expanded_r % cavern_map.n_rows,
                c=expanded_c % cavern_map.n_cols,
            )
            risk_level = cavern_map.get_risk_level(wrapped_point)
            assert risk_level is not None
            risk_level = wrap_risk_level(
                risk_level
                + expanded_r // cavern_map.n_rows
                + expanded_c // cavern_map.n_cols
            )
            expanded_row.append(risk_level)

        expanded_map_rows.append(expanded_row)

    return RiskLevelMap(expanded_map_rows)


MAP_EXPANSION_FACTOR: Final[int] = 5


def part_2(file: pathlib.Path) -> None:
    chiton_density_scan = file.read_text(encoding='ascii')
    cavern_map = RiskLevelMap.parse(chiton_density_scan)
    full_cavern_map = expand_cavern_map(cavern_map, MAP_EXPANSION_FACTOR)

    start = Point(r=0, c=0)
    finish = Point(r=full_cavern_map.n_rows - 1, c=full_cavern_map.n_cols - 1)
    lowest_total_risk = find_least_risky_path(full_cavern_map, start, finish)

    print('part 2:', lowest_total_risk)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
