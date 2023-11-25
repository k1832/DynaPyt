# -*- coding: utf-8 -*-
import os, logging
import tqdm
from typing import Optional, List
import pickle
from classes.meta_data import MetaData

logging.basicConfig(level=logging.INFO)

LOG_BASE = "/Users/keita/projects/DynaPyt/logs/"
GENERATED_TEST_BASE = "/Users/keita/projects/DynaPyt/post-processing/generated-tests"
CALL_FILE_SUFFIX = "_CALL.pickle"
RETURN_FILE_SUFFIX = "_RETURN.pickle"

INDT = "    "

FUNC_VAR_NAME = "module"
POS_ARG_VAR_NAME = "pos_args"
KW_ARG_VAR_NAME = "kw_args"

RET_VAR_NAME = "ret"
EXPECTED_RET_VAR_NAME = "expected"

preload_modules = ["pickle"]


def get_pos_arg_assign_code(pos_arg_len: int) -> Optional[str]:
    if not pos_arg_len:
        return None

    pos_arg_var_names = [f"pos_arg_{str(i).zfill(2)}" for i in range(pos_arg_len)]

    if pos_arg_len == 1:
        # To prevent this: pos_args: ('/Resource',) -> pos_arg_00: ('/Resource',)
        return f"{pos_arg_var_names[0]} = {POS_ARG_VAR_NAME}[0]"

    ret = ", ".join(pos_arg_var_names)
    ret += f" = {POS_ARG_VAR_NAME}"

    return ret

def get_pos_arg_for_func_code(pos_arg_len: int) -> Optional[str]:
    if not pos_arg_len:
        return None

    pos_arg_var_names = [f"pos_arg_{str(i).zfill(2)}" for i in range(pos_arg_len)]
    return ", ".join(pos_arg_var_names)

def get_kw_arg_for_func_code(kw_args: dict) -> Optional[str]:
    if not len(kw_args):
        return None

    # ["a=kw_args['a']", "b=kw_arg['b']", ..., "z=kw_args['z']""]
    kw_arg_list = []
    for key in kw_args.keys():
        kw_arg_list.append(f"{key}={KW_ARG_VAR_NAME}['{key}']")
    return ", ".join(kw_arg_list)

def is_class_instance(a) -> bool:
    # TODO(k1832): Revisit if this really works
    try:
        return a.__class__.__module__ != 'builtins'
    except:
        return False

def is_eq_implemented(a) -> bool:
    assert is_class_instance(a)
    try:
        return a.__class__.__eq__ is not object.__eq__
    except:
        raise Exception("Checking __eq__ failed")

def comparable_object(a) -> bool:
    if is_class_instance(a):
        return is_eq_implemented(a)

    return True

def get_load_call_pickle_code(path: str, need_pos: bool, need_kw: bool) -> str:
    # return (f'with open("{path}", "rb") as f:\n'
    #         + f"{INDT}{FUNC_VAR_NAME}, {POS_ARG_VAR_NAME}, {KW_ARG_VAR_NAME} = pickle.load(f)")

    pos_arg_var_name = POS_ARG_VAR_NAME if need_pos else "_"
    kw_arg_var_name = KW_ARG_VAR_NAME if need_kw else "_"

    return (f'with open("{path}", "rb") as f:\n'
            + f"{INDT}{pos_arg_var_name}, {kw_arg_var_name} = pickle.load(f)")

def get_load_return_pickle_code(path: str) -> str:
    return (f'with open("{path}", "rb") as f:\n'
            + f"{INDT}{EXPECTED_RET_VAR_NAME} = pickle.load(f)")

def generate_test_case(meta_file: MetaData, ignore_no_arg_calls: bool = True) -> Optional[str]:
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

    try:
        with open(meta_file.call_pickle_path, 'rb') as f:
            pos_args, kw_args = pickle.load(f)
    except EOFError:
        logging.debug("Empty args pickle file")
        return None
    except Exception as e:
        # Unknown error
        logging.error(e)
        return None

    # TODO(k1832): Investigate why this causes duplication of a log directory
    try:
        with open(meta_file.return_pickle_path, 'rb') as f:
            ret_value = pickle.load(f)
    except EOFError:
        logging.debug("Empty return pickle file")
        return None
    except Exception as e:
        # Unknown error
        logging.error(e)
        return None

    # TODO(k1832): Revisit if ignoring calls with None as return value is a good idea
    if ret_value is None:
        return None


    pos_arg_len = len(pos_args)
    kw_arg_len = len(kw_args)

    if ignore_no_arg_calls and not pos_arg_len and not kw_arg_len:
        logging.debug("No arguments")
        return None

    ret += get_load_call_pickle_code(meta_file.call_pickle_path, pos_arg_len, kw_arg_len) + "\n"
    ret += get_load_return_pickle_code(meta_file.return_pickle_path) + "\n"

    ret += "\n"

    ret += "# Make sure the function returns something\n"
    ret += f"assert {EXPECTED_RET_VAR_NAME} is not None\n"

    ret += "\n"

    pos_arg_assign_code = get_pos_arg_assign_code(pos_arg_len)
    if pos_arg_assign_code:
        ret += pos_arg_assign_code + "\n"

    ret += f"{RET_VAR_NAME} = {meta_file.module_name}("

    # Function args are here
    pos_arg_for_func = get_pos_arg_for_func_code(len(pos_args))
    if pos_arg_for_func:
        ret += pos_arg_for_func

    kw_arg_for_func = get_kw_arg_for_func_code(kw_args)
    if kw_arg_for_func:
        if pos_arg_for_func:
            ret += ", "

        ret += kw_arg_for_func
    # Function args are here
    ret += ")\n"

    ret += "\n"

    """
    Special handling for return values that are class instances.

    If `__eq__` is explicitly implemented (not inherited default), the expected value and the actual value are simply compared with `==`.
    Otherwise, check if have the same type, and compare them using `vars()` (i.e. `vars(expected) == vars(actual)`).
    """

    if comparable_object(ret_value):
        return ret + f"assert {RET_VAR_NAME} == {EXPECTED_RET_VAR_NAME}\n"

    ret += f"assert type({RET_VAR_NAME}) == type({EXPECTED_RET_VAR_NAME})\n"
    ret += f"assert vars({RET_VAR_NAME}) == vars({EXPECTED_RET_VAR_NAME})\n"
    return ret

def get_test_file_path(meta_file: MetaData) -> str:
    ret = os.path.join(GENERATED_TEST_BASE, meta_file.get_log_dir_name())
    return os.path.join(ret, meta_file.get_test_case_name() + ".py")

def main():
    meta_files: List[MetaData] = []

    for log_dir_name in tqdm.tqdm(os.listdir(LOG_BASE)):
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
        test_code = ""
        for preload_module in preload_modules:
            # print(f"import {preload_module}")
            test_code += f"import {preload_module}\n"

        # print()
        test_code += "\n"

        # print(generate_test_case(meta_files[0]))

        # TODO(k1832): Function calls with no arguments should be excluded
        test_case_code = generate_test_case(meta_file)
        if test_case_code is None:
            print(f"Failed to create a test for {meta_file.path}")
            continue

        test_code += test_case_code + "\n"

        test_file_path = get_test_file_path(meta_file)
        print(f"Test file path: {test_file_path}")
        # print(test_code)
        os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
        with open(test_file_path, "w") as f:
            f.write(test_code)

        # print(meta_file.get_log_dir_name())
        # try:
        #     exec(py_content)
        #     print("SUCCESS")
        #     print(py_content)
        # except:
        #     print("FAILED")

        # if i > 3:
        #     break


if __name__ == '__main__':
    main()
