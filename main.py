import json
import time
from functools import reduce
from itertools import chain

BANNER_WIDTH = 80
TAPE_VIEW_WIDTH = 20
STAR = "*"

def fmt_bracket(items):
    return "[ " + ", ".join(map(str, items)) + " ]"

def banner_lines(name, width=BANNER_WIDTH):
    top = STAR * width
    empty = STAR + (" " * (width - 2)) + STAR
    mid = STAR + " " + name.center(width - 4) + " " + STAR
    return [top, empty, mid, empty, top]

def render_tape(tape, head, blank, width=TAPE_VIEW_WIDTH):
    def cell(i):
        v = tape[i] if 0 <= i < len(tape) else None
        s = blank if v is None else v
        return f"<{s}>" if i == head else s
    return "[" + "".join(map(cell, range(width))) + "]"

def format_transition(from_state, read, to_state, write, action):
    return f"({from_state}, {read}) -> ({to_state}, {write}, {action})"

class Assembler:
    def __init__(self):
        self.alphabet = []
        self.machine_code = """"""
        self.instructions = []
        self.labels = {}
        self.start_address = None
        self._addr_to_label = {}
        self._json_code = None

    def compile(self, json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            code = json.loads(f.read())
        self._json_code = code
        self.alphabet = code["alphabet"]
        self.blank_symbol = code["blank"]
        labels = code["transitions"].keys()
        initial_label = code["initial"]
        for label in labels:
            self.labels[label] = len(self.instructions)
            for instruction in code["transitions"][label]:
                self.instructions.append(instruction)
        self.start_address = self.labels[initial_label]
        self.labels["HALT"] = len(self.instructions)
        self._addr_to_label = {v: k for k, v in self.labels.items()}
        self.assemble(code)

    def assemble(self, code):
        halt_symbols = code["finals"]
        self.machine_code += f"ALPHABET: {','.join(self.alphabet)}\n"
        self.machine_code += f"BLANK: {self.blank_symbol}\n"
        self.machine_code += f"START: {self.start_address}\n"
        self.machine_code += f"HALT: {','.join([str(self.labels[s]) for s in halt_symbols])}\n"
        for idx, instruction in enumerate(self.instructions):
            read = instruction["read"]
            to_state = self.labels[instruction["to_state"]]
            write = instruction["write"]
            action = instruction["action"]
            self.machine_code += f"{idx}: READ {read} WRITE {write} MOVE {action} TO {to_state}\n"

    def addr_to_label(self):
        return self._addr_to_label

    def ip_to_label(self, ip):
        starts = sorted(filter(lambda kv: kv[0] != "HALT", self.labels.items()), key=lambda kv: kv[1])
        candidates = tuple(filter(lambda kv: kv[1] <= ip, starts))
        return reduce(lambda acc, kv: kv if kv[1] >= acc[1] else acc, candidates, ("?", -1))[0]

    def describe_lines(self, width=BANNER_WIDTH):
        code = self._json_code or {}
        name = code.get("name", "")
        alphabet = code.get("alphabet", [])
        states = code.get("states", [])
        initial = code.get("initial", "")
        finals = code.get("finals", [])
        transitions = code.get("transitions", {})

        header = list(chain(
            banner_lines(name, width),
            [
                f"Alphabet: {fmt_bracket(alphabet)}",
                f"States : {fmt_bracket(states)}",
                f"Initial : {initial}",
                f"Finals : {fmt_bracket(finals)}",
            ]
        ))

        def state_lines(st):
            ts = transitions.get(st, [])
            return list(map(
                lambda t: format_transition(st, t["read"], t["to_state"], t["write"], t["action"]),
                ts
            ))

        body = list(chain.from_iterable(map(state_lines, states)))
        return list(chain(header, body, [STAR * width]))

class TuringMachine:
    def __init__(self, tape_str: str, machine_code="", ip_to_label_fn=None, addr_to_label_map=None):
        tape = list(tape_str)
        self.tape = tape
        self.head = 0
        self.machine_code = machine_code
        self.alphabet = []
        self.blank_symbol = None
        self.start_address = None
        self.halt_address = []
        self.instruction_pointer = 0
        self.ip_to_label_fn = ip_to_label_fn or (lambda _ip: "?")
        self.addr_to_label_map = addr_to_label_map or {}
        self.tape = self.load_tape(tape)
        self.init_code()

    def init_code(self):
        lines = self.machine_code.strip().split("\n")
        for line in lines:
            if line.startswith("ALPHABET:"):
                self.alphabet = line.split(":")[1].strip().split(",")
            elif line.startswith("BLANK:"):
                self.blank_symbol = line.split(":")[1].strip()
            elif line.startswith("START:"):
                self.start_address = int(line.split(":")[1].strip())
            elif line.startswith("HALT:"):
                self.halt_address = [int(x) for x in line.split(":")[1].strip().split(",")]
        self.instruction_pointer = self.start_address
        self.machine_code = lines[4:]

    def load_tape(self, tape):
        if not tape:
            return [self.blank_symbol] * 100
        return tape + [self.blank_symbol] * (100 - len(tape))

    def step(self):
        if self.instruction_pointer in self.halt_address:
            return False

        instruction_line = self.machine_code[self.instruction_pointer]
        parts = instruction_line.split()
        read_symbol = parts[2]
        write_symbol = parts[4]
        move_direction = parts[6]
        to_state_addr = int(parts[8])

        from_state_name = self.ip_to_label_fn(self.instruction_pointer)
        to_state_name = self.addr_to_label_map.get(to_state_addr, str(to_state_addr))

        tape_view = render_tape(self.tape, self.head, self.blank_symbol, TAPE_VIEW_WIDTH)
        print(f"{tape_view} {format_transition(from_state_name, read_symbol, to_state_name, write_symbol, move_direction)}")

        current_symbol = self.tape[self.head]
        if current_symbol == read_symbol:
            self.tape[self.head] = write_symbol
            self.head += 1 if move_direction == "RIGHT" else (-1 if move_direction == "LEFT" else 0)
            self.instruction_pointer = to_state_addr
        else:
            self.instruction_pointer += 1

        return True

    def run(self):
        while self.step():
            pass
        return self.tape

if __name__ == "__main__":
    comp = Assembler()
    comp.compile("example.json")
    print("\n".join(comp.describe_lines(BANNER_WIDTH)))
    mach = TuringMachine(
        tape_str="1111-1=",
        machine_code=comp.machine_code,
        ip_to_label_fn=comp.ip_to_label,
        addr_to_label_map=comp.addr_to_label()
    )
    final_tape = mach.run()
    print("Final Tape:", final_tape[:20])