# -*- coding: utf-8 -*-
import os
from typing import Optional, List
import pickle

LOG_BASE = "/Users/keita/projects/DynaPyt/logs/"
GENERATED_TEST_BASE = "/Users/keita/projects/DynaPyt/post-processing/generated-tests"
META_FILE_SUFFIX = "_META.txt"
CALL_FILE_SUFFIX = "_CALL.pickle"
RETURN_FILE_SUFFIX = "_RETURN.pickle"

INDT = "    "

FUNC_VAR_NAME = "module"
POS_ARG_VAR_NAME = "pos_args"
KW_ARG_VAR_NAME = "kw_args"

RET_VAR_NAME = "ret"
EXPECTED_RET_VAR_NAME = "expected"

preload_modules = ["pickle"]

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

    def get_log_dir_name(self) -> str:
        return os.path.basename(os.path.dirname(self.path))

    @classmethod
    def is_meta_file(cls, path: str) -> bool:
        return os.path.isfile(path) and path.endswith(META_FILE_SUFFIX)

def get_pos_arg_assign_code(pos_arg_len: int) -> Optional[str]:
    if not pos_arg_len:
        return None

    pos_arg_var_names = [f"pos_arg_{i.zfill(2)}" for i in range(pos_arg_len)]

    ret = ", ".join(pos_arg_var_names)
    ret += " = " + POS_ARG_VAR_NAME
    return ret

def get_pos_arg_for_func_code(pos_arg_len: int) -> Optional[str]:
    if not pos_arg_len:
        return None

    pos_arg_var_names = [f"pos_arg_{i.zfill(2)}" for i in range(pos_arg_len)]
    return ", ".join(pos_arg_var_names)

def get_kw_arg_for_func_code(kw_args: dict) -> Optional[str]:
    if not len(kw_args):
        return None

    # ["a=kw_args['a']", "b=kw_arg['b']", ..., "z=kw_args['z']""]
    kw_arg_list = []
    for key in kw_args.keys():
        kw_arg_list.append(f"{key}={POS_ARG_VAR_NAME}['{key}']")
    return ", ".join(kw_arg_list)

def get_load_call_pickle_code(path: str) -> str:
    return (f'with open("{path}", "rb") as f:\n'
            + f"{INDT}{FUNC_VAR_NAME}, {POS_ARG_VAR_NAME}, {KW_ARG_VAR_NAME} = pickle.load(f)")

def get_load_return_pickle_code(path: str) -> str:
    return (f'with open("{path}", "rb") as f:\n'
            + f"{INDT}{EXPECTED_RET_VAR_NAME} = pickle.load(f)")

def generate_test_case(meta_file: MetaData) -> Optional[str]:
    """
    Note: It only supports pos_args now!
    """
    if not os.path.isfile(meta_file.call_pickle_path):
        print(f"Call pickle file not found: {meta_file.call_pickle_path}")
        return None

    if not os.path.isfile(meta_file.return_pickle_path):
        print(f"Return pickle file not found: {meta_file.return_pickle_path}")
        return None

    ret = ""

    ret += meta_file.module_import_path + "\n\n"

    with open(meta_file.call_pickle_path, 'rb') as f:
        module, pos_args, kw_args = pickle.load(f)

    pos_arg_len = len(pos_args)
    kw_arg_len = len(kw_args)

    ret += get_load_call_pickle_code(meta_file.call_pickle_path) + "\n"

    pos_arg_assign_code = get_pos_arg_assign_code(pos_arg_len)
    if pos_arg_assign_code:
        ret += pos_arg_assign_code + "\n"

    ret += f"{RET_VAR_NAME} = {meta_file.module_name}("

    # Function args are here
    pos_arg_for_func = get_pos_arg_for_func_code(len(pos_args))
    if pos_arg_for_func:
        ret += pos_arg_for_func + "\n"

    kw_arg_for_func = get_kw_arg_for_func_code(kw_args)
    if kw_arg_for_func:
        if pos_arg_for_func:
            ret += ", "

        ret += kw_arg_for_func + "\n"
    # Function args are here
    ret += ")\n"

    ret += get_load_return_pickle_code(meta_file.return_pickle_path) + "\n"
    ret += f"assert {RET_VAR_NAME} == {EXPECTED_RET_VAR_NAME}\n"

    return ret

def get_test_file_path(meta_file: MetaData) -> str:
    ret = os.path.join(GENERATED_TEST_BASE, meta_file.get_log_dir_name())
    return os.path.join(ret, meta_file.get_test_case_name() + ".py")

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

    for i, meta_file in enumerate(meta_files):
        py_content = ""
        for preload_module in preload_modules:
            # print(f"import {preload_module}")
            py_content += f"import {preload_module}\n"

        # print()
        py_content += "\n"

        # print(generate_test_case(meta_files[0]))
        py_content += generate_test_case(meta_files[0])

        print(get_test_file_path(meta_file))
        # test_file_path = os.path.join(GENERATED_TEST_BASE, meta_file meta_file.get_test_case_name() + ".py")
        # os.makedirs(, exist_ok=True)
        # print(meta_file.get_log_dir_name())
        # try:
        #     exec(py_content)
        #     print("SUCCESS")
        #     print(py_content)
        # except:
        #     print("FAILED")

        if i > 3:
            break


if __name__ == '__main__':
    main()
