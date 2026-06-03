import math
import pathlib
import sys
from typing import Any, Final


BINARY_BASE: Final[int] = 2
HEXADECIMAL_BASE: Final[int] = 16

BITS_PER_HEXADECIMAL_DIGIT: Final[int] = 4


class BinaryReader:

    __slots__ = ('_binary_string', '_position')

    def __init__(self, hexadecimal_string: str) -> None:
        cleaned_hexadecimal = hexadecimal_string.strip()
        integer = int(cleaned_hexadecimal, base=HEXADECIMAL_BASE)
        bits_without_padding = bin(integer).removeprefix('0b')
        final_length = len(cleaned_hexadecimal) * BITS_PER_HEXADECIMAL_DIGIT

        self._binary_string: str = bits_without_padding.zfill(final_length)
        self._position: int = 0

    @property
    def position(self) -> int:
        return self._position

    def read_bits(self, number_of_bits: int) -> str:
        if self._position >= len(self._binary_string):
            return ''
        begin = self._position
        self._position += number_of_bits
        end = self._position
        return self._binary_string[begin:end]

    def read_int(self, number_of_bits: int) -> int:
        bits = self.read_bits(number_of_bits)
        if not bits:
            raise IndexError('cannot read int at end of binary string')
        return int(bits, base=BINARY_BASE)


def parse_standard_header(reader: BinaryReader) -> tuple[int, int]:
    version = reader.read_int(3)
    type_id = reader.read_int(3)
    return version, type_id


GROUP_PREFIX_BITS: Final[int] = 1
GROUP_VALUE_BITS: Final[int] = 4

KEEP_READING_GROUP_PREFIX: Final[int] = 1
END_OF_PACKET_GROUP_PREFIX: Final[int] = 0


def parse_literal_value(reader: BinaryReader) -> int:
    value = 0
    done_reading = False

    while not done_reading:

        group_prefix = reader.read_int(GROUP_PREFIX_BITS)
        group_value = reader.read_int(GROUP_VALUE_BITS)

        value = (value << GROUP_VALUE_BITS) ^ group_value

        if group_prefix == KEEP_READING_GROUP_PREFIX:
            done_reading = False
        elif group_prefix == END_OF_PACKET_GROUP_PREFIX:
            done_reading = True
        else:
            raise ValueError('invalid group prefix')

    return value


def parse_length_type_id(reader: BinaryReader) -> int:
    length_type_id = reader.read_int(1)
    return length_type_id


def parse_total_length_in_bits(reader: BinaryReader) -> int:
    total_length_in_bits = reader.read_int(15)
    return total_length_in_bits


def parse_number_of_sub_packets(reader: BinaryReader) -> int:
    number_of_sub_packets = reader.read_int(11)
    return number_of_sub_packets


type Packet = dict[str, Any]

VERSION: Final[str] = 'version'
TYPE_ID: Final[str] = 'type_id'
VALUE: Final[str] = 'value'
LENGTH_TYPE_ID: Final[str] = 'length_type_id'
TOTAL_LENGTH_IN_BITS: Final[str] = 'total_length_in_bits'
NUMBER_OF_SUB_PACKETS: Final[str] = 'number_of_sub_packets'
SUB_PACKETS: Final[str] = 'sub_packets'

LITERAL_VALUE_TYPE_ID: Final[int] = 4
TOTAL_LENGTH_IN_BITS_LENGTH_TYPE_ID: Final[int] = 0
NUMBER_OF_SUB_PACKETS_LENGTH_TYPE_ID: Final[int] = 1


def parse_packet(reader: BinaryReader) -> Packet:
    version, type_id = parse_standard_header(reader)
    packet: Packet = {VERSION: version, TYPE_ID: type_id}

    if type_id == LITERAL_VALUE_TYPE_ID:
        value = parse_literal_value(reader)
        packet[VALUE] = value
        return packet

    # Operator packet
    length_type_id = parse_length_type_id(reader)
    packet[LENGTH_TYPE_ID] = length_type_id

    if length_type_id == TOTAL_LENGTH_IN_BITS_LENGTH_TYPE_ID:
        total_length_in_bits = parse_total_length_in_bits(reader)
        packet[TOTAL_LENGTH_IN_BITS] = total_length_in_bits
        sub_packets = parse_sub_packets(
            reader, total_length_in_bits=total_length_in_bits,
        )
        packet[SUB_PACKETS] = sub_packets
        return packet

    if length_type_id == NUMBER_OF_SUB_PACKETS_LENGTH_TYPE_ID:
        number_of_sub_packets = parse_number_of_sub_packets(reader)
        packet[NUMBER_OF_SUB_PACKETS] = NUMBER_OF_SUB_PACKETS
        sub_packets = parse_sub_packets(
            reader, number_of_sub_packets=number_of_sub_packets,
        )
        packet[SUB_PACKETS] = sub_packets
        return packet

    raise ValueError('invalid length type ID')


def parse_sub_packets(
    reader: BinaryReader,
    *,
    total_length_in_bits: int | None = None,
    number_of_sub_packets: int | None = None,
) -> list[Packet]:
    if total_length_in_bits is None and number_of_sub_packets is None:
        raise TypeError('keyword argument required for parsing sub-packets')
    if total_length_in_bits is not None and number_of_sub_packets is not None:
        raise TypeError('too many keyword arguments for parsing sub-packets')

    if total_length_in_bits is not None:
        progress = reader.position
        goal = reader.position + total_length_in_bits
    elif number_of_sub_packets is not None:
        progress = 0
        goal = number_of_sub_packets
    else:
        raise RuntimeError('unreachable code')

    sub_packets: list[Packet] = []
    while progress < goal:

        sub_packet = parse_packet(reader)
        sub_packets.append(sub_packet)

        if total_length_in_bits is not None:
            progress = reader.position
        elif number_of_sub_packets is not None:
            progress += 1
        else:
            raise RuntimeError('unreachable code')

    if progress > goal:
        raise RuntimeError('went too far while parsing sub-packets')

    return sub_packets


def add_version_numbers_recursively(packet: Packet) -> int:
    version = packet[VERSION]
    if packet[TYPE_ID] == LITERAL_VALUE_TYPE_ID:
        return version

    # Operator packet
    sub_packet_sum = 0
    for sub_packet in packet[SUB_PACKETS]:
        sub_packet_sum += add_version_numbers_recursively(sub_packet)
    return version + sub_packet_sum


def part_1(file: pathlib.Path) -> None:
    hexadecimal_transmission = file.read_text(encoding='ascii')
    reader = BinaryReader(hexadecimal_transmission)

    outermost_packet = parse_packet(reader)
    version_number_sum = add_version_numbers_recursively(outermost_packet)

    print('part 1:', version_number_sum)


SUM_TYPE_ID: Final[int] = 0
PRODUCT_TYPE_ID: Final[int] = 1
MINIMUM_TYPE_ID: Final[int] = 2
MAXIMUM_TYPE_ID: Final[int] = 3
GREATER_THAN_TYPE_ID: Final[int] = 5
LESS_THAN_TYPE_ID: Final[int] = 6
EQUAL_TO_TYPE_ID: Final[int] = 7


def evaluate_expression(packet: Packet) -> None:
    if packet[TYPE_ID] == LITERAL_VALUE_TYPE_ID:
        return

    # Operator packet
    for sub_packet in packet[SUB_PACKETS]:
        evaluate_expression(sub_packet)

    value: int | None = None
    sub_packet_values = (
        sub_packet[VALUE] for sub_packet in packet[SUB_PACKETS]
    )

    if packet[TYPE_ID] == SUM_TYPE_ID:
        value = sum(sub_packet_values)
    elif packet[TYPE_ID] == PRODUCT_TYPE_ID:
        value = math.prod(sub_packet_values)
    elif packet[TYPE_ID] == MINIMUM_TYPE_ID:
        value = min(sub_packet_values)
    elif packet[TYPE_ID] == MAXIMUM_TYPE_ID:
        value = max(sub_packet_values)
    elif packet[TYPE_ID] == GREATER_THAN_TYPE_ID:
        first, second = sub_packet_values
        value = int(first > second)
    elif packet[TYPE_ID] == LESS_THAN_TYPE_ID:
        first, second = sub_packet_values
        value = int(first < second)
    elif packet[TYPE_ID] == EQUAL_TO_TYPE_ID:
        first, second = sub_packet_values
        value = int(first == second)

    if value is None:
        raise ValueError('invalid packet type ID when evaluating expression')
    packet[VALUE] = value


def part_2(file: pathlib.Path) -> None:
    hexadecimal_transmission = file.read_text(encoding='ascii')
    reader = BinaryReader(hexadecimal_transmission)

    outermost_packet = parse_packet(reader)
    evaluate_expression(outermost_packet)

    print('part 2:', outermost_packet[VALUE])


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
