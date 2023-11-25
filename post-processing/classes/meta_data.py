import os
from typing import Optional
META_FILE_SUFFIX = "_META.txt"

NOT_CLASS_METHOD_NAME = "NOT_A_CLASS_METHOD"

class MetaData:

    def __init__(self, path):
        assert MetaData.is_meta_file(path), f"{path} is not a meta file."

        # Assuming it's a meta file
        self.path = path
        self.file_name = os.path.basename(path)

        with open(path) as f:
            lines = f.readlines()

        self.module_name: str = lines[0].strip()
        self.class_name: Optional[str] = lines[1].strip()
        self.module_import_path = lines[2].strip()
        self.call_pickle_path = lines[3].strip()
        self.return_pickle_path = lines[4].strip()

        if self.class_name == NOT_CLASS_METHOD_NAME:
            self.class_name = None

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

    def get_log_dir_name(self) -> str:
        return os.path.basename(os.path.dirname(self.path))

    @classmethod
    def is_meta_file(cls, path: str) -> bool:
        return os.path.isfile(path) and path.endswith(META_FILE_SUFFIX)
