from collections.abc import Iterable, Iterator
import itertools
import pathlib
import sys


def parse_report(sonar_sweep_report: str) -> list[int]:
    return list(map(int, sonar_sweep_report.strip().split('\n')))


def increasing(depths: tuple[int, int]) -> bool:
    depth_1, depth_2 = depths
    return depth_1 < depth_2


def part_1(file: pathlib.Path) -> None:
    sonar_sweep_report = file.read_text(encoding='ascii')
    depths = parse_report(sonar_sweep_report)
    depth_pairs = itertools.pairwise(depths)
    depth_is_increasing = map(increasing, depth_pairs)
    print('part 1:', sum(depth_is_increasing))


def triplewise[T](iterable: Iterable[T]) -> Iterator[tuple[T, T, T]]:
    iterator = iter(iterable)
    item_0, item_1 = itertools.islice(iterator, 2)
    for item_2 in iterator:
        yield item_0, item_1, item_2
        item_0, item_1 = item_1, item_2


def part_2(file: pathlib.Path) -> None:
    sonar_sweep_report = file.read_text(encoding='ascii')
    depths = parse_report(sonar_sweep_report)
    windows = triplewise(depths)
    window_sums = map(sum, windows)
    window_sum_pairs = itertools.pairwise(window_sums)
    sum_is_increasing = map(increasing, window_sum_pairs)
    print('part 2:', sum(sum_is_increasing))


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
