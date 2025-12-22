import json
from dataclasses import dataclass, field, replace
from itertools import accumulate, chain
from typing import Dict, Tuple

def assembler_compile(code: Dict):
    labels = list(code['transitions'].keys())
    instruction_blocks = [code['transitions'][label] for label in labels]
    all_instructions = list(chain.from_iterable(instruction_blocks))
    block_lengths = [len(block) for block in instruction_blocks]
    offsets = [0] + list(accumulate(block_lengths))
    label_map = {label: offset for label, offset in zip(labels, offsets)}
    label_map = {**label_map, 'HALT': len(all_instructions)}
    return {
        "alphabet": tuple(code["alphabet"]),
        "blank_symbol": code["blank"],
        "instructions": tuple(all_instructions),
        "labels": label_map,
        "start_address": label_map[code['initial']],
        "finals": tuple(code['finals'])
    }


def assembler_compile_file(json_file: str):
    with open(json_file, 'r') as f:
        code_json = f.read()
    return assembler_compile(json.loads(code_json))


@dataclass(frozen=True)
class TuringMachine_struct:
    tape: Tuple[str, ...] = field(default_factory=tuple)
    head: int = 0
    machine_code: Tuple[str, ...] = field(default_factory=tuple)
    alphabet: Tuple[str, ...] = field(default_factory=tuple)
    blank_symbol: str = ""
    start_address: int = 0
    halt_address: Tuple[int, ...] = field(default_factory=tuple)
    instruction_pointer: int = 0


def assembler_assemble(compiled):
    halt_symbols = compiled['finals']

    header_lines = [
        f"ALPHABET: {','.join(compiled['alphabet'])}",
        f"BLANK: {compiled['blank_symbol']}",
        f"START: {compiled['start_address']}",
        f"HALT: {','.join(str(compiled['labels'][s]) for s in halt_symbols)}"
    ]

    body_lines = [
        f"{idx}: READ {ins['read']} WRITE {ins['write']} MOVE {ins['action']} TO {compiled['labels'][ins['to_state']]}"
        for idx, ins in enumerate(compiled['instructions'])
    ]

    return "\n".join(header_lines + body_lines) + "\n"


def _parse_machine_code(machine_code: str):
    lines = machine_code.strip().split("\n")
    alphabet = tuple(lines[0].split(":")[1].strip().split(","))
    blank_symbol = lines[1].split(":")[1].strip()
    start_address = int(lines[2].split(":")[1].strip())
    halt_address = tuple(int(x) for x in lines[3].split(":")[1].strip().split(","))
    instructions = tuple(lines[4:])
    return {
        "alphabet": alphabet,
        "blank_symbol": blank_symbol,
        "start_address": start_address,
        "halt_address": halt_address,
        "instructions": instructions,
    }


def _pad_tape(tape, blank_symbol, size=100):
    return tuple(tape + [blank_symbol] * max(0, size - len(tape)))

def turingmachine_init(tape_str: str, machine_code=""):
    parsed = _parse_machine_code(machine_code)
    return TuringMachine_struct(
        tape=_pad_tape(list(tape_str), parsed["blank_symbol"]),
        head=0,
        machine_code=parsed["instructions"],
        alphabet=parsed["alphabet"],
        blank_symbol=parsed["blank_symbol"],
        start_address=parsed["start_address"],
        halt_address=parsed["halt_address"],
        instruction_pointer=parsed["start_address"],
    )

def turingmachine_step(machine: TuringMachine_struct):
    if machine.instruction_pointer in machine.halt_address:
        return machine, False
    instruction_line = machine.machine_code[machine.instruction_pointer]
    parts = instruction_line.split()
    read_symbol, write_symbol = parts[2], parts[4]
    move_direction, to_state = parts[6], int(parts[8])
    tape_list = list(machine.tape)
    head = machine.head
    instruction_pointer = machine.instruction_pointer
    if tape_list[head] == read_symbol:
        tape_list[head] = write_symbol
        head = head + 1 if move_direction == "RIGHT" else head - 1
        instruction_pointer = to_state
    else:
        instruction_pointer += 1
    return replace(
        machine,
        tape=tuple(tape_list),
        head=head,
        instruction_pointer=instruction_pointer,
    ), True


def turingmachine_run(machine: TuringMachine_struct):
    def loop(state: TuringMachine_struct):
        next_state, running = turingmachine_step(state)
        return loop(next_state) if running else next_state
    return loop(machine)


compiled = assembler_compile_file("example.json")
machine_code = assembler_assemble(compiled)
print("Machine Code:\n", machine_code)
mach = turingmachine_init(tape_str="111-11=", machine_code=machine_code)
final_machine = turingmachine_run(mach)
print("Final Tape:", final_machine.tape[:20])

