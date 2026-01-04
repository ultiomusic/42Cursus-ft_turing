import json
import sys


def eprint(msg: str):
    sys.stderr.write(msg + "\n")


def read_json_file(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.loads(f.read()), ""
    except FileNotFoundError:
        return None, f"Error: file not found: {path}"
    except PermissionError:
        return None, f"Error: permission denied: {path}"
    except json.JSONDecodeError as ex:
        return None, f"Error: invalid JSON: {ex}"
    except Exception as ex:
        return None, f"Error: {type(ex).__name__}: {ex}"
