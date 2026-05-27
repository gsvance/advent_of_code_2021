from collections.abc import Iterator
import pathlib
import sys
from typing import Final, NamedTuple, Self


class Point(NamedTuple):
    r: int
    c: int


def iter_neighbors(point: Point) -> Iterator[Point]:
    yield Point(r=point.r + 1, c=point.c)
    yield Point(r=point.r - 1, c=point.c)
    yield Point(r=point.r, c=point.c + 1)
    yield Point(r=point.r, c=point.c - 1)


HIGHEST_HEIGHT: Final[int] = 9
LOWEST_HEIGHT: Final[int] = 0


class Heightmap:

    __slots__ = ('heights',)

    def __init__(self, heights: list[list[int]]) -> None:
        self.heights: list[list[int]] = heights

        for row in self.heights:
            for height in row:
                if height not in range(LOWEST_HEIGHT, HIGHEST_HEIGHT + 1):
                    raise ValueError('invalid height')

    @classmethod
    def parse(cls, string: str) -> Self:
        heights: list[list[int]] = []
        for line in string.strip().split('\n'):
            row = [int(digit) for digit in line.strip()]
            heights.append(row)
        return cls(heights)

    def __getitem__(self, point: Point) -> int:
        return self.heights[point.r][point.c]

    def get(self, point: Point) -> int | None:
        if point.r < 0 or point.c < 0:
            return None
        try:
            return self[point]
        except IndexError:
            return None

    def iter_low_points(self) -> Iterator[Point]:
        for r, row in enumerate(self.heights):
            for c, height in enumerate(row):
                point = Point(r=r, c=c)
                looks_like_a_low_point = True
                for neighbor in iter_neighbors(point):
                    neighbor_height = self.get(neighbor)
                    if neighbor_height is None:
                        continue
                    if height >= neighbor_height:
                        looks_like_a_low_point = False
                        break
                if looks_like_a_low_point:
                    yield point


def part_1(file: pathlib.Path) -> None:
    heightmap_string = file.read_text(encoding='ascii')
    heightmap = Heightmap.parse(heightmap_string)

    sum_of_risk_levels = 0

    for low_point in heightmap.iter_low_points():
        risk_level = 1 + heightmap[low_point]
        sum_of_risk_levels += risk_level

    print('part 1:', sum_of_risk_levels)


def explore_basin(heightmap: Heightmap, low_point: Point) -> frozenset[Point]:
    visited: set[Point] = set()
    frontier: set[Point] = {low_point}

    while frontier:
        current = frontier.pop()
        visited.add(current)

        for neighbor in iter_neighbors(current):
            if neighbor in visited:
                continue
            if heightmap.get(neighbor) in (HIGHEST_HEIGHT, None):
                continue
            frontier.add(neighbor)

    return frozenset(visited)


NUMBER_OF_LARGEST_BASINS: Final[int] = 3


def part_2(file: pathlib.Path) -> None:
    heightmap_string = file.read_text(encoding='ascii')
    heightmap = Heightmap.parse(heightmap_string)

    basins: list[frozenset[Point]] = []
    for low_point in heightmap.iter_low_points():
        basin = explore_basin(heightmap, low_point)
        basins.append(basin)

    basins.sort(key=len)

    largest_basins_size_product = 1
    for large_basin in basins[-NUMBER_OF_LARGEST_BASINS:]:
        largest_basins_size_product *= len(large_basin)
    print('part 2:', largest_basins_size_product)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
