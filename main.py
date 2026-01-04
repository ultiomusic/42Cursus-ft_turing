import json
import sys
from dataclasses import dataclass, field, replace
from itertools import accumulate, chain
from typing import Dict, Tuple

BANNER_WIDTH = 80
TAPE_VIEW_WIDTH = 20
STAR = "*"

LABEL_MAP: Dict[str, int] = {}
ADDR_TO_LABEL: Dict[int, str] = {}
STATE_END_MAP: Dict[str, int] = {}


def fmt_bracket(items):
    return "[ " + ", ".join(map(str, items)) + " ]"


def banner_lines(name, width=BANNER_WIDTH):
    top = STAR * width
    empty = STAR + (" " * (width - 2)) + STAR
    mid = STAR + " " + name.center(width - 4) + " " + STAR
    return [top, empty, mid, empty, top]


def format_transition(from_state, read, to_state, write, action):
    return f"({from_state}, {read}) -> ({to_state}, {write}, {action})"


def render_tape(tape, head, width=TAPE_VIEW_WIDTH):
    def cell(i):
        s = tape[i]
        return f"<{s}>" if i == head else s

    return "[" + "".join(map(cell, range(width))) + "]"


def ip_to_label(label_map: Dict[str, int], ip: int) -> str:
    items = sorted(
        filter(lambda kv: kv[0] != "HALT", label_map.items()),
        key=lambda kv: kv[1],
    )
    best = max(filter(lambda kv: kv[1] <= ip, items), key=lambda kv: kv[1], default=("?", -1))
    return best[0]


def describe_lines_from_json(code: Dict, width=BANNER_WIDTH):
    name = code.get("name", "")
    alphabet = code.get("alphabet", [])
    states = code.get("states", [])
    initial = code.get("initial", "")
    finals = code.get("finals", [])
    transitions = code.get("transitions", {})

    header = list(
        chain(
            banner_lines(name, width),
            [
                f"Alphabet: {fmt_bracket(alphabet)}",
                f"States : {fmt_bracket(states)}",
                f"Initial : {initial}",
                f"Finals : {fmt_bracket(finals)}",
            ],
        )
    )

    def state_lines(st):
        ts = transitions.get(st, [])
        return list(
            map(
                lambda t: format_transition(st, t["read"], t["to_state"], t["write"], t["action"]),
                ts,
            )
        )

    body = list(chain.from_iterable(map(state_lines, states)))
    return header + body + [STAR * width]


def assembler_compile(code: Dict):
    if "transitions" not in code.keys() or not isinstance(code["transitions"], dict):
        raise ValueError("Invalid code: missing 'transitions'")
    if "alphabet" not in code.keys() or not isinstance(code["alphabet"], list):
        raise ValueError("Invalid code: missing 'alphabet'")
    if "blank" not in code.keys() or not isinstance(code["blank"], str):
        raise ValueError("Invalid code: missing 'blank'")
    if "initial" not in code.keys() or not isinstance(code["initial"], str):
        raise ValueError("Invalid code: missing 'initial'")
    if "finals" not in code.keys() or not isinstance(code["finals"], list):
        raise ValueError("Invalid code: missing 'finals'")

    labels = list(code["transitions"].keys())
    instruction_blocks = list(map(lambda label: code["transitions"][label], labels))
    all_instructions = list(chain.from_iterable(instruction_blocks))
    block_lengths = list(map(len, instruction_blocks))
    offsets = [0] + list(accumulate(block_lengths))
    label_map = dict(zip(labels, offsets))
    label_map = {**label_map, "HALT": len(all_instructions)}

    state_end_map = dict(zip(labels, offsets[1:]))

    return {
        "alphabet": tuple(code["alphabet"]),
        "blank_symbol": code["blank"],
        "instructions": tuple(all_instructions),
        "labels": label_map,
        "state_ends": state_end_map,
        "start_address": label_map[code["initial"]],
        "finals": tuple(code["finals"]),
    }


def assembler_compile_file(json_file: str):
    with open(json_file, "r", encoding="utf-8") as f:
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
    halt_symbols = compiled["finals"]

    header_lines = [
        f"ALPHABET: {','.join(compiled['alphabet'])}",
        f"BLANK: {compiled['blank_symbol']}",
        f"START: {compiled['start_address']}",
        f"HALT: {','.join(map(lambda s: str(compiled['labels'][s]), halt_symbols))}",
    ]

    def ins_line(idx_ins):
        idx, ins = idx_ins
        return (
            f"{idx}: READ {ins['read']} WRITE {ins['write']} "
            f"MOVE {ins['action']} TO {compiled['labels'][ins['to_state']]}"
        )

    body_lines = list(map(ins_line, enumerate(compiled["instructions"])))
    return "\n".join(header_lines + body_lines) + "\n"


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

    tape_list = list(machine.tape)
    head = machine.head
    ip = machine.instruction_pointer

    if tape_list[head] not in machine.alphabet:
        raise ValueError("Tape symbol not in alphabet")

    current_state = ip_to_label(LABEL_MAP, ip)
    state_start = LABEL_MAP.get(current_state, ip)
    state_end = STATE_END_MAP.get(current_state, state_start)

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
        return machine, False

    def matched(ins):
        read_symbol, write_symbol, move_direction, to_state = ins

        if read_symbol not in machine.alphabet or write_symbol not in machine.alphabet:
            raise ValueError("Symbol not in alphabet")

        to_state_name = ADDR_TO_LABEL.get(to_state, str(to_state))
        print(
            f"{render_tape(machine.tape, head, TAPE_VIEW_WIDTH)} "
            f"{format_transition(current_state, read_symbol, to_state_name, write_symbol, move_direction)}"
        )

        tape_list[head] = write_symbol
        next_head = head + 1 if move_direction == "RIGHT" else head - 1
        next_ip = to_state

        return replace(machine, tape=tuple(tape_list), head=next_head, instruction_pointer=next_ip), True

    return blocked() if match is None else matched(match)


def turingmachine_run(machine: TuringMachine_struct):
    def loop(state: TuringMachine_struct):
        next_state, running = turingmachine_step(state)
        return loop(next_state) if running else next_state

    return loop(machine)


def main():
    global LABEL_MAP, ADDR_TO_LABEL, STATE_END_MAP

    ok = len(sys.argv) == 3
    if not ok:
        prog = sys.argv[0] if sys.argv else "ft_turing.py"
        print(f"usage: {prog} <jsonfile> <input>")
        raise SystemExit(1)

    jsonfile = sys.argv[1]
    tape_input = sys.argv[2]

    with open(jsonfile, "r", encoding="utf-8") as f:
        code = json.loads(f.read())

    compiled = assembler_compile(code)
    LABEL_MAP = compiled["labels"]
    STATE_END_MAP = compiled["state_ends"]
    ADDR_TO_LABEL = dict(map(lambda kv: (kv[1], kv[0]), LABEL_MAP.items()))

    print("\n".join(describe_lines_from_json(code, BANNER_WIDTH)))

    machine_code = assembler_assemble(compiled)
    mach = turingmachine_init(tape_str=tape_input, machine_code=machine_code)
    turingmachine_run(mach)


if __name__ == "__main__":
    main()
