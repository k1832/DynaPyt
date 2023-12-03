import os, logging
import subprocess
from typing import List, Optional
from classes.meta_data import MetaData

from multiprocessing import Process, Manager
from concurrent.futures import Future, ProcessPoolExecutor

from tqdm import tqdm
import argparse

logging.basicConfig(level=logging.INFO)

TEST_BASE = "/Users/keita/projects/DynaPyt/post-processing/generated-tests"
LOG_BASE = "/Users/keita/projects/DynaPyt/logs/"
TEST_STATS_FAILURE_FILE = "/Users/keita/projects/DynaPyt/post-processing/test-run-stats/failure.txt"
TEST_STATS_SUCCESS_FILE = "/Users/keita/projects/DynaPyt/post-processing/test-run-stats/success.txt"
PARALLEL_COUNT = 8
SAMPLE_RATE = 1

META_FILE_SUFFIX = "_META.txt"

def run_test(path: str,
             coverage: bool = False,
             rcfile: Optional[str] = None,
             datafile: Optional[str] = None,
             append: bool = False,
             parallel: bool = False,
             progress_bar: tqdm = None) -> int:
    """
    Run python script at `path` and returns its return code.
    """

    if coverage:
        # Only when both are specified
        cmd = ["coverage", "run"]

        if parallel:
            if append:
                print("Append is ignored when parallel is specified")
            cmd.append("-p")
        else:
            if append:
                cmd.append("-a")

        if datafile:
            cmd.append(f"--data-file={datafile}")
        if rcfile:
            cmd.append(f"--rcfile={rcfile}")
        if parallel:
            cmd.append("-p")

        cmd.append(path)
    else:
        cmd = ["python", path]


    msg = f"Running: {' '.join(cmd)}"
    if progress_bar:
        # progress_bar.set_description(msg)
        pass
    else:
        print(msg)
    child = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    _ = child.communicate()[0]
    return child.returncode

def run_test_multiprocess(path: str, module_name: str, success_log: List[str], failed_log: List[str]):
    try:
        result = subprocess.run(["python", path], shell=True, check=True, stderr=subprocess.PIPE, text=True)
        if result.returncode:
            failed_log.append(f"FAILED:{path} {module_name}\n{result.stderr}\n")
        else:
            success_log.append(f"{path} {module_name}")
    except subprocess.CalledProcessError as e:
        failed_log.append(f"FAILED:{path} {module_name}\n{e.stderr}\n")

def run_test_concurrent_item(path: str) -> bool:
    try:
        result = subprocess.run(["python", path])
        if result.returncode:
            return False
        else:
            return True
    except subprocess.CalledProcessError as e:
        return False

def run_test_coverage_concurrent_item(path: str, rcfile_path: Optional[str] = None) -> bool:
    cmd = ["coverage", "run", "-p"]

    if rcfile_path:
        cmd.append(f"--rcfile={rcfile_path}")

    cmd.append(path)

    try:
        result = subprocess.run(cmd)
        if result.returncode:
            return False
        else:
            return True
    except subprocess.CalledProcessError as e:
        return False


# print(run_test("/Users/keita/projects/DynaPyt/post-processing/generated-tests/20231030_224445_112/test_00000_00021.py"))
# print(run_test("/Users/keita/projects/DynaPyt/post-processing/generated-tests/20231030_224445_112/test_00002_00018.py"))

def get_meta_file_path_from_test_path(test_path: str) -> str:
    dir_name = os.path.basename(os.path.dirname(test_path))
    test_file_name_wo_ex = os.path.basename(test_path).replace(".py", "")

    meta_file_prefix = "_".join(test_file_name_wo_ex.split("_")[1:3])
    meta_file_name = meta_file_prefix + "_META.txt"

    return os.path.join(LOG_BASE, dir_name, meta_file_name)

def run_test_concurrent(test_case_file_paths: List[str], coverage: bool = False, rcfile: Optional[str] = None):
    with ProcessPoolExecutor(max_workers=PARALLEL_COUNT) as executor:

        processes: list[tuple[Future[any], str, str]] = []
        success_count = 0
        handle_from = 0
        for test_case_file_path in tqdm(test_case_file_paths):
            meta_file_path = get_meta_file_path_from_test_path(test_case_file_path)
            meta_data = MetaData(meta_file_path)
            module_name = meta_data.module_name

            # Run a test case, ignore stdout, stderr, but get return code
            # process = Process(target=run_test_multiprocess, args=(test_case_file_path, module_name, success_log, failed_log))
            # process.start()
            # processes.append(proces)

            if coverage:
                process = executor.submit(run_test_coverage_concurrent_item, test_case_file_path, rcfile)
                processes.append((process, test_case_file_path, module_name))

                if len(processes) - handle_from >= PARALLEL_COUNT:
                    for process, processed_file_path, _ in processes[handle_from:]:
                        if not process.result():
                            logging.error(f"Failed to run {processed_file_path}")

                    handle_from = len(processes)

                continue

            # not coverage
            process = executor.submit(run_test_concurrent_item, test_case_file_path)
            processes.append((process, test_case_file_path, module_name))

            if len(processes) - handle_from >= PARALLEL_COUNT:
                for process, processed_file_path, processed_module_name in processes[handle_from:]:
                    if process.result():
                        success_count += 1
                        with open(TEST_STATS_SUCCESS_FILE, "a") as f:
                            f.write(f"{processed_file_path} {processed_module_name}\n")
                    else:
                        with open(TEST_STATS_FAILURE_FILE, "a") as f:
                            f.write(f"{processed_file_path} {processed_module_name}\n")

                handle_from = len(processes)

        # Handle the rest

        if coverage:
            if len(processes) > handle_from:
                    for process, processed_file_path, _ in processes[handle_from:]:
                        if not process.result():
                            logging.error(f"Failed to run {processed_file_path}")

                    handle_from = len(processes)
            return

        # not coverage
        if len(processes) > handle_from:
            for process, processed_file_path, processed_module_name in processes[handle_from:]:
                if process.result():
                    success_count += 1
                    with open(TEST_STATS_SUCCESS_FILE, "a") as f:
                        f.write(f"{processed_file_path} {processed_module_name}\n")
                else:
                    with open(TEST_STATS_FAILURE_FILE, "a") as f:
                        f.write(f"{processed_file_path} {processed_module_name}\n")

            handle_from = len(processes)

        print(f"Total run: {handle_from}, Success: {success_count}, Failure: {handle_from - success_count}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--coverage", action="store_true", help="run only successful tests and collect coverage data")
    parser.add_argument("-rc", "--rcfile", type=str, help="rcfile for coverage")
    parser.add_argument("-df", "--datafile", type=str, help="datafile for coverage")
    parser.add_argument("-a", "--append", action="store_true", help="append coverage data")
    parser.add_argument("-p", "--parallel", action="store_true", help="store coverage data with unique name")
    parser.add_argument("--concurrent-coverage", action="store_true", help="run coverage in parallel")
    args = parser.parse_args()

    if args.coverage and args.concurrent_coverage:
        logging.error(f"Cannot specify both --coverage and --concurrent-coverage")
        exit()

    if args.coverage:
        try:
            with open(TEST_STATS_SUCCESS_FILE, "r") as f:
                success_tests = f.readlines()
        except:
            print("No success tests found")
            exit()

        if not len(success_tests):
            print("No success tests found")
            exit()

        progress_bar = tqdm(range(len(success_tests)))

        if args.concurrent:

            return

        for i in progress_bar:
            success_test = success_tests[i]
            file_path, _ = success_test.split()

            rcfile = args.rcfile if args.rcfile else None
            datafile = args.datafile if args.datafile else None
            append = args.append
            parallel = args.parallel
            assert run_test(file_path,
                            coverage=True,
                            rcfile=rcfile,
                            datafile=datafile,
                            append=(i>0 or append),
                            parallel=parallel,
                            progress_bar=progress_bar) == 0

        exit()

    if args.concurrent_coverage:
        print("Running coverage in parallel...")

        try:
            with open(TEST_STATS_SUCCESS_FILE, "r") as f:
                success_tests = f.readlines()
        except:
            print("No success tests found")
            exit()

        if not len(success_tests):
            print("No success tests found")
            exit()

        test_case_file_paths = []
        for success_test in success_tests:
            file_path, _ = success_test.split()
            test_case_file_paths.append(file_path)

        rcfile = args.rcfile if args.rcfile else None
        run_test_concurrent(test_case_file_paths, coverage=True, rcfile=rcfile)

        exit()

    # Create test case list first
    test_case_total_count = 0
    test_case_file_paths = []
    for test_case_dir in os.listdir(TEST_BASE):
        test_case_dir_path = os.path.join(TEST_BASE, test_case_dir)
        test_case_log_path = os.path.join(test_case_dir_path, "log.txt")

        for test_case_file_name in os.listdir(test_case_dir_path):
            test_case_file_path = os.path.join(test_case_dir_path, test_case_file_name)
            if not os.path.isfile(test_case_file_path):
                continue

            if test_case_file_path == test_case_log_path:
                continue

            test_case_total_count += 1
            if test_case_total_count % SAMPLE_RATE:
                continue

            test_case_file_paths.append(test_case_file_path)

    print(f"Total test case count: {test_case_total_count}")
    print(f"Sampled test case count: {len(test_case_file_paths)}")
    print(f"Sample rate: 1/{SAMPLE_RATE}")

    # Multiprocess
    # with Manager() as manager:
        # success_log: List[str] = manager.list()
        # failed_log: List[str] = manager.list()




        # print(f"Total Commands: {len(success_log) + len(failed_log)}, Successes: {len(success_log)}, Failures: {len(failed_log)}")

        # with open(TEST_STATS_SUCCESS_FILE, "w") as f:
        #     f.write("\n".join(success_log))
        # with open(TEST_STATS_FAILURE_FILE, "w") as f:
        #     f.write("\n".join(failed_log))

    run_test_concurrent(test_case_file_paths)

    exit()


    # Single process
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
