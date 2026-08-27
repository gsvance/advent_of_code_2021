from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from enum import StrEnum
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

    def shift_up_1(self) -> Self:
        return self.shift_by(dr=-1)

    def shift_down_1(self) -> Self:
        return self.shift_by(dr=+1)

    def shift_left_1(self) -> Self:
        return self.shift_by(dc=-1)

    def shift_right_1(self) -> Self:
        return self.shift_by(dc=+1)


class AmphipodType(StrEnum):
    AMBER = 'A'
    BRONZE = 'B'
    COPPER = 'C'
    DESERT = 'D'


@dataclass(init=False, repr=False, frozen=True, match_args=False, slots=True)
class Hallway:
    points: frozenset[Point]
    doorways: frozenset[Point]
    r: int

    def __init__(
        self, points: Iterable[Point], doorways: Iterable[Point],
    ) -> None:
        object.__setattr__(self, 'points', frozenset(points))
        object.__setattr__(self, 'doorways', frozenset(doorways))
        if not self.doorways < self.points:
            raise ValueError(
                'expected doorways to be a subset of the hallway points'
            )
        r_values = {point.r for point in self.points}
        if len(r_values) != 1:
            raise ValueError(
                f'expected one r value for hallway, but got {r_values!r}'
            )
        object.__setattr__(self, 'r', r_values.pop())

    def __contains__(self, point: Point) -> bool:
        return point in self.points

    def is_doorway(self, point: Point) -> bool:
        if point in self.doorways:
            return True
        if point in self.points:
            return False
        raise ValueError(
            f'point passed to is_doorway() is not even in hallway: {point!r}'
        )


@dataclass(init=False, repr=False, frozen=True, match_args=False, slots=True)
class Room:
    points: frozenset[Point]
    c: int

    def __init__(self, points: Iterable[Point]) -> None:
        object.__setattr__(self, 'points', frozenset(points))
        c_values = {point.c for point in self.points}
        if len(c_values) != 1:
            raise ValueError(
                f'expected one c value for room, but got {c_values!r}'
            )
        object.__setattr__(self, 'c', c_values.pop())

    def __contains__(self, point: Point) -> bool:
        return point in self.points

    def __iter__(self) -> Iterator[Point]:
        return iter(self.points)


AMPHIPOD_TILES: Final[frozenset[str]] = frozenset(
    amphipod_type.value for amphipod_type in AmphipodType
)

WALL: Final[str] = '#'
OPEN: Final[str] = '.'


@dataclass(init=False, repr=False, frozen=True, match_args=False, slots=True)
class Burrow:
    points: frozenset[Point]
    hallway: Hallway
    rooms: dict[AmphipodType, Room]  # Treat this dict as immutable

    def __init__(
        self,
        points: Iterable[Point],
        hallway: Hallway,
        rooms: Iterable[tuple[AmphipodType, Room]],
    ) -> None:
        object.__setattr__(self, 'points', frozenset(points))
        object.__setattr__(self, 'hallway', hallway)
        object.__setattr__(self, 'rooms', dict(rooms))

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
            if point.shift_down_1() in room_points
        }

        room_columns: dict[int, set[Point]] = {}
        for point in room_points:
            if point.c in room_columns:
                room_columns[point.c].add(point)
            else:
                room_columns[point.c] = {point}

        labeled_rooms: list[tuple[AmphipodType, Room]] = []
        pairings = zip(sorted(AMPHIPOD_TILES), sorted(room_columns.keys()))
        for tile, c in pairings:
            amphipod_type = AmphipodType(tile)
            room = Room(room_columns[c])
            labeled_rooms.append((amphipod_type, room))

        return cls(
            points=not_wall_points,
            hallway=Hallway(hallway_points, doorway_points),
            rooms=labeled_rooms,
        )

    def get_tile(self, point: Point) -> str:
        return OPEN if point in self.points else WALL

    def get_destination_room(self, amphipod_type: AmphipodType) -> Room:
        return self.rooms[amphipod_type]


@dataclass(frozen=True, match_args=False, slots=True)
class Amphipod:
    type: AmphipodType
    position: Point

    @property
    def r(self) -> int:
        return self.position.r

    @property
    def c(self) -> int:
        return self.position.c


@dataclass(init=False, frozen=True, match_args=False, slots=True)
class Amphipods:
    amphipods: frozenset[Amphipod]

    def __init__(self, amphipods: Iterable[Amphipod]) -> None:
        object.__setattr__(self, 'amphipods', frozenset(amphipods))

    @classmethod
    def parse(cls, situation_diagram: str) -> Self:
        amphipods: set[Amphipod] = set()
        for r, line in enumerate(situation_diagram.split('\n')):
            for c, tile in enumerate(line):
                if tile not in AMPHIPOD_TILES:
                    continue
                amphipod = Amphipod(AmphipodType(tile), Point(r, c))
                amphipods.add(amphipod)
        return cls(amphipods)

    def __contains__(self, amphipod: Amphipod) -> bool:
        return amphipod in self.amphipods

    def __iter__(self) -> Iterator[Amphipod]:
        return iter(self.amphipods)

    def get(self, point: Point) -> Amphipod | None:
        for amphipod in self.amphipods:
            if amphipod.position == point:
                return amphipod
        return None

    def reposition(self, amphipod: Amphipod, new_position: Point) -> Self:
        new_amphipods = {
            old_amphipod for old_amphipod in self.amphipods
            if old_amphipod != amphipod
        }
        new_amphipods.add(Amphipod(amphipod.type, new_position))
        return self.__class__(new_amphipods)


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

    __slots__ = ('heap', 'entry_finder', 'length')

    def __init__(self) -> None:
        self.heap: list[PriorityQueueEntry[T]] = []
        self.entry_finder: dict[T, PriorityQueueEntry[T]] = {}
        self.length: int = 0

    def remove(self, item: T) -> None:
        entry = self.entry_finder.pop(item)
        entry.removed = True
        self.length -= 1

    def add_with_priority(self, item: T, priority: int) -> None:
        if item in self.entry_finder:
            self.remove(item)
        entry = PriorityQueueEntry(priority, item)
        self.entry_finder[item] = entry
        heapq.heappush(self.heap, entry)
        self.length += 1

    def pop_min_priority(self) -> T:
        while self.heap:
            entry = heapq.heappop(self.heap)
            if not entry.removed:
                del self.entry_finder[entry.item]
                self.length -= 1
                return entry.item
        raise IndexError(
            'pop_min_priority() was called on an empty priority queue'
        )

    def is_empty(self) -> bool:
        return self.length == 0


STEP_ENERGY_COST: Final[dict[AmphipodType, int]] = {
    AmphipodType.AMBER: 1,
    AmphipodType.BRONZE: 10,
    AmphipodType.COPPER: 100,
    AmphipodType.DESERT: 1_000,
}


def compute_energy_bound(burrow: Burrow, amphipods: Amphipods) -> int:
    energy_lower_bound = 0
    for amphipod in amphipods:
        destination_room = burrow.get_destination_room(amphipod.type)
        if amphipod.position in destination_room:
            continue
        minimum_steps = (
            abs(amphipod.r - burrow.hallway.r)  # Moving into the hallway
            + abs(amphipod.c - destination_room.c)  # Moving along the hallway
            + 1  # Moving into the destination room
        )
        energy_lower_bound += STEP_ENERGY_COST[amphipod.type] * minimum_steps
    return energy_lower_bound


def is_fully_organized(burrow: Burrow, amphipods: Amphipods) -> bool:
    for amphipod_type in AmphipodType:
        destination_room = burrow.get_destination_room(amphipod_type)
        for point in destination_room:
            desired_amphipod = Amphipod(amphipod_type, point)
            if desired_amphipod not in amphipods:
                return False
    return True


def destination_room_is_available(
    burrow: Burrow, amphipods: Amphipods, amphipod_type: AmphipodType,
) -> bool:
    destination_room = burrow.get_destination_room(amphipod_type)
    for amphipod in amphipods:
        if (
            amphipod.position in destination_room
            and amphipod.type != amphipod_type
        ):
            return False
    return True


@dataclass(frozen=True, match_args=False, slots=True)
class Move:
    amphipods: Amphipods
    energy: int


def compute_moves_into_hallway(
    burrow: Burrow, amphipods: Amphipods, amphipod: Amphipod,
) -> list[Move]:
    point_above = amphipod.position.shift_up_1()
    while point_above not in burrow.hallway:
        if amphipods.get(point_above) is not None:
            return []  # The amphipod is blocked from reaching the hallway
        point_above = point_above.shift_up_1()

    upward_steps = abs(point_above.r - amphipod.r)
    hallway_moves: list[Move] = []

    point_leftward = point_above.shift_left_1()
    while (
        burrow.get_tile(point_leftward) != WALL
        and amphipods.get(point_leftward) is None
    ):
        if not burrow.hallway.is_doorway(point_leftward):
            steps = upward_steps + abs(point_above.c - point_leftward.c)
            hallway_moves.append(Move(
                amphipods.reposition(amphipod, point_leftward),
                STEP_ENERGY_COST[amphipod.type] * steps,
            ))
        point_leftward = point_leftward.shift_left_1()

    point_rightward = point_above.shift_right_1()
    while (
        burrow.get_tile(point_rightward) != WALL
        and amphipods.get(point_rightward) is None
    ):
        if not burrow.hallway.is_doorway(point_rightward):
            steps = upward_steps + abs(point_above.c - point_rightward.c)
            hallway_moves.append(Move(
                amphipods.reposition(amphipod, point_rightward),
                STEP_ENERGY_COST[amphipod.type] * steps,
            ))
        point_rightward = point_rightward.shift_right_1()

    return hallway_moves


def compute_destination_room_move(
    burrow: Burrow, amphipods: Amphipods, amphipod: Amphipod,
) -> list[Move]:
    if not destination_room_is_available(burrow, amphipods, amphipod.type):
        return []  # Must wait for non-matching amphipods to leave the room

    destination_doorway = Point(
        burrow.hallway.r, burrow.get_destination_room(amphipod.type).c
    )
    rightward_steps = destination_doorway.c - amphipod.position.c
    sign = +1 if rightward_steps >= 0 else -1

    for dc in range(sign, rightward_steps + sign, sign):
        if amphipods.get(amphipod.position.shift_by(dc=dc)) is not None:
            return []  # Another amphipod is currently blocking the hallway

    destination_point = destination_doorway
    while True:
        point_below = destination_point.shift_down_1()
        if (
            burrow.get_tile(point_below) != WALL
            and amphipods.get(point_below) is None
        ):
            destination_point = point_below
        else:
            break  # The amphipod cannot move downward any farther

    steps = abs(rightward_steps) + abs(burrow.hallway.r - destination_point.r)
    return [Move(
        amphipods.reposition(amphipod, destination_point),
        STEP_ENERGY_COST[amphipod.type] * steps,
    )]


def find_single_amphipod_moves(
    burrow: Burrow, amphipods: Amphipods, amphipod: Amphipod,
) -> list[Move]:
    # Once an amphipod is stopped in the hallway, it can only move from there
    # into its destination room
    if amphipod.position in burrow.hallway:
        return compute_destination_room_move(burrow, amphipods, amphipod)

    # An amphipod that's not inside its correct room needs to try and move into
    # the hallway and find a good stopping place
    if amphipod.position not in burrow.get_destination_room(amphipod.type):
        return compute_moves_into_hallway(burrow, amphipods, amphipod)

    # In this case, the amphipod is already in its correct room, but there are
    # non-matching amphipods in that room as well. If we can move into the
    # hallway and allow them to escape, then we should do that. 
    if not destination_room_is_available(burrow, amphipods, amphipod.type):
        return compute_moves_into_hallway(burrow, amphipods, amphipod)

    return []  # The amphipod has no reason to move


def find_possible_next_moves(
    burrow: Burrow, amphipods: Amphipods,
) -> list[Move]:
    possible_next_moves: list[Move] = []
    for amphipod in amphipods:
        possible_next_moves.extend(
            find_single_amphipod_moves(burrow, amphipods, amphipod)
        )
    return possible_next_moves


HUGE: Final[int] = 2 ** 63 - 1


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
                new_priority = (
                    new_energy + compute_energy_bound(burrow, move.amphipods)
                )
                frontier_queue.add_with_priority(move.amphipods, new_priority)

    raise RuntimeError('failed to find any least energy way to organize')


def part_1(file: pathlib.Path) -> None:
    situation_diagram = file.read_text(encoding='ascii')
    burrow, amphipods = parse_situation_diagram(situation_diagram)
    least_energy = find_least_energy_to_organize(burrow, amphipods)
    print('part 1:', least_energy)


def unfold_situation_diagram(situation_diagram: str) -> str:
    situation_diagram_lines = situation_diagram.split('\n')
    situation_diagram_lines.insert(3, '  #D#C#B#A#')
    situation_diagram_lines.insert(4, '  #D#B#A#C#')
    return '\n'.join(situation_diagram_lines)


def part_2(file: pathlib.Path) -> None:
    situation_diagram = file.read_text(encoding='ascii')
    unfolded_situation_diagram = unfold_situation_diagram(situation_diagram)
    burrow, amphipods = parse_situation_diagram(unfolded_situation_diagram)
    least_energy = find_least_energy_to_organize(burrow, amphipods)
    print('part 2:', least_energy)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
