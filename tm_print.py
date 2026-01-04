from itertools import chain

BANNER_WIDTH = 80
TAPE_VIEW_WIDTH = 20
STAR = "*"


def help_text() -> str:
    return "\n".join(
        [
            "usage: ft_turing [-h] jsonfile input",
            "positional arguments:",
            "jsonfile json description of the machine",
            "input input of the machine",
            "optional arguments:",
            "-h, --help show this help message and exit",
        ]
    )


def usage_line() -> str:
    return "usage: ft_turing [-h] jsonfile input"


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


def describe_lines_from_json(code: dict, width=BANNER_WIDTH):
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
                lambda t: format_transition(
                    st,
                    t.get("read"),
                    t.get("to_state"),
                    t.get("write"),
                    t.get("action"),
                ),
                ts,
            )
        )

    body = list(chain.from_iterable(map(state_lines, states)))
    return header + body + [STAR * width]
