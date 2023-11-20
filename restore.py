# -*- coding: utf-8 -*-
import os, sys
import argparse

def main():
    base = os.path.abspath(os.path.dirname(__file__))

    parser = argparse.ArgumentParser()
    parser.add_argument("--keep-inst", action="store_true", help="Restore original file but keep the instrumented file")
    parser.add_argument("--restore-inst", action="store_true", help="Restore instrumented file")
    parser.add_argument("--path", action="store", help="Path to the directory to restore")
    args = parser.parse_args()

    if args.path:
        base = os.path.abspath(args.path)

    print(f"Path: {base}")

    if args.keep_inst and args.restore_inst:
        raise Exception("Cannot specify both --keep-inst and --restore-inst")

    if args.keep_inst:
        print("Restore original file but keep the instrumented file")
    elif args.restore_inst:
        print("Restore instrumented file from backup")
    else:
        print("Restore original file, and remove the instrumented file")

    PY_SUFFIX = ".py"
    ORIGINAL_SUFFIX = ".orig"
    INSTRUMENT_SUFFIX = ".inst"
    DYNAPYT_JSON_SUFFIX = "-dynapyt.json"
    DYNAPYT_JSON_BACKUP_SUFFIX = "-backup.json.backup"

    for curr_path, _dir_names, file_names in os.walk(base):
        if "/example_programs/" in curr_path:
            continue

        for file_name in file_names:
            file_path = os.path.join(curr_path, file_name)
            if not os.path.exists(file_path):
                continue

            if args.keep_inst:
                # Instrumented -> Original
                # but keep the instrumented file with the suffix `INSTRUMENT_SUFFIX`
                if file_path.endswith(DYNAPYT_JSON_SUFFIX):
                    os.rename(file_path, file_path.replace(DYNAPYT_JSON_SUFFIX, DYNAPYT_JSON_BACKUP_SUFFIX))
                    continue

                if not file_path.endswith(PY_SUFFIX):
                    continue

                orig_file = file_path + ORIGINAL_SUFFIX

                if os.path.exists(orig_file):
                    os.rename(file_path, file_path + INSTRUMENT_SUFFIX)
                    os.rename(orig_file, file_path)

                continue

            if args.restore_inst:
                # Original -> Instrumented
                # using the instrumented file with the suffix `INSTRUMENT_SUFFIX`
                if file_path.endswith(DYNAPYT_JSON_BACKUP_SUFFIX):
                    os.rename(file_path, file_path.replace(DYNAPYT_JSON_BACKUP_SUFFIX, DYNAPYT_JSON_SUFFIX))
                    continue

                if not file_path.endswith(PY_SUFFIX):
                    continue

                inst_file = file_path + INSTRUMENT_SUFFIX

                if os.path.exists(inst_file):
                    os.rename(file_path, file_path + ORIGINAL_SUFFIX)
                    os.rename(inst_file, file_path)

                continue

            # Instrumented -> original
            # and remove the instrumented file
            if file_path.endswith(DYNAPYT_JSON_SUFFIX):
                os.remove(os.path.join(curr_path, file_path))
                continue

            if not file_path.endswith(PY_SUFFIX):
                continue

            orig_file = file_path + ORIGINAL_SUFFIX

            if os.path.exists(file_path) and os.path.exists(orig_file):
                # Remove Python file with instrumentation
                os.remove(file_path)
                # Restore original Python file
                os.rename(orig_file, file_path)

if __name__ == '__main__':
    main()
