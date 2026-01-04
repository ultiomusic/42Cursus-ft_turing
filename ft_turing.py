import sys

from tm_io import read_json_file, eprint
from tm_print import help_text, usage_line, describe_lines_from_json, BANNER_WIDTH
from tm_assembler import assembler_compile, assembler_assemble
from tm_runtime import turingmachine_init, turingmachine_run, build_addr_to_label


def main():
    args = tuple(sys.argv[1:])

    if "-h" in args or "--help" in args:
        print(help_text())
        return 0

    if len(args) != 2:
        print(usage_line())
        return 1

    jsonfile, tape_input = args[0], args[1]

    code, err = read_json_file(jsonfile)
    if err:
        eprint(err)
        return 1

    compiled, cerr = assembler_compile(code)
    if cerr:
        eprint("Error: invalid machine description")
        eprint(cerr)
        return 1

    machine_code, aerr = assembler_assemble(compiled)
    if aerr:
        eprint("Error: invalid machine description")
        eprint(aerr)
        return 1

    addr_to_label = build_addr_to_label(compiled["labels"])

    print("\n".join(describe_lines_from_json(code, BANNER_WIDTH)))

    try:
        mach = turingmachine_init(tape_str=tape_input, machine_code=machine_code)
        _, run_err = turingmachine_run(
            mach,
            label_map=compiled["labels"],
            state_end_map=compiled["state_ends"],
            addr_to_label=addr_to_label,
        )
        if run_err:
            eprint(run_err)
            return 1
        return 0
    except RecursionError:
        eprint("Runtime error: too many steps (recursion limit reached)")
        return 1
    except Exception as ex:
        eprint(f"Runtime error: {type(ex).__name__}: {ex}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
