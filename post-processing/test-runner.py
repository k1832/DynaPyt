import os
import subprocess
from typing import Optional
from classes.meta_data import MetaData

import argparse

TEST_BASE = "/Users/keita/projects/DynaPyt/post-processing/generated-tests"
LOG_BASE = "/Users/keita/projects/DynaPyt/logs/"
TEST_STATS_FAILURE_FILE = "/Users/keita/projects/DynaPyt/post-processing/test-run-stats/failure.txt"
TEST_STATS_SUCCESS_FILE = "/Users/keita/projects/DynaPyt/post-processing/test-run-stats/success.txt"

META_FILE_SUFFIX = "_META.txt"

def run_test(path: str, rcfile: Optional[str] = None, datafile: Optional[str] = None, append: bool = False) -> int:
    """
    Run python script at `path` and returns its return code.
    """

    if rcfile is not None or datafile is not None:
        # Only when both are specified
        cmd = ["coverage", "run"]
        if append:
            cmd.append("-a")
        if datafile is not None:
            cmd.append(f"--data-file={datafile}")
        if rcfile is not None:
            cmd.append(f"--rcfile={rcfile}")
        cmd.append(path)
    else:
        cmd = ["python", path]

    print(f"Running: {' '.join(cmd)}")
    child = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    _ = child.communicate()[0]
    return child.returncode

# print(run_test("/Users/keita/projects/DynaPyt/post-processing/generated-tests/20231030_224445_112/test_00000_00021.py"))
# print(run_test("/Users/keita/projects/DynaPyt/post-processing/generated-tests/20231030_224445_112/test_00002_00018.py"))

def get_meta_file_path_from_test_path(test_path: str) -> str:
    dir_name = os.path.basename(os.path.dirname(test_path))
    test_file_name_wo_ex = os.path.basename(test_path).replace(".py", "")

    meta_file_prefix = "_".join(test_file_name_wo_ex.split("_")[1:3])
    meta_file_name = meta_file_prefix + "_META.txt"

    return os.path.join(LOG_BASE, dir_name, meta_file_name)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--success-only", action="store_true", help="Only run succeeded tests")
    parser.add_argument("-rc", "--rcfile", type=str, help="rcfile for coverage")
    parser.add_argument("-df", "--datafile", type=str, help="datafile for coverage")
    parser.add_argument("-a", "--append", action="store_true", help="append coverage data")
    args = parser.parse_args()

    if args.success_only:
        with open(TEST_STATS_SUCCESS_FILE, "r") as f:
            success_tests = f.readlines()

        for i, success_test in enumerate(success_tests):
            file_path, _ = success_test.split()

            rcfile = args.rcfile if args.rcfile else None
            datafile = args.datafile if args.datafile else None
            append = args.append
            assert run_test(file_path, rcfile=rcfile, datafile=datafile, append=(i>0 or append)) == 0

        exit()

    success_module_count = {}
    failure_module_count = {}
    for test_case_dir_i, test_case_dir in enumerate(os.listdir(TEST_BASE)):
        test_case_dir_path = os.path.join(TEST_BASE, test_case_dir)
        test_case_log_path = os.path.join(test_case_dir_path, "log.txt")

        for test_case_file_name in os.listdir(test_case_dir_path):
            test_case_file_path = os.path.join(test_case_dir_path, test_case_file_name)
            if not os.path.isfile(test_case_file_path):
                continue

            if test_case_file_path == test_case_log_path:
                continue


            meta_file_path = get_meta_file_path_from_test_path(test_case_file_path)
            meta_data = MetaData(meta_file_path)
            module_name = meta_data.module_name
            try:
                rt_code = run_test(test_case_file_path)
                if rt_code:
                    raise Exception(f"Return code: {rt_code}")

                with open(test_case_log_path, "a") as f:
                    f.write(f"{test_case_file_path}\n")

                if module_name not in success_module_count:
                    success_module_count[module_name] = 0

                success_module_count[module_name] += 1
                with open(TEST_STATS_SUCCESS_FILE, "a") as f:
                    f.write(f"{test_case_file_path} {module_name}\n")
            except KeyboardInterrupt:
                print("KeyboardInterrupt")
                exit()
            except Exception:
                print("Running test failed")
                module_name = meta_data.module_name
                if module_name not in failure_module_count:
                    failure_module_count[module_name] = 0

                failure_module_count[module_name] += 1
                with open(TEST_STATS_FAILURE_FILE, "a") as f:
                    f.write(f"{test_case_file_path} {module_name}\n")

        # Only 5 folder for now
        # if test_case_dir_i > 10:
        #     break

    print("SUCCESS MODULE COUNT")
    print(success_module_count)
    print()
    print("FAILURE MODULE COUNT")
    print(failure_module_count)

if __name__ == '__main__':
    main()
