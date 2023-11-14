# -*- coding: utf-8 -*-
import os, sys

def main():
    base = os.path.abspath(os.path.dirname(__file__))

    if len(sys.argv) > 1:
        base = os.path.abspath(sys.argv[1])

    print(f"Clearing coverage data in {base}...")

    COVERAGE_DATA_PREFIX = ".coverage"
    COVERAGE_CONFIG_FILE_NAME = ".coveragerc"

    count = 0
    for curr_dir, _, file_names in os.walk(base):

        for file_name in file_names:
            if not file_name.startswith(COVERAGE_DATA_PREFIX):
                continue

            if file_name == COVERAGE_CONFIG_FILE_NAME:
                # Config file has the same prefix
                # Don't remove it
                continue

            file_path = os.path.join(curr_dir, file_name)

            if not os.path.exists(file_path):
                continue

            print(f"Removing {file_path}")
            os.remove(file_path)
            count += 1

    print(f"Removed {count} file(s)")

if __name__ == '__main__':
    main()
