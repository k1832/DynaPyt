# try-except version
import os, sys
from datetime import datetime
import pickle
from typing import Any, Callable, Dict, Optional, Tuple
from .BaseAnalysis import BaseAnalysis

import inspect

# To prevent stack overflow
sys.setrecursionlimit(10000000)

LOG_BASE = "/Users/keita/projects/DynaPyt/logs"

# TARGET_MODULE_PATH = "/projects/casanova/casanova"
TARGET_MODULE_PATH = "/Users/keita/projects/flair/flair"
# TARGET_MODULE_PATH = "/Users/keita/projects/pdfrw/pdfrw"

# HACK(k1832): These 2 are to make the tests of pdfrw pass...
IS_PDFRW = "pdfrw" in TARGET_MODULE_PATH
LIMIT_BY_FILE_IID = 20 if IS_PDFRW else 1000

NOT_CLASS_METHOD_NAME = "NOT_A_CLASS_METHOD"

TMP_TXT = "/Users/keita/projects/pdfrw/tmp.txt"


def write_tmp_log(s):
    with open(TMP_TXT, 'a') as f:
        f.write(s)

def is_target_module(module: Callable, target_module_path: Optional[str]) -> bool:
    if not target_module_path:
        return False

    parent = inspect.getmodule(module)
    try:
        parent_file_path = parent.__file__
    except:
        return False

    return target_module_path in parent_file_path

def get_import_path(module: Callable) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Returns 3 values:
        - module name
        - class name if it's class/instance method, otherwise None
        - import path of the module or class,
    If it fails to resolve the module import path, the import path is None.

    Example:
        >>> get_import_path(getmodule)
        "getmodule", None, "from inspect import getmodule"
        >>> get_import_path(accumulate)
        "accumulate", None, "from itertools import accumulate"
    """

    """
    if inspect.ismethod(module):
        try:
            class_name = module.__self__.__name__
            # It's a class method
        except:
            # It's an instance method (i.e. methods in a class without @classmethod)
    else:
        qualname = module.__qualname__
        if "." in qualname:
            # It's a (probably) static method
        else:
            # It's a normal function
    """

    try:
        module_name = module.__name__
    except:
        return (None,
                None,
                None)

    class_name = None
    if inspect.ismethod(module):
        try:
            class_obj = module.__self__
        except:
            # TODO(k1832): Revisit if skipping instance method is a good idea
            # TODO(k1832): Revisit if it's sufficient to conclude it's instance method
            # Exclude instance methods (i.e. methods in a class without @classmethod)
            return (module_name,
                    None,
                    None)

        if not inspect.isclass(class_obj):
            # TODO(k1832): Revisit if skipping instance method is a good idea
            # TODO(k1832): Revisit if it's sufficient to conclude it's instance method
            # Exclude instance methods (i.e. methods in a class without @classmethod)
            return (module_name,
                    None,
                    None)

        try:
            class_name = class_obj.__name__
        except:
            # TODO(k1832): Revisit if skipping instance method is a good idea
            # TODO(k1832): Revisit if it's sufficient to conclude it's instance method
            # Exclude instance methods (i.e. methods in a class without @classmethod)
            return (module_name,
                    None,
                    None)
    else:
        try:
            qualname = module.__qualname__
        except:
            return (module_name,
                    None,
                    None)

        if isinstance(qualname, str):
            period_split = qualname.split(".")
        else:
            return (module_name,
                    None,
                    None)

        if len(period_split) == 1:
            pass
        elif len(period_split) == 2:
            class_name = period_split[0]
        else:
            # Now it can only handle {Class name}.{static method name}
            # logging.warning(f"qualname: {qualname} not supported")
            return (module_name,
                    None,
                    None)

    parent_module = inspect.getmodule(module)

    # This cannot be done by simply comparing 2 names
    # Example: from datetime import datetime
    if parent_module == module:
        return (module_name,
                class_name,
                f"import {class_name if class_name else module_name}")

    try:
        parent_module_name = parent_module.__name__
    except:
        return (module_name,
                class_name,
                None)

    return (module_name,
            class_name,
            f"from {parent_module_name} import {class_name if class_name else module_name}")

class MyCallGraph(BaseAnalysis):

    def __init__(self) -> None:
        super().__init__()
        self.running_time = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

        self.count = 0

        # self.count_by_file_iid[filename][iid] = count
        self.count_by_file_iid: dict[str, dict[int, int]] = {}


        self.log_dir = os.path.join(LOG_BASE, self.running_time)
        self.error_file_path = os.path.join(self.log_dir, "error.txt")


    def post_call(
        self,
        dyn_ast: str,
        iid: int,
        result: Any,
        function: Callable,
        pos_args: Tuple,
        kw_args: Dict,
    ) -> Any:
        """Hook called after a function call.


        Parameters
        ----------
        dyn_ast : str
            The path to the original code. Can be used to extract the syntax tree.

        iid : int
            Unique ID of the syntax tree node.

        val : Any
            The return value of the function.

        call: Callable
            The function which was called.

        pos_args : Tuple
            The positional arguments passed to the function.

        kw_args : Dict
            The keyword arguments passed to the function.


        Returns
        -------
        Any
            If provided, overwrites the returned value.

        """

        """
        Pair a corresponding call with the return.
        If there is a corresponding call,
        save following.
        - pos_args, kw_args as a pickle file
        - return value (result) as a pickle file
        - module info (name, path, etc.), and corresponding pickle files as a text file
        """

        if not is_target_module(function, TARGET_MODULE_PATH):
            return

        if dyn_ast not in self.count_by_file_iid:
            self.count_by_file_iid[dyn_ast] = {}

        if iid not in self.count_by_file_iid[dyn_ast]:
            self.count_by_file_iid[dyn_ast][iid] = 0

        # TODO(k1832): Consider moving this after saving pickle files
        # Doing that will make some tests fail now...
        if self.count_by_file_iid[dyn_ast][iid] > LIMIT_BY_FILE_IID:
            return

        function_name, class_name, import_path = get_import_path(function)

        if not function_name:
            # logging.warning(f"Failed toget function name")
            return

        if not class_name:
            # It's fine to have None as a class name
            class_name = NOT_CLASS_METHOD_NAME

        if not import_path:
            # logging.warning(f"Failed to get import path")
            return

        if IS_PDFRW:
            self.count_by_file_iid[dyn_ast][iid] += 1

        zfill_len = 6
        zfilled_iid = str(iid).zfill(zfill_len)
        zfilled_count = str(self.count).zfill(zfill_len)
        self.count += 1

        # Create a directory for the log files
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

        pickle_prefix = f"{zfilled_count}_{zfilled_iid}"
        call_pickle_file_path = os.path.join(self.log_dir, f"{pickle_prefix}_CALL.pickle")
        return_pickle_file_path = os.path.join(self.log_dir, f"{pickle_prefix}_RETURN.pickle")
        meta_file_path = os.path.join(self.log_dir, f"{pickle_prefix}_META.txt")

        # pos_args, kw_args = self.call_return_pairs[iid].pop()
        # try:
        #     pos_args = copy.deepcopy(pos_args)
        #     kw_args = copy.deepcopy(kw_args)
        # except Exception as e:
        #     return

        try:
            with open(call_pickle_file_path, "wb") as f:
                pickle.dump((pos_args, kw_args), f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            with open(self.error_file_path, "a") as f:
                f.write(f"Failed to dump call: {call_pickle_file_path}\n")
            return

        try:
            with open(return_pickle_file_path, "wb") as f:
                pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            with open(self.error_file_path, "a") as f:
                f.write(f"Failed to dump return: {return_pickle_file_path}\n")
            return

        if not IS_PDFRW:
            self.count_by_file_iid[dyn_ast][iid] += 1

        # Resolve import path from module object and save it as a text file
        # The file content looks like this:
        """
        {function name}
        {class name if it's a class/instance method, otherwise `NOT_CLASS_METHOD_NAME`}
        {import path}
        {call pickle file path}
        {return pickle file path}
        """
        assert function_name and isinstance(function_name, str)
        assert class_name and isinstance(class_name, str)
        assert import_path and isinstance(import_path, str)
        assert call_pickle_file_path and isinstance(call_pickle_file_path, str)
        assert return_pickle_file_path and isinstance(return_pickle_file_path, str)

        with open(meta_file_path, "w") as f:
            f.write(function_name + "\n")
            f.write(class_name + "\n")
            f.write(import_path + "\n")
            f.write(call_pickle_file_path + "\n")
            f.write(return_pickle_file_path + "\n")

        return

    # def begin_execution(self) -> None:
    #     """Hook for the start of execution."""
    #     # self.log(-1, "Execution started")

    #     pass

    # def end_execution(self) -> None:
    #     """Hook for the end of execution."""
    #     # self.log(-1, "Execution ended")

    #     pass
