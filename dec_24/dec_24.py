from abc import ABC, abstractmethod
from collections import deque
from enum import Enum
from dataclasses import dataclass, fields
import pathlib
import sys
from typing import Final, Self


class ALUStatus(Enum):
    NOT_STARTED = 0
    RUNNING = 1
    AWAITING_INPUT = 2
    FINISHED = 3


@dataclass(match_args=False, slots=True)
class ALUState:
    w: int = 0
    x: int = 0
    y: int = 0
    z: int = 0
    ip: int = 0  # Instruction pointer
    st: ALUStatus = ALUStatus.NOT_STARTED

    def get(self, name: str) -> int:
        match name:
            case 'w': return self.w
            case 'x': return self.x
            case 'y': return self.y
            case 'z': return self.z
            case _:
                raise AssertionError('supposed to be unreachable')

    def set(self, name: str, value: int) -> None:
        match name:
            case 'w': self.w = value
            case 'x': self.x = value
            case 'y': self.y = value
            case 'z': self.z = value
            case _:
                raise AssertionError('supposed to be unreachable')

    def copy(self) -> Self:
        return self.__class__(
            w=self.w, x=self.x, y=self.y, z=self.z, ip=self.ip, st=self.st,
        )


VARIABLE_NAMES: Final[frozenset[str]] = frozenset(
    dataclass_field.name for dataclass_field in fields(ALUState)
    if len(dataclass_field.name) == 1
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
        if len(inputs) > 0:
            state.set(self.a, inputs.popleft())
            state.ip += 1
            state.st = ALUStatus.RUNNING
        else:
            state.ip += 0
            state.st = ALUStatus.AWAITING_INPUT


class Add(Instruction):

    __slots__ = ('a', 'b')

    def execute(self, state: ALUState, inputs: deque[int]) -> None:
        a, b = self.fetch_a_and_b(state)
        state.set(self.a, a + b)
        state.ip += 1
        state.st = ALUStatus.RUNNING


class Multiply(Instruction):

    __slots__ = ('a', 'b')

    def execute(self, state: ALUState, inputs: deque[int]) -> None:
        a, b = self.fetch_a_and_b(state)
        state.set(self.a, a * b)
        state.ip += 1
        state.st = ALUStatus.RUNNING


class Divide(Instruction):

    __slots__ = ('a', 'b')

    def execute(self, state: ALUState, inputs: deque[int]) -> None:
        a, b = self.fetch_a_and_b(state)
        if b == 0:
            raise RuntimeError(
                'attempting to execute div instruction with b = 0'
            )
        if b < 0:
            a, b = -a, -b
        if a >= 0:
            state.set(self.a, a // b)
        else:
            state.set(self.a, -(abs(a) // b))
        state.ip += 1
        state.st = ALUStatus.RUNNING


class Modulo(Instruction):

    __slots__ = ('a', 'b')

    def execute(self, state: ALUState, inputs: deque[int]) -> None:
        a, b = self.fetch_a_and_b(state)
        if a < 0:
            raise RuntimeError(
                'attempting to execute mod instruction with a < 0'
            )
        if b <= 0:
            raise RuntimeError(
                'attempting to execute mod instruction with b <= 0'
            )
        state.set(self.a, a % b)
        state.ip += 1
        state.st = ALUStatus.RUNNING


class Equal(Instruction):

    __slots__ = ('a', 'b')

    def execute(self, state: ALUState, inputs: deque[int]) -> None:
        a, b = self.fetch_a_and_b(state)
        state.set(self.a, int(a == b))
        state.ip += 1
        state.st = ALUStatus.RUNNING


INSTRUCTIONS_LOOKUP: Final[dict[str, type[Instruction]]] = {
    'inp': Input,
    'add': Add,
    'mul': Multiply,
    'div': Divide,
    'mod': Modulo,
    'eql': Equal,
}


def parse_instructions(program: str) -> list[Instruction]:
    instructions: list[Instruction] = []
    for line in program.strip().split('\n'):
        instruction_code, *args = line.strip().split()
        InstructionType = INSTRUCTIONS_LOOKUP[instruction_code]
        instruction = InstructionType(*args)
        instructions.append(instruction)
    return instructions


def run_program(
    instructions: list[Instruction],
    inputs: deque[int],
    initial_state: ALUState | None = None,
) -> ALUState:
    state = ALUState() if initial_state is None else initial_state
    if state.st == ALUStatus.FINISHED:
        return state

    while True:
        if state.ip >= len(instructions):
            state.st = ALUStatus.FINISHED
            break
        instruction = instructions[state.ip]
        instruction.execute(state, inputs)
        if state.st == ALUStatus.AWAITING_INPUT:
            break

    return state


MODEL_NUMBER_MAX_VALID_DIGIT: Final[int] = 9
MODEL_NUMBER_MIN_VALID_DIGIT: Final[int] = 1


memo: dict[tuple[int, int, int, int, int, ALUStatus], str | None] = {}


def recursively_find_largest_accepted_model_number(
    state: ALUState, monad_instructions: list[Instruction], z_cap: int
) -> str | None:
    memo_key = (state.w, state.x, state.y, state.z, state.ip, state.st)
    try:
        return memo[memo_key]
    except KeyError:
        pass

    if state.st == ALUStatus.FINISHED:
        memo[memo_key] = '' if state.z == 0 else None
        return '' if state.z == 0 else None
    assert state.st == ALUStatus.AWAITING_INPUT

    if abs(state.z) > z_cap:
        memo[memo_key] = None
        return None

    digit = MODEL_NUMBER_MAX_VALID_DIGIT
    while digit >= MODEL_NUMBER_MIN_VALID_DIGIT:
        next_state = run_program(
            monad_instructions, deque([digit]), state.copy()
        )
        potential_result = recursively_find_largest_accepted_model_number(
            next_state, monad_instructions, z_cap
        )
        if potential_result is not None:
            memo[memo_key] = str(digit) + potential_result
            return str(digit) + potential_result
        digit -= 1

    memo[memo_key] = None
    return None


def find_largest_accepted_model_number(
    monad_instructions: list[Instruction], z_cap: int
) -> str | None:
    started_state = run_program(monad_instructions, deque())
    model_number = recursively_find_largest_accepted_model_number(
        started_state, monad_instructions, z_cap
    )
    return model_number


def part_1(file: pathlib.Path) -> None:
    if file.stem in ('example_01', 'example_02', 'example_03'):
        example_program = file.read_text(encoding='ascii')
        example_instructions = parse_instructions(example_program)
        alu_state = run_program(example_instructions, deque([10, 30]))
        print('part 1:', repr(alu_state))
        return

    monad_program = file.read_text(encoding='ascii')
    monad_instructions = parse_instructions(monad_program)
    z_cap = 10 ** 4  # Limit how large intermediate values of z can get
    while True:
        model_number = find_largest_accepted_model_number(
            monad_instructions, z_cap
        )
        if model_number is not None:
            break
        z_cap *= 10
        memo.clear()
    print('part 1:', model_number)


def part_2(file: pathlib.Path) -> None:
    file.read_text(encoding='ascii')
    print('part 2:', )


if __name__ == '__main__':
    _, arg_1 = sys.argv
    arg_1_path = pathlib.Path(arg_1)
    part_1(arg_1_path)
    part_2(arg_1_path)
