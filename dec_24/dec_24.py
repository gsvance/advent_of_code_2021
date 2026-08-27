from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass, fields
import pathlib
import sys
from typing import Final


@dataclass(match_args=False, slots=True)
class ALUState:
    w: int = 0
    x: int = 0
    y: int = 0
    z: int = 0

    def get(self, name: str) -> int:
        return getattr(self, name)

    def set(self, name: str, value: int) -> None:
        setattr(self, name, value)


VARIABLE_NAMES: Final[frozenset[str]] = frozenset(
    field.name for field in fields(ALUState)
)


def check_variable_name(name: str) -> str:
    if name not in VARIABLE_NAMES:
        raise ValueError(f'invalid variable name for ALU state: {name!r}')
    return name


def check_variable_name_or_number(name_or_number: str) -> str | int:
    if name_or_number in VARIABLE_NAMES:
        return name_or_number
    try:
        return int(name_or_number)
    except ValueError:
        pass
    raise ValueError(
        f'invalid variable name or number for ALU state: {name_or_number!r}'
    )


class Instruction(ABC):

    def __init__(self, a: str, b: str) -> None:
        self.a: str = check_variable_name(a)
        self.b: str | int = check_variable_name_or_number(b)

    def __repr__(self) -> str:
        a = self.a
        if not hasattr(self, 'b'):
            return f'{self.__class__.__name__}({a=!r})'
        b = self.b
        return f'{self.__class__.__name__}({a=!r}, {b=!r})'

    def fetch_a_and_b(self, state: ALUState) -> tuple[int, int]:
        a = state.get(self.a)
        b = state.get(self.b) if isinstance(self.b, str) else self.b
        return a, b

    @abstractmethod
    def execute(self, state: ALUState, inputs: deque[int]) -> None:
        ...


class Input(Instruction):

    __slots__ = ('a',)

    def __init__(self, a: str) -> None:
        super().__init__(a, a)
        del self.b

    def execute(self, state: ALUState, inputs: deque[int]) -> None:
        state.set(self.a, inputs.popleft())


class Add(Instruction):

    __slots__ = ('a', 'b')

    def execute(self, state: ALUState, inputs: deque[int]) -> None:
        a, b = self.fetch_a_and_b(state)
        state.set(self.a, a + b)


class Multiply(Instruction):

    __slots__ = ('a', 'b')

    def execute(self, state: ALUState, inputs: deque[int]) -> None:
        a, b = self.fetch_a_and_b(state)
        state.set(self.a, a * b)


class Divide(Instruction):

    __slots__ = ('a', 'b')

    def execute(self, state: ALUState, inputs: deque[int]) -> None:
        a, b = self.fetch_a_and_b(state)
        if b == 0:
            raise RuntimeError('attempting to execute div with b=0')
        if b < 0:
            a, b = -a, -b
        if a >= 0:
            state.set(self.a, a // b)
        else:
            state.set(self.a, -(-a // b))


class Modulo(Instruction):

    __slots__ = ('a', 'b')

    def execute(self, state: ALUState, inputs: deque[int]) -> None:
        a, b = self.fetch_a_and_b(state)
        if a < 0 or b <= 0:
            raise RuntimeError('attempting to execute mod with a<0 or b<=0')
        state.set(self.a, a % b)


class Equal(Instruction):

    __slots__ = ('a', 'b')

    def execute(self, state: ALUState, inputs: deque[int]) -> None:
        a, b = self.fetch_a_and_b(state)
        state.set(self.a, int(a == b))


INSTRUCTIONS_LOOKUP: Final[dict[str, type[Instruction]]] = {
    'inp': Input,
    'add': Add,
    'mul': Multiply,
    'div': Divide,
    'mod': Modulo,
    'eql': Equal,
}


def run_program(
    instructions: list[Instruction],
    inputs: deque[int],
    initial_state: ALUState | None = None,
) -> ALUState:
    state = ALUState() if initial_state is None else initial_state
    for instruction in instructions:
        instruction.execute(state, inputs)
    return state


def is_valid(model_number: int, monad_instructions: list[Instruction]) -> bool:
    model_number_digits = deque(int(digit) for digit in str(model_number))
    state = run_program(monad_instructions, model_number_digits)
    return state.z == 0


MODEL_NUMBER_DIGIT_COUNT: Final[int] = 14

MODEL_NUMBER_UPPER_LIMIT: Final[int] = 10 ** MODEL_NUMBER_DIGIT_COUNT - 1
MODEL_NUMBER_LOWER_LIMIT: Final[int] = 10 ** (MODEL_NUMBER_DIGIT_COUNT - 1)


def generate_large_model_numbers() -> Iterator[int]:
    model_number = MODEL_NUMBER_UPPER_LIMIT
    while model_number >= MODEL_NUMBER_LOWER_LIMIT:
        if '0' not in str(model_number):
            yield model_number
        model_number -= 1


def parse_instructions(program: str) -> list[Instruction]:
    instructions: list[Instruction] = []
    for line in program.strip().split('\n'):
        instruction_code, *args = line.strip().split()
        InstructionType = INSTRUCTIONS_LOOKUP[instruction_code]
        instruction = InstructionType(*args)
        instructions.append(instruction)
    return instructions


def part_1(file: pathlib.Path) -> None:
    monad_program = file.read_text(encoding='ascii')
    monad_instructions = parse_instructions(monad_program)
    for model_number in generate_large_model_numbers():
        if is_valid(model_number, monad_instructions):
            print('part 1:', model_number)
            break


def part_2(file: pathlib.Path) -> None:
    file.read_text(encoding='ascii')
    print('part 2:', )


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
