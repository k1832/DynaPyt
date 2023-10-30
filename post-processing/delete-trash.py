"""
Removes "trash" directories in `logs/`.
"Trash" directories are directories that don't have
any files other than "error.txt"
"""

import os
import shutil

LOG_BASE = "/Users/keita/projects/DynaPyt/logs"

def main():
    delete_count = 0

    for log_dir_name in os.listdir(LOG_BASE):
        log_dir_path = os.path.join(LOG_BASE, log_dir_name)
        if not os.path.isdir(log_dir_path):
            continue

        file_names = os.listdir(log_dir_path)
        if not len(file_names):
            delete_count += 1
            shutil.rmtree(log_dir_path, ignore_errors=True)
            continue

        if len(file_names) > 1:
            continue

        # len(file_names) == 1
        if file_names[0] == "error.txt":
            delete_count += 1
            shutil.rmtree(log_dir_path, ignore_errors=True)
            continue

    print(f"Deleted {delete_count} directories.")

if __name__ == '__main__':
    main()
