from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum
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

    def to_binary(self) -> bytes:
        assert 0 <= self.r < 16 and 0 <= self.c < 16
        return bytes([(self.r << 4) | self.c])

    @classmethod
    def from_binary(cls, binary: bytes) -> Self:
        assert len(binary) == 1
        r = binary[0] >> 4
        c = binary[0] & 0xf
        return cls(r, c)


class AmphipodType(Enum):
    AMBER = 'A'
    BRONZE = 'B'
    COPPER = 'C'
    DESERT = 'D'

    def to_binary(self) -> bytes:
        return self.value.encode('ascii')

    @classmethod
    def from_binary(cls, binary: bytes) -> Self:
        assert len(binary) == 1
        return cls(binary.decode('ascii'))


@dataclass(frozen=True, match_args=False, slots=True)
class Hallway:
    points: frozenset[Point]
    doorways: frozenset[Point]

    def __post_init__(self) -> None:
        r_values = {point.r for point in self.points}
        if len(r_values) != 1:
            raise ValueError(f'hallway has multiple r values: {r_values!r}')
        if not self.doorways < self.points:
            raise ValueError('doorways are not a subset of the hallway')

    def __contains__(self, point: Point) -> bool:
        return point in self.points

    @property
    def r(self) -> int:
        return next(iter(self.points)).r


@dataclass(frozen=True, match_args=False, slots=True)
class Room:
    points: frozenset[Point]

    def __post_init__(self) -> None:
        c_values = {point.c for point in self.points}
        if len(c_values) != 1:
            raise ValueError(f'room has multiple c values: {c_values!r}')

    def __contains__(self, point: Point) -> bool:
        return point in self.points

    def __iter__(self) -> Iterator[Point]:
        return iter(self.points)

    @property
    def c(self) -> int:
        return next(iter(self.points)).c


AMPHIPOD_TILES: Final[frozenset[str]] = frozenset(
    amphipod_type.value for amphipod_type in AmphipodType
)

WALL: Final[str] = '#'
OPEN: Final[str] = '.'


@dataclass(repr=False, frozen=True, match_args=False, slots=True)
class Burrow:
    spaces: frozenset[Point]
    hallway: Hallway
    rooms: tuple[tuple[AmphipodType, Room], ...]

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

        labeled_rooms: list[tuple[AmphipodType, Room]] = []
        pairings = zip(sorted(AMPHIPOD_TILES), sorted(room_columns.keys()))
        for tile, c in pairings:
            amphipod_type = AmphipodType(tile)
            room = Room(frozenset(room_columns[c]))
            labeled_rooms.append((amphipod_type, room))

        return cls(
            spaces=frozenset(not_wall_points),
            hallway=Hallway(
                frozenset(hallway_points), frozenset(doorway_points),
            ),
            rooms=tuple(labeled_rooms),
        )

    def get(self, point: Point) -> str:
        return OPEN if point in self.spaces else WALL

    def destination_room(self, amphipod_type: AmphipodType) -> Room:
        for room_amphipod_type, room in self.rooms:
            if room_amphipod_type == amphipod_type:
                return room
        raise RuntimeError('unreachable code')


@dataclass(frozen=True, match_args=False, slots=True)
class Amphipod:
    type: AmphipodType
    position: Point

    def to_binary(self) -> bytes:
        return self.type.to_binary() + self.position.to_binary()

    @classmethod
    def from_binary(cls, binary: bytes) -> Self:
        assert len(binary) == 2
        return cls(
            AmphipodType.from_binary(binary[0:1]),
            Point.from_binary(binary[1:2]),
        )


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

    def get(self, point: Point) -> Amphipod | None:
        for amphipod in self.amphipods:
            if amphipod.position == point:
                return amphipod
        return None

    def reposition(self, amphipod: Amphipod, new_position: Point) -> Self:
        new_amphipods = set(self.amphipods)
        new_amphipods.remove(amphipod)
        new_amphipods.add(Amphipod(amphipod.type, new_position))
        return self.__class__(frozenset(new_amphipods))

    def to_binary(self) -> bytes:
        amphipods_binary = [
            amphipod.to_binary() for amphipod in self.amphipods
        ]
        amphipods_binary.sort()
        return b''.join(amphipods_binary)

    @classmethod
    def from_binary(cls, binary: bytes) -> Self:
        assert len(binary) % 2 == 0
        amphipods: set[Amphipod] = set()
        for i in range(0, len(binary), 2):
            amphipod = Amphipod.from_binary(binary[i:i+2])
            amphipods.add(amphipod)
        return cls(frozenset(amphipods))


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


def compute_energy_bound(burrow: Burrow, amphipods: Amphipods) -> int:
    energy_lower_bound = 0
    for amphipod in amphipods:
        destination_room = burrow.destination_room(amphipod.type)
        if amphipod.position in destination_room:
            continue
        minimum_steps = (
            1 + abs(amphipod.position.r - burrow.hallway.r)
            + abs(amphipod.position.c - destination_room.c)
        )
        energy_lower_bound += STEP_ENERGY_COST[amphipod.type] * minimum_steps
    return energy_lower_bound


def is_fully_organized(burrow: Burrow, amphipods: Amphipods) -> bool:
    for room_amphipod_type, room in burrow.rooms:
        for room_point in room:
            desired_amphipod = Amphipod(room_amphipod_type, room_point)
            if desired_amphipod not in amphipods:
                return False
    return True


@dataclass(frozen=True, match_args=False, slots=True)
class Move:
    amphipods: Amphipods
    energy: int


def get_single_amphipod_moves(
    burrow: Burrow, amphipods: Amphipods, amphipod: Amphipod,
) -> frozenset[Move]:
    destination_room = burrow.destination_room(amphipod.type)

    # When the amphipod is in its destination room, the choice of move depends
    # on whether there is another amphipod below it that needs to escape
    if amphipod.position in destination_room:
        amphipod_below_needs_to_escape = False
        point_below = amphipod.position.shift_by(dr=+1)
        while burrow.get(point_below) != WALL:
            amphipod_below = amphipods.get(point_below)
            if (
                amphipod_below is not None
                and amphipod_below.type != amphipod.type
            ):
                amphipod_below_needs_to_escape = True
                break
            point_below = point_below.shift_by(dr=+1)

        # When an amphipod below needs to escape, we should try to move upward
        # or into the hallway to get out of the way
        if amphipod_below_needs_to_escape:
            point_above = amphipod.position.shift_by(dr=-1)
            if point_above in burrow.hallway.doorways:
                hallway_moves: set[Move] = set()
                point_leftward = point_above.shift_by(dc=-1)
                while (
                    burrow.get(point_leftward) != WALL
                    and amphipods.get(point_leftward) is None
                ):
                    if point_leftward not in burrow.hallway.doorways:
                        steps = 1 + abs(point_above.c - point_leftward.c)
                        hallway_moves.add(Move(
                            amphipods.reposition(amphipod, point_leftward),
                            STEP_ENERGY_COST[amphipod.type] * steps,
                        ))
                    point_leftward = point_leftward.shift_by(dc=-1)
                point_rightward = point_above.shift_by(dc=+1)
                while (
                    burrow.get(point_rightward) != WALL
                    and amphipods.get(point_rightward) is None
                ):
                    if point_rightward not in burrow.hallway.doorways:
                        steps = 1 + abs(point_above.c - point_rightward.c)
                        hallway_moves.add(Move(
                            amphipods.reposition(amphipod, point_rightward),
                            STEP_ENERGY_COST[amphipod.type] * steps,
                        ))
                    point_rightward = point_rightward.shift_by(dc=+1)
                return frozenset(hallway_moves)
            if amphipods.get(point_above) is None:
                return frozenset([Move(
                    amphipods.reposition(amphipod, point_above),
                    STEP_ENERGY_COST[amphipod.type] * 1,
                )])
            return frozenset()

        # Otherwise, just move downward whenever possible to make space for
        # other amphipods entering this room
        point_below = amphipod.position.shift_by(dr=+1)
        if (
            burrow.get(point_below) != WALL
            and amphipods.get(point_below) is None
        ):
            return frozenset([Move(
                amphipods.reposition(amphipod, point_below),
                STEP_ENERGY_COST[amphipod.type] * 1,
            )])
        return frozenset()

    # When the amphipod is stopped in the hallway, the only possibility is to
    # check whether it can move into its destination room
    if amphipod.position in burrow.hallway:
        entry_point = Point(burrow.hallway.r + 1, destination_room.c)
        delta_c = entry_point.c - amphipod.position.c
        sign = +1 if delta_c >= 0 else -1
        for dc in range(sign, delta_c + sign, sign):
            if amphipods.get(amphipod.position.shift_by(dc=dc)) is not None:
                return frozenset()
        if amphipods.get(entry_point) is not None:
            return frozenset()
        for room_point in destination_room:
            if room_point == entry_point:
                continue
            amphipod_in_room = amphipods.get(room_point)
            if (
                amphipod_in_room is not None
                and amphipod_in_room.type != amphipod.type
            ):
                return frozenset()
        steps = 1 + abs(amphipod.position.c - entry_point.c)
        return frozenset([Move(
            amphipods.reposition(amphipod, entry_point),
            STEP_ENERGY_COST[amphipod.type] * steps,
        )])

    # Otherwise, the amphipod is in the wrong room and needs to either move
    # upwards or move into the hallway
    point_above = amphipod.position.shift_by(dr=-1)
    if point_above not in burrow.hallway.doorways:
        if amphipods.get(point_above) is None:
            return frozenset([Move(
                amphipods.reposition(amphipod, point_above),
                STEP_ENERGY_COST[amphipod.type] * 1,
            )])
        return frozenset()
    hallway_moves: set[Move] = set()
    point_leftward = point_above.shift_by(dc=-1)
    while (
        burrow.get(point_leftward) != WALL
        and amphipods.get(point_leftward) is None
    ):
        if point_leftward not in burrow.hallway.doorways:
            steps = 1 + abs(point_above.c - point_leftward.c)
            hallway_moves.add(Move(
                amphipods.reposition(amphipod, point_leftward),
                STEP_ENERGY_COST[amphipod.type] * steps,
            ))
        point_leftward = point_leftward.shift_by(dc=-1)
    point_rightward = point_above.shift_by(dc=+1)
    while (
        burrow.get(point_rightward) != WALL
        and amphipods.get(point_rightward) is None
    ):
        if point_rightward not in burrow.hallway.doorways:
            steps = 1 + abs(point_above.c - point_rightward.c)
            hallway_moves.add(Move(
                amphipods.reposition(amphipod, point_rightward),
                STEP_ENERGY_COST[amphipod.type] * steps,
            ))
        point_rightward = point_rightward.shift_by(dc=+1)
    return frozenset(hallway_moves)


def find_possible_next_moves(
    burrow: Burrow, amphipods: Amphipods,
) -> frozenset[Move]:
    possible_next_moves: set[Move] = set()
    for amphipod in amphipods:
        possible_next_moves.update(
            get_single_amphipod_moves(burrow, amphipods, amphipod),
        )
    return frozenset(possible_next_moves)


HUGE: Final[int] = 2 ** 63 - 1


def find_least_energy_to_organize(
    burrow: Burrow, initial_amphipods: Amphipods,
) -> int:
    known_energy_so_far: dict[bytes, int] = {}
    frontier_queue: PriorityQueue[bytes] = PriorityQueue()

    initial_amphipods_binary = initial_amphipods.to_binary()
    known_energy_so_far[initial_amphipods_binary] = 0
    priority = compute_energy_bound(burrow, initial_amphipods)
    frontier_queue.add_with_priority(initial_amphipods_binary, priority)

    while not frontier_queue.is_empty():

        current_amphipods_binary = frontier_queue.pop_min_priority()
        current_amphipods = Amphipods.from_binary(current_amphipods_binary)
        if is_fully_organized(burrow, current_amphipods):
            return known_energy_so_far[current_amphipods_binary]

        possible_next_moves = find_possible_next_moves(
            burrow, current_amphipods,
        )

        for move in possible_next_moves:
            new_energy = (
                known_energy_so_far[current_amphipods_binary] + move.energy
            )
            move_amphipods_binary = move.amphipods.to_binary()
            if new_energy < known_energy_so_far.get(
                move_amphipods_binary, HUGE,
            ):
                known_energy_so_far[move_amphipods_binary] = new_energy
                priority = (
                    new_energy + compute_energy_bound(burrow, move.amphipods)
                )
                frontier_queue.add_with_priority(
                    move_amphipods_binary, priority,
                )

    raise RuntimeError('failed to find a least energy way to organize')


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
    situation_diagram = unfold_situation_diagram(situation_diagram)
    burrow, amphipods = parse_situation_diagram(situation_diagram)
    least_energy = find_least_energy_to_organize(burrow, amphipods)
    print('part 2:', least_energy)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
