from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum
import functools
import heapq
import pathlib
import sys
from typing import Final, Self


@dataclass(frozen=True, match_args=False, slots=True)
class Point:
    r: int
    c: int

    def shift_by(self, *, dr: int = 0, dc: int = 0) -> Self:
        return self.__class__(r=self.r + dr, c=self.c + dc)

    def iter_neighbors(self) -> Iterator[Self]:
        yield self.shift_by(dr=+1)
        yield self.shift_by(dr=-1)
        yield self.shift_by(dc=+1)
        yield self.shift_by(dc=-1)


class AmphipodType(Enum):
    AMBER = 'A'
    BRONZE = 'B'
    COPPER = 'C'
    DESERT = 'D'


AMPHIPOD_TILES: Final[frozenset[str]] = frozenset(
    amphipod_type.value for amphipod_type in AmphipodType
)

WALL: Final[str] = '#'
OPEN: Final[str] = '.'
BURROW_TILES: Final[frozenset[str]] = frozenset([WALL, OPEN])

VALID_TILES: Final[frozenset[str]] = AMPHIPOD_TILES | BURROW_TILES


@dataclass(repr=False, frozen=True, match_args=False, slots=True)
class Burrow:
    spaces: frozenset[Point]
    hallway: frozenset[Point]
    doorways: frozenset[Point]
    rooms: tuple[tuple[AmphipodType, frozenset[Point]], ...]

    @classmethod
    def parse(cls, situation_diagram: str) -> Self:
        hallway_points: set[Point] = set()
        room_points: set[Point] = set()

        for r, line in enumerate(situation_diagram.split('\n')):
            for c, tile in enumerate(line):
                if tile == OPEN:
                    hallway_points.add(Point(r, c))
                elif tile in AMPHIPOD_TILES:
                    room_points.add(Point(r, c))
                # Ignore wall tiles and any other characters (like spaces)

        not_wall_points = hallway_points | room_points
        doorway_points = {
            point for point in hallway_points
            if point.shift_by(dr=+1) in room_points
        }

        room_columns: dict[int, set[Point]] = {}
        for point in room_points:
            if point.c in room_columns:
                room_columns[point.c].add(point)
            else:
                room_columns[point.c] = {point}

        room_labels: list[tuple[AmphipodType, frozenset[Point]]] = []
        pairings = zip(sorted(AMPHIPOD_TILES), sorted(room_columns.keys()))
        for tile, c in pairings:
            amphipod_type = AmphipodType(tile)
            points = frozenset(room_columns[c])
            room_labels.append((amphipod_type, points))

        return cls(
            spaces=frozenset(not_wall_points),
            hallway=frozenset(hallway_points),
            doorways=frozenset(doorway_points),
            rooms=tuple(room_labels),
        )

    def get(self, point: Point) -> str:
        return OPEN if point in self.spaces else WALL

    def destination_room(
        self, amphipod_type: AmphipodType,
    ) -> frozenset[Point]:
        for room_type, room_points in self.rooms:
            if room_type == amphipod_type:
                return room_points
        raise RuntimeError('unreachable code')


@dataclass(frozen=True, match_args=False, slots=True)
class Amphipod:
    type: AmphipodType
    position: Point


@dataclass(frozen=True, match_args=False, slots=True)
class Amphipods:
    amphipods: frozenset[Amphipod]

    @classmethod
    def parse(cls, situation_diagram: str) -> Self:
        amphipods: set[Amphipod] = set()
        for r, line in enumerate(situation_diagram.split('\n')):
            for c, tile in enumerate(line):
                if tile not in AMPHIPOD_TILES:
                    continue
                amphipod = Amphipod(AmphipodType(tile), Point(r, c))
                amphipods.add(amphipod)
        return cls(frozenset(amphipods))

    def __contains__(self, amphipod: Amphipod) -> bool:
        return amphipod in self.amphipods

    def __iter__(self) -> Iterator[Amphipod]:
        return iter(self.amphipods)

    def reposition(self, amphipod: Amphipod, new_position: Point) -> Self:
        repositioned_amphipod = Amphipod(amphipod.type, new_position)
        new_amphipods = (
            (self.amphipods - frozenset([amphipod]))
            | frozenset([repositioned_amphipod])
        )
        return self.__class__(new_amphipods)

    def is_occupied(self, point: Point) -> bool:
        for amphipod in self.amphipods:
            if amphipod.position == point:
                return True
        return False


def parse_situation_diagram(
    situation_diagram: str,
) -> tuple[Burrow, Amphipods]:
    burrow = Burrow.parse(situation_diagram)
    amphipods = Amphipods.parse(situation_diagram)
    return burrow, amphipods


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


STEP_ENERGY_COST: Final[dict[AmphipodType, int]] = {
    AmphipodType.AMBER: 1,
    AmphipodType.BRONZE: 10,
    AmphipodType.COPPER: 100,
    AmphipodType.DESERT: 1_000,
}


@functools.cache
def compute_energy_bound(burrow: Burrow, amphipods: Amphipods) -> int:
    hallway_r = next(iter(burrow.hallway)).r
    energy_lower_bound = 0
    for amphipod in amphipods:
        destination_room = burrow.destination_room(amphipod.type)
        if amphipod.position in destination_room:
            continue
        destination_room_c = next(iter(destination_room)).c
        minimum_steps = 0
        minimum_steps += abs(amphipod.position.r - hallway_r)
        minimum_steps += abs(amphipod.position.c - destination_room_c)
        minimum_steps += 1
        energy_lower_bound += STEP_ENERGY_COST[amphipod.type] * minimum_steps
    return energy_lower_bound

    # energy_lower_bound = 0
    # for amphipod_type, room_points in burrow.rooms:
    #     for room_point in room_points:
    #         desired_amphipod = Amphipod(amphipod_type, room_point)
    #         if desired_amphipod not in amphipods:
    #             energy_lower_bound += STEP_ENERGY_COST[amphipod_type]
    # return energy_lower_bound


def is_fully_organized(burrow: Burrow, amphipods: Amphipods) -> bool:
    return compute_energy_bound(burrow, amphipods) == 0


@functools.cache
def room_is_unavailable(
    burrow: Burrow, amphipod_type: AmphipodType, amphipods: Amphipods,
) -> bool:
    room_points = burrow.destination_room(amphipod_type)
    for amphipod in amphipods:
        if amphipod.position in room_points and amphipod.type != amphipod_type:
            return True
    return False


@dataclass(frozen=True, match_args=False, slots=True)
class Move:
    amphipods: Amphipods
    energy: int


HUGE: Final[int] = 2 ** 63 - 1


@functools.cache
def get_single_amphipod_moves(
    burrow: Burrow, amphipods: Amphipods, amphipod: Amphipod,
) -> list[Move]:
    known_energy: dict[Point, int] = {amphipod.position: 0}
    frontier: set[Point] = {amphipod.position}

    while frontier:
        current_point = frontier.pop()

        for neighbor_point in current_point.iter_neighbors():
            if burrow.get(neighbor_point) == WALL:
                continue
            if amphipods.is_occupied(neighbor_point):
                continue
            new_energy = (
                known_energy[current_point] + STEP_ENERGY_COST[amphipod.type]
            )
            if new_energy < known_energy.get(neighbor_point, HUGE):
                known_energy[neighbor_point] = new_energy
                frontier.add(neighbor_point)

    amphipod_moves: list[Move] = []
    for new_position, energy in known_energy.items():
        if new_position == amphipod.position:
            continue
        if new_position in burrow.doorways:
            continue
        if (
            amphipod.position not in burrow.hallway
            and new_position not in burrow.hallway
        ):
            continue
        if (
            amphipod.position in burrow.hallway
            and new_position not in burrow.destination_room(amphipod.type)
        ):
            continue
        if (
            new_position not in burrow.hallway
            and room_is_unavailable(burrow, amphipod.type, amphipods)
        ):
            continue
        new_amphipods = amphipods.reposition(amphipod, new_position)
        move = Move(new_amphipods, energy)
        amphipod_moves.append(move)
    return amphipod_moves


def find_possible_next_moves(
    burrow: Burrow, amphipods: Amphipods,
) -> list[Move]:
    possible_next_moves: list[Move] = []
    for amphipod in amphipods:
        possible_next_moves.extend(
            get_single_amphipod_moves(burrow, amphipods, amphipod),
        )
    return possible_next_moves


def find_least_energy_to_organize(
    burrow: Burrow, initial_amphipods: Amphipods,
) -> int:
    known_energy_so_far: dict[Amphipods, int] = {}
    frontier_queue: PriorityQueue[Amphipods] = PriorityQueue()

    known_energy_so_far[initial_amphipods] = 0
    priority = compute_energy_bound(burrow, initial_amphipods)
    frontier_queue.add_with_priority(initial_amphipods, priority)

    while not frontier_queue.is_empty():

        current_amphipods = frontier_queue.pop_min_priority()
        if is_fully_organized(burrow, current_amphipods):
            return known_energy_so_far[current_amphipods]

        possible_next_moves = find_possible_next_moves(
            burrow, current_amphipods,
        )

        for move in possible_next_moves:
            new_energy = known_energy_so_far[current_amphipods] + move.energy
            if new_energy < known_energy_so_far.get(move.amphipods, HUGE):
                known_energy_so_far[move.amphipods] = new_energy
                priority = (
                    new_energy + compute_energy_bound(burrow, move.amphipods)
                )
                frontier_queue.add_with_priority(move.amphipods, priority)

    raise RuntimeError('failed to find a least energy way to organize')


def part_1(file: pathlib.Path) -> None:
    situation_diagram = file.read_text(encoding='ascii')
    burrow, amphipods = parse_situation_diagram(situation_diagram)
    least_energy = find_least_energy_to_organize(burrow, amphipods)
    print('part 1:', least_energy)


def unfold_situation_diagram(situation_diagram: str) -> str:
    situation_diagram_lines = situation_diagram.split('\n')
    situation_diagram_lines.insert(3, "  #D#C#B#A#")
    situation_diagram_lines.insert(4, "  #D#B#A#C#")
    return '\n'.join(situation_diagram_lines)


def part_2(file: pathlib.Path) -> None:
    situation_diagram = file.read_text(encoding='ascii')
    situation_diagram = unfold_situation_diagram(situation_diagram)
    burrow, amphipods = parse_situation_diagram(situation_diagram)
    least_energy = find_least_energy_to_organize(burrow, amphipods)
    print('part 2:', least_energy)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
