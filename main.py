import time
import json

class Assembler:
    def __init__(self):
        self.alphabet = []
        self.machine_code = """"""
        self.instructions = []
        self.labels = {}
        self.start_address = None
    
    def compile(self, json_file):
        with open(json_file, 'r') as f:
            code_json = f.read()
        code = json.loads(code_json)
        self.alphabet = code["alphabet"]
        self.blank_symbol = code["blank"]
        labels = code['transitions'].keys()
        initial_label = code['initial']
        for label in labels:
            self.labels[label] = len(self.instructions)
            for instruction in code['transitions'][label]:
                self.instructions.append(instruction)
        self.start_address = self.labels[initial_label]
        self.labels['HALT'] = len(self.instructions)
        self.assemble(code)

    def assemble(self, code):
        halt_symbols = code['finals']
        self.machine_code += f"ALPHABET: {','.join(self.alphabet)}\n"
        self.machine_code += f"BLANK: {self.blank_symbol}\n"
        self.machine_code += f"START: {self.start_address}\n"
        self.machine_code += f"HALT: {','.join([str(self.labels[s]) for s in halt_symbols])}\n"
        for idx, instruction in enumerate(self.instructions):
            read = instruction['read']
            to_state = self.labels[instruction['to_state']]
            write = instruction['write']
            action = instruction['action']
            self.machine_code += f"{idx}: READ {read} WRITE {write} MOVE {action} TO {to_state}\n"
        


class TuringMachine:
    def __init__(self, tape_str : str, machine_code=""):
        tape = list(tape_str)
        self.tape = tape
        self.head = 0
        self.machine_code = machine_code
        self.alphabet = []
        self.blank_symbol = None
        self.start_address = None
        self.halt_address = []
        self.instruction_pointer = 0
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
                self.halt_address = line.split(":")[1].strip()
        self.instruction_pointer = self.start_address
        self.machine_code = lines[4:]

    def load_tape(self, tape):
        print("self.blank_symbol:", self.blank_symbol)
        if not tape:
            return [self.blank_symbol] * 100
        return tape + [self.blank_symbol] * (100 - len(tape))

    def step(self):
        if self.instruction_pointer == int(self.halt_address):
            return False
        current_symbol = self.tape[self.head]
        instruction_line = self.machine_code[self.instruction_pointer]
        parts = instruction_line.split()
        read_symbol = parts[2]
        write_symbol = parts[4]
        move_direction = parts[6]
        to_state = int(parts[8])
        if current_symbol == read_symbol:
            self.tape[self.head] = write_symbol
            if move_direction == "RIGHT":
                self.head += 1
            elif move_direction == "LEFT":
                self.head -= 1
            self.instruction_pointer = to_state
        else:
            self.instruction_pointer += 1
        print("tape:", self.tape[:20])
        return True
    
    def run(self):
        while self.step():
            pass
        return self.tape
        

comp = Assembler()
comp.compile("example.json")
print("Machine Code:\n", comp.machine_code)
mach = TuringMachine(tape_str="1111-1=", machine_code=comp.machine_code)
final_tape = mach.run()
print("Final Tape:", final_tape[:20])

