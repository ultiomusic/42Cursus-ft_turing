from itertools import accumulate, chain

from tm_validate import validate_code, _first_error


def assembler_compile(code: dict):
    ok, msg = validate_code(code)
    if not ok:
        return None, msg

    alphabet = tuple(code["alphabet"])
    blank_symbol = code["blank"]
    states = code["states"]
    transitions = code["transitions"]
    finals = tuple(code["finals"])

    states_for_layout = states if "HALT" in states else (states + ["HALT"])

    instruction_blocks = list(map(lambda st: transitions.get(st, []), states_for_layout))
    all_instructions = list(chain.from_iterable(instruction_blocks))
    block_lengths = list(map(len, instruction_blocks))
    offsets = [0] + list(accumulate(block_lengths))

    label_map = dict(zip(states_for_layout, offsets))
    state_end_map = dict(zip(states_for_layout, offsets[1:]))

    start_state = code["initial"]
    start_address = label_map.get(start_state, 0)

    return (
        {
            "alphabet": alphabet,
            "blank_symbol": blank_symbol,
            "instructions": tuple(all_instructions),
            "labels": label_map,
            "state_ends": state_end_map,
            "start_address": start_address,
            "finals": finals,
        },
        "",
    )


def assembler_assemble(compiled: dict):
    halt_symbols = compiled["finals"]

    def halt_addr_of(s):
        return compiled["labels"].get(s, None)

    bad_halt = _first_error(map(lambda s: None if halt_addr_of(s) is not None else f"Invalid code: final state '{s}' has no address", halt_symbols))
    if bad_halt is not None:
        return None, bad_halt

    header_lines = [
        f"ALPHABET: {','.join(compiled['alphabet'])}",
        f"BLANK: {compiled['blank_symbol']}",
        f"START: {compiled['start_address']}",
        f"HALT: {','.join(map(lambda s: str(compiled['labels'][s]), halt_symbols))}",
    ]

    def ins_line(idx_ins):
        idx, ins = idx_ins
        to_addr = compiled["labels"].get(ins.get("to_state"), None)
        if to_addr is None:
            return None, f"Invalid code: transition TO '{ins.get('to_state')}' has no address"
        return (
            f"{idx}: READ {ins['read']} WRITE {ins['write']} "
            f"MOVE {ins['action']} TO {to_addr}"
        ), ""

    def build_lines(items):
        first_bad = _first_error(map(lambda x: x[1] if x[1] else None, items))
        if first_bad is not None:
            return None, first_bad
        return list(map(lambda x: x[0], items)), ""

    built, err = build_lines(list(map(ins_line, enumerate(compiled["instructions"]))))
    if err:
        return None, err

    return "\n".join(header_lines + built) + "\n", ""
