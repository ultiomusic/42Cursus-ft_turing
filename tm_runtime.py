from dataclasses import dataclass, field, replace
from typing import Tuple, Dict

from tm_print import render_tape, format_transition, TAPE_VIEW_WIDTH


@dataclass(frozen=True)
class TuringMachine:
    tape: Tuple[str, ...] = field(default_factory=tuple)
    head: int = 0
    machine_code: Tuple[str, ...] = field(default_factory=tuple)
    alphabet: Tuple[str, ...] = field(default_factory=tuple)
    blank_symbol: str = ""
    start_address: int = 0
    halt_address: Tuple[int, ...] = field(default_factory=tuple)
    instruction_pointer: int = 0


def build_addr_to_label(label_map: Dict[str, int]) -> Dict[int, str]:
    return dict(map(lambda kv: (kv[1], kv[0]), label_map.items()))


def ip_to_label(label_map: Dict[str, int], ip: int) -> str:
    items = sorted(
        filter(lambda kv: kv[0] != "HALT", label_map.items()),
        key=lambda kv: kv[1],
    )
    best = max(filter(lambda kv: kv[1] <= ip, items), key=lambda kv: kv[1], default=("?", -1))
    return best[0]


def _parse_machine_code(machine_code: str):
    lines = machine_code.strip().split("\n")
    alphabet = tuple(lines[0].split(":")[1].strip().split(","))
    blank_symbol = lines[1].split(":")[1].strip()
    start_address = int(lines[2].split(":")[1].strip())
    halt_address = tuple(map(int, lines[3].split(":")[1].strip().split(",")))
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


def turingmachine_init(tape_str: str, machine_code: str):
    parsed = _parse_machine_code(machine_code)
    return TuringMachine(
        tape=_pad_tape(list(tape_str), parsed["blank_symbol"]),
        head=0,
        machine_code=parsed["instructions"],
        alphabet=parsed["alphabet"],
        blank_symbol=parsed["blank_symbol"],
        start_address=parsed["start_address"],
        halt_address=parsed["halt_address"],
        instruction_pointer=parsed["start_address"],
    )


def turingmachine_step(machine: TuringMachine, label_map: Dict[str, int], state_end_map: Dict[str, int], addr_to_label: Dict[int, str]):
    if machine.instruction_pointer in machine.halt_address:
        return machine, False, ""

    try:
        tape_list = list(machine.tape)
        head = machine.head
        ip = machine.instruction_pointer

        if head < 0 or head >= len(tape_list):
            return machine, False, "Runtime error: head moved out of tape bounds (infinite tape not implemented yet)"

        if tape_list[head] not in machine.alphabet:
            return machine, False, "Runtime error: tape symbol not in alphabet"

        current_state = ip_to_label(label_map, ip)
        state_start = label_map.get(current_state, ip)
        state_end = state_end_map.get(current_state, state_start)

        block_lines = machine.machine_code[state_start:state_end]

        def parse_line(line: str):
            parts = line.split()
            read_symbol = parts[2]
            write_symbol = parts[4]
            move_direction = parts[6]
            to_state = int(parts[8])
            return read_symbol, write_symbol, move_direction, to_state

        cur_symbol = tape_list[head]
        parsed_block = tuple(map(parse_line, block_lines))
        match = next(filter(lambda ins: ins[0] == cur_symbol, parsed_block), None)

        def blocked():
            print(
                f"{render_tape(machine.tape, head, TAPE_VIEW_WIDTH)} "
                f"BLOCKED in state {current_state} on symbol {cur_symbol}"
            )
            return machine, False, ""

        def matched(ins):
            read_symbol, write_symbol, move_direction, to_state = ins

            if read_symbol not in machine.alphabet or write_symbol not in machine.alphabet:
                return machine, False, "Runtime error: symbol not in alphabet"

            to_state_name = addr_to_label.get(to_state, str(to_state))
            print(
                f"{render_tape(machine.tape, head, TAPE_VIEW_WIDTH)} "
                f"{format_transition(current_state, read_symbol, to_state_name, write_symbol, move_direction)}"
            )

            tape_list[head] = write_symbol
            next_head = head + 1 if move_direction == "RIGHT" else head - 1
            next_ip = to_state

            return replace(machine, tape=tuple(tape_list), head=next_head, instruction_pointer=next_ip), True, ""

        return blocked() if match is None else matched(match)

    except Exception as ex:
        return machine, False, f"Runtime error: {type(ex).__name__}: {ex}"


def turingmachine_run(machine: TuringMachine, label_map: Dict[str, int], state_end_map: Dict[str, int], addr_to_label: Dict[int, str]):
    def loop(state: TuringMachine):
        next_state, running, err = turingmachine_step(state, label_map, state_end_map, addr_to_label)
        if err:
            return next_state, err
        return loop(next_state) if running else (next_state, "")

    return loop(machine)
