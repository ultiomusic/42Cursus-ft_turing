def _is_str(x):
    return isinstance(x, str)


def _is_list(x):
    return isinstance(x, list)


def _is_dict(x):
    return isinstance(x, dict)


def _uniq(seq):
    return len(set(seq)) == len(seq)


def _first_error(errors):
    return next(filter(lambda x: x is not None, errors), None)


def validate_code(code: dict):
    if not _is_dict(code):
        return False, "Invalid JSON: root must be an object"

    required = ("alphabet", "blank", "states", "initial", "finals", "transitions")
    missing = _first_error(map(lambda k: None if k in code else f"Invalid code: missing '{k}'", required))
    if missing is not None:
        return False, missing

    alphabet = code.get("alphabet")
    blank = code.get("blank")
    states = code.get("states")
    initial = code.get("initial")
    finals = code.get("finals")
    transitions = code.get("transitions")

    if not _is_list(alphabet):
        return False, "Invalid code: 'alphabet' must be a list"
    if not _is_str(blank):
        return False, "Invalid code: 'blank' must be a string"
    if not _is_list(states):
        return False, "Invalid code: 'states' must be a list"
    if not _is_str(initial):
        return False, "Invalid code: 'initial' must be a string"
    if not _is_list(finals):
        return False, "Invalid code: 'finals' must be a list"
    if not _is_dict(transitions):
        return False, "Invalid code: 'transitions' must be an object"

    if _first_error(map(lambda s: None if _is_str(s) else "x", states)) is not None:
        return False, "Invalid code: every state must be a string"
    if not _uniq(states):
        return False, "Invalid code: 'states' must not contain duplicates"
    if len(states) == 0:
        return False, "Invalid code: 'states' must not be empty"

    if _first_error(map(lambda a: None if (_is_str(a) and len(a) == 1) else "x", alphabet)) is not None:
        return False, "Invalid code: alphabet symbols must be 1-char strings"
    if not _uniq(alphabet):
        return False, "Invalid code: 'alphabet' must not contain duplicates"

    if len(blank) != 1:
        return False, "Invalid code: 'blank' must be a 1-char string"
    if blank not in alphabet:
        return False, "Invalid code: 'blank' must be included in 'alphabet'"

    if initial not in states:
        return False, "Invalid code: 'initial' must be one of the 'states'"

    if _first_error(map(lambda s: None if _is_str(s) else "x", finals)) is not None:
        return False, "Invalid code: every final must be a string"

    states_for_layout = states if "HALT" in states else (states + ["HALT"])
    states_set = set(states_for_layout)

    if _first_error(map(lambda f: None if f in states_set else "x", finals)) is not None:
        return False, "Invalid code: every final must be in 'states' (or HALT)"

    bad_key = _first_error(map(lambda k: None if k in states_set else f"Invalid code: transition state '{k}' not in states", transitions.keys()))
    if bad_key is not None:
        return False, bad_key

    def validate_transition(st, idx, t):
        if not _is_dict(t):
            return f"Invalid code: transitions['{st}'][{idx}] must be an object"

        need = ("read", "to_state", "write", "action")
        miss = _first_error(map(lambda k: None if k in t else f"Invalid code: transitions['{st}'][{idx}] missing '{k}'", need))
        if miss is not None:
            return miss

        read = t.get("read")
        write = t.get("write")
        to_state = t.get("to_state")
        action = t.get("action")

        if not (_is_str(read) and len(read) == 1):
            return f"Invalid code: transitions['{st}'][{idx}].read must be a 1-char string"
        if not (_is_str(write) and len(write) == 1):
            return f"Invalid code: transitions['{st}'][{idx}].write must be a 1-char string"
        if not _is_str(to_state):
            return f"Invalid code: transitions['{st}'][{idx}].to_state must be a string"
        if not _is_str(action):
            return f"Invalid code: transitions['{st}'][{idx}].action must be a string"

        if read not in alphabet:
            return f"Invalid code: transitions['{st}'][{idx}].read '{read}' not in alphabet"
        if write not in alphabet:
            return f"Invalid code: transitions['{st}'][{idx}].write '{write}' not in alphabet"
        if to_state not in states_set:
            return f"Invalid code: transitions['{st}'][{idx}].to_state '{to_state}' not in states"
        if action not in ("LEFT", "RIGHT"):
            return f"Invalid code: transitions['{st}'][{idx}].action must be LEFT or RIGHT"

        return None

    def validate_state_block(st):
        ts = transitions.get(st, [])
        if ts is None:
            return f"Invalid code: transitions['{st}'] must be a list"
        if not _is_list(ts):
            return f"Invalid code: transitions['{st}'] must be a list"

        err = _first_error(map(lambda it: validate_transition(st, it[0], it[1]), enumerate(ts)))
        if err is not None:
            return err

        reads = tuple(map(lambda t: t.get("read"), ts))
        if not _uniq(reads):
            return f"Invalid code: transitions['{st}'] has duplicate 'read' rules (non-deterministic)"

        return None

    err2 = _first_error(map(validate_state_block, transitions.keys()))
    if err2 is not None:
        return False, err2

    return True, ""
