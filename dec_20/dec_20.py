from dataclasses import dataclass
import pathlib
import sys
from typing import Final, Self


LIGHT_PIXEL: Final[str] = '#'
DARK_PIXEL: Final[str] = '.'

VALID_PIXELS: Final[tuple[str, ...]] = (LIGHT_PIXEL, DARK_PIXEL)


INVERT_PIXEL: Final[dict[str, str]] = {
    LIGHT_PIXEL: DARK_PIXEL, DARK_PIXEL: LIGHT_PIXEL,
}
PIXEL_AS_BIT: Final[dict[str, int]] = {LIGHT_PIXEL: 1, DARK_PIXEL: 0}


SQUARE_SIZE: Final[int] = 3
SQUARE_RADIUS: Final[int] = SQUARE_SIZE // 2

INDEX_BITS: Final[int] = SQUARE_SIZE ** 2
ALGORITHM_LENGTH: Final[int] = 1 << INDEX_BITS


def parse_algorithm(raw_algorithm_string: str) -> str:
    cleaned_chars: list[str] = []
    for raw_char in raw_algorithm_string:
        if raw_char in VALID_PIXELS:
            cleaned_chars.append(raw_char)

    cleaned_algorithm = ''.join(cleaned_chars)
    if len(cleaned_algorithm) != ALGORITHM_LENGTH:
        raise ValueError('image enhancement algorithm has the wrong length')
    return cleaned_algorithm


@dataclass(frozen=True, match_args=False, slots=True)
class Point:
    r: int
    c: int


@dataclass(frozen=True, match_args=False, slots=True)
class InfiniteImage:
    foreground_pixels: frozenset[Point]
    background_pixel: str

    @classmethod
    def parse(cls, image_string: str) -> Self:
        light_pixels: set[Point] = set()

        for r, line in enumerate(image_string.strip().split('\n')):
            for c, char in enumerate(line.strip()):
                if char not in VALID_PIXELS:
                    raise ValueError('image contains invalid pixel char')
                if char == LIGHT_PIXEL:
                    light_pixels.add(Point(r, c))

        return cls(frozenset(light_pixels), DARK_PIXEL)

    def r_min(self, *, border: bool = False) -> int:
        r_min_value = min(pixel.r for pixel in self.foreground_pixels)
        if border:
            r_min_value -= SQUARE_RADIUS
        return r_min_value

    def r_max(self, *, border: bool = False) -> int:
        r_max_value = max(pixel.r for pixel in self.foreground_pixels)
        if border:
            r_max_value += SQUARE_RADIUS
        return r_max_value

    def c_min(self, *, border: bool = False) -> int:
        c_min_value = min(pixel.c for pixel in self.foreground_pixels)
        if border:
            c_min_value -= SQUARE_RADIUS
        return c_min_value

    def c_max(self, *, border: bool = False) -> int:
        c_max_value = max(pixel.c for pixel in self.foreground_pixels)
        if border:
            c_max_value += SQUARE_RADIUS
        return c_max_value

    def __getitem__(self, point: Point) -> str:
        if point in self.foreground_pixels:
            return INVERT_PIXEL[self.background_pixel]
        return self.background_pixel

    def __str__(self) -> str:
        lines: list[str] = []
        r_range = range(self.r_min(border=True), self.r_max(border=True) + 1)
        c_range = range(self.c_min(border=True), self.c_max(border=True) + 1)

        for r in r_range:
            line_chars: list[str] = []
            for c in c_range:
                line_chars.append(self[Point(r, c)])
            lines.append(''.join(line_chars))

        return '\n'.join(lines)

    def count_pixels(self, pixel: str) -> int:
        if pixel not in VALID_PIXELS:
            raise ValueError('not a valid pixel to count')
        if pixel == self.background_pixel:
            raise ValueError('counting infinite background pixels')
        return len(self.foreground_pixels)


def parse_inputs(puzzle_input: str) -> tuple[str, InfiniteImage]:
    algorithm_part, image_part = puzzle_input.strip().split('\n\n')
    image_enhancement_algorithm = parse_algorithm(algorithm_part)
    input_image = InfiniteImage.parse(image_part)
    return image_enhancement_algorithm, input_image


def extract_square_as_binary(image: InfiniteImage, center: Point) -> int:
    index = 0
    for dr in range(-SQUARE_RADIUS, SQUARE_RADIUS + 1):
        for dc in range(-SQUARE_RADIUS, SQUARE_RADIUS + 1):
            point = Point(center.r + dr, center.c + dc)
            index = (index << 1) ^ PIXEL_AS_BIT[image[point]]
    return index


BIG: Final[int] = 10**9


def apply_algorithm(
    image: InfiniteImage, image_enhancement_algorithm: str,
) -> InfiniteImage:
    pixels: dict[str, set[Point]] = {pixel: set() for pixel in VALID_PIXELS}
    r_range = range(image.r_min(border=True), image.r_max(border=True) + 1)
    c_range = range(image.c_min(border=True), image.c_max(border=True) + 1)

    for r in r_range:
        for c in c_range:
            point = Point(r, c)
            index = extract_square_as_binary(image, point)
            new_pixel = image_enhancement_algorithm[index]
            pixels[new_pixel].add(point)

    infinity_index = extract_square_as_binary(image, Point(-BIG, -BIG))
    background_pixel = image_enhancement_algorithm[infinity_index]
    foreground_pixels = frozenset(pixels[INVERT_PIXEL[background_pixel]])

    return InfiniteImage(foreground_pixels, background_pixel)


def part_1(file: pathlib.Path) -> None:
    puzzle_input = file.read_text(encoding='ascii')
    image_enhancement_algorithm, input_image = parse_inputs(puzzle_input)

    image_1 = apply_algorithm(input_image, image_enhancement_algorithm)
    image_2 = apply_algorithm(image_1, image_enhancement_algorithm)
    lit_pixels_count = image_2.count_pixels(LIGHT_PIXEL)

    # print(input_image, image_1, image_2, sep='\n\n', end='\n\n')
    print('part 1:', lit_pixels_count)


IMAGE_ENHANCEMENTS: Final[int] = 50


def part_2(file: pathlib.Path) -> None:
    puzzle_input = file.read_text(encoding='ascii')
    image_enhancement_algorithm, input_image = parse_inputs(puzzle_input)

    image = input_image
    for _ in range(IMAGE_ENHANCEMENTS):
        image = apply_algorithm(image, image_enhancement_algorithm)
    lit_pixels_count = image.count_pixels(LIGHT_PIXEL)

    print('part 2:', lit_pixels_count)


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
