# -*- coding: utf-8 -*-
import os
from typing import Optional

LOG_BASE = "/Users/keita/projects/DynaPyt/logs/"
META_FILE_SUFFIX = "_META.txt"
CALL_FILE_SUFFIX = "_CALL.pickle"
RETURN_FILE_SUFFIX = "_RETURN.pickle"

class MetaData:

    def __init__(self, path):
        assert MetaData.is_meta_file(path), f"{path} is not a meta file."

        # Assuming it's a meta file
        self.path = path
        self.file_name = os.path.basename(path)

        with open(path) as f:
            lines = f.readlines()

        self.module_name = lines[0].strip()
        self.module_import_path = lines[1].strip()
        self.call_pickle_path = lines[2].strip()
        self.return_pickle_path = lines[3].strip()

    def debug_print(self) -> None:
        print(self.module_name)
        print(self.module_import_path)
        print(self.call_pickle_path)
        print(self.return_pickle_path)

    def get_test_case_name(self) -> str:
        """
        Example:
            self.file_name: "00001_00021_META.txt"
        Returns:
            "test_00001_00021"
        """
        return "test_" + "_".join(self.file_name.split("_")[:2])


    @classmethod
    def is_meta_file(cls, path: str) -> bool:
        return os.path.isfile(path) and path.endswith(META_FILE_SUFFIX)

def generate_test_case(meta_file: MetaData) -> Optional[str]:
    """
    Note: It only supports pos_args now!
    """


def main():
    meta_files = []

    for log_dir_name in os.listdir(LOG_BASE):
        log_dir_path = os.path.join(LOG_BASE, log_dir_name)
        if not os.path.isdir(log_dir_path):
            continue

        for log_file_name in os.listdir(log_dir_path):
            log_file_path = os.path.join(log_dir_path, log_file_name)
            if MetaData.is_meta_file(log_file_path):
                meta_files.append(MetaData(log_file_path))


    if not len(meta_files):
        print("No log files")
        exit()

    meta_files[0].debug_print()
    print()
    meta_files[1].debug_print()


if __name__ == '__main__':
    main()
