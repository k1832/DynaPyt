# -*- coding: utf-8 -*-
import os, sys

def main():
    base = os.path.abspath(os.path.dirname(__file__))

    if len(sys.argv) > 1:
        base = os.path.abspath(sys.argv[1])

    print(f"Restoring {base}...")

    PY_SUFFIX = ".py"
    ORIGINAL_SUFFIX = ".orig"
    DYNAPYT_JSON_SUFFIX = "-dynapyt.json"

    for curr_path, _dir_names, file_names in os.walk(base):
        if "/example_programs/" in curr_path:
            continue

        for file_path in file_names:
            if file_path.endswith(DYNAPYT_JSON_SUFFIX):
                os.remove(os.path.join(curr_path, file_path))
                continue

            if not file_path.endswith(PY_SUFFIX):
                continue

            py_file = os.path.join(curr_path, file_path)
            orig_file = py_file + ORIGINAL_SUFFIX

            if os.path.exists(py_file) and os.path.exists(orig_file):
                # Remove Python file with instrumentation
                os.remove(py_file)
                # Restore original Python file
                os.rename(orig_file, py_file)

if __name__ == '__main__':
    main()
