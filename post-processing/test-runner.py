import os
import subprocess

TEST_DIR = "/Users/keita/projects/DynaPyt/post-processing/generated-tests/20231030_224445_112"

def run_test(path: str) -> int:
    """
    Run python script at `path` and returns its return code.
    """
    child = subprocess.Popen(["python", path], stdout=subprocess.PIPE)
    _ = child.communicate()[0]
    return child.returncode

# print(run_test("/Users/keita/projects/DynaPyt/post-processing/generated-tests/20231030_224445_112/test_00000_00021.py"))
# print(run_test("/Users/keita/projects/DynaPyt/post-processing/generated-tests/20231030_224445_112/test_00002_00018.py"))

def main():
    log_file_path = os.path.join(TEST_DIR, "log.txt")

    for file_name in os.listdir(TEST_DIR):
        file_path = os.path.join(TEST_DIR, file_name)
        if not os.path.isfile(file_path):
            continue

        try:
            rt_code = run_test(file_path)
            if rt_code:
                continue


            with open(log_file_path, "a") as f:
                f.write(f"{file_path}\n")
        except:
            print("Running test threw an exception.")

if __name__ == '__main__':
    main()
