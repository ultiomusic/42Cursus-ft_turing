import time

class TuringMachine:
    def __init__(
                 self, 
                 tape=[],
                 name="def", 
                 alphabet=["1", ".", "-", "="], 
                 blank_symbol=".",
                 states= [ "scanright", "eraseone", "subone", "skip", "HALT" ],
                 initial_state="scanright", 
                 final_states=["HALT"],
                 transitions=[]
                 ):
        self.name = name
        self.alphabet = alphabet
        self.blank_symbol = blank_symbol
        self.states = states
        self.initial_state = initial_state
        self.final_states = final_states
        self.transitions = transitions
        self.tape = tape

        self.current_state = initial_state
        self.head_position = 0


    def step(self, instruction):
        current_symbol = self.tape[self.head_position]
        time.sleep(0.5)
        print(self.head_position, "tape :", self.tape, "state:", self.current_state)
        (symbol, new_state, new_symbol, direction) = instruction.values()
        if current_symbol == symbol:
            self.tape[self.head_position] = new_symbol
            self.current_state = new_state
            if direction == "RIGHT":
                self.head_position += 1
            elif direction == "LEFT":
                self.head_position -= 1
            return True
        return False

    def run(self):
        while self.current_state not in self.final_states:
            instructions = self.transitions[self.current_state]
            for instruction in instructions:
                if self.step(instruction):
                    break

tape = [".","1", "1", "1", "=", "1", "1", "."]

mach = TuringMachine(tape=tape, transitions={
"scanright": [
{ "read" : ".", "to_state": "scanright", "write": ".", "action": "RIGHT"},
{ "read" : "1", "to_state": "scanright", "write": "1", "action": "RIGHT"},
{ "read" : "-", "to_state": "scanright", "write": "-", "action": "RIGHT"},
{ "read" : "=", "to_state": "eraseone" , "write": ".", "action": "LEFT" }
],
"eraseone": [
{ "read" : "1", "to_state": "subone", "write": "=", "action": "LEFT"},
{ "read" : "-", "to_state": "HALT" , "write": ".", "action": "LEFT"}
],
"subone": [
{ "read" : "1", "to_state": "subone", "write": "1", "action": "LEFT"},
{ "read" : "-", "to_state": "skip" , "write": "-", "action": "LEFT"}
],
"skip": [
{ "read" : ".", "to_state": "skip" , "write": ".", "action": "LEFT"},
{ "read" : "1", "to_state": "scanright", "write": ".", "action": "RIGHT"}
]
})


mach.run()
print(mach.tape)
