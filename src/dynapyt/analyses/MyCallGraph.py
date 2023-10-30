import os
from datetime import datetime
import logging
import pickle
from typing import Any, Callable, Dict, Optional, Tuple
from .BaseAnalysis import BaseAnalysis

import inspect

# from itertools import accumulate
# # from inspect import getmodule, getabsfile
# import inspect

# def sum(a, b, c=10, d=1000):
#     return a + b + c + d

# def get_module(module):
#         file_path = None

#         parent_module = inspect.getmodule(module)
#         try:
#                 file_path = parent_module.__file__
#         except:
#                 pass

#         return file_path, parent_module.__name__

# def print_module_info(module):
#         print(f"Inspecting module: {module.__name__}")
#         file_path, parenet_module_name = get_module(module)
#         if file_path is None:
#                 print("Built-in module")
#         else:
#                 print(f"Defined in {file_path}")

#         print(f"Parent module name: {parenet_module_name}\n")

# print_module_info(accumulate)
# print_module_info(sum)
# print_module_info(inspect)
# print_module_info(inspect)

def get_module_file_path(module: Callable) -> Optional[str]:
    """
    Returns the path of the file where the module is defined.
    If it fails to get the path, returns None.
    """
    try:
        return module.__file__
    except:
        return None

def is_target_module(file_path: Optional[str], target_module_path: Optional[str]) -> bool:
    if not target_module_path:
        return False

    if not file_path:
        return False

    return target_module_path in file_path

def get_import_path(module: Callable, target_module_path: Optional[str]) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Returns the module name, import path of the module, and whether or not
    the module is under specified target path.
    If `target_module_path` is not specified, the second return value is always False.
    If it fails to resolve the module import path,
    it returns either `"{module_name}", None, False` or `None, None, False`.

    Example:
        >>> get_import_path(getmodule, "versions/3.11.0/lib/python3.11/inspect.py")
        "getmodule", "from inspect import getmodule", True
        >>> get_import_path(accumulate, "versions/3.11.0/lib/python3.11/inspect.py")
        "accumulate", "from itertools import accumulate", False
    """

    try:
        module_name = module.__name__
    except:
        return None, None, False

    parent_module = inspect.getmodule(module)

    # This cannot be done by simply comparing 2 names
    # Example: from datetime import datetime
    if parent_module == module:

        file_path = get_module_file_path(module)
        return f"import {module_name}", is_target_module(module_name, target_module_path)

    file_path = get_module_file_path(parent_module)
    try:
        parent_module_name = parent_module.__name__
    except:
        return module_name, None, False

    return module_name, f"from {parent_module_name} import {module_name}", is_target_module(file_path, target_module_path)


LOG_BASE = "/Users/keita/projects/DynaPyt/logs"
TARGET_MODULE_PATH = "site-packages/pdfrw/"

class MyCallGraph(BaseAnalysis):

    def __init__(self) -> None:
        super().__init__()
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        handler = logging.FileHandler("output.log", "w", "utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        root_logger.addHandler(handler)

        # Formatted time string when the class is instantiated
        self.running_time = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

        # key: iid, value: List[(module, pos_args, kw_args)]
        self.call_return_pairs = {}

        self.count = 0

        self.log_dir = os.path.join(LOG_BASE, self.running_time)

        self.error_file_path = os.path.join(self.log_dir, "error.txt")

        os.makedirs(self.log_dir, exist_ok=True)

        with open(self.error_file_path, "w") as f:
            f.write("")

    def log(self, iid: int, *args, **kwargs):
        res = ""
        for arg in args:
            if 'danger_of_recursion' in kwargs:
                res += ' ' + str(hex(id(arg)))
            else:
                res += ' ' + str(arg)
        logging.info(str(iid) + ": " + res[:200])

    # Function Call

    def pre_call(
        self, dyn_ast: str, iid: int, function: Callable, pos_args: Tuple, kw_args: Dict
    ):
        """Hook called before a function call happens.


        Parameters
        ----------
        dyn_ast : str
            The path to the original code. Can be used to extract the syntax tree.

        iid : int
            Unique ID of the syntax tree node.

        function : str
            Function which will be called.

        pos_args : Tuple
            The positional arguments passed to the function.

        kw_args : Dict
            The keyword arguments passed to the function.

        """

        function_name, _, is_target = get_import_path(function, TARGET_MODULE_PATH)
        if not is_target:
            return

        if function_name is None:
            function_name = "FAILED_TO_GET_NAME"

        if iid not in self.call_return_pairs:
            self.call_return_pairs[iid] = []

        self.call_return_pairs[iid].append((function_name, pos_args, kw_args))
        # self.log(iid, f"Before function call: {function_name} ({'/'.join(list(dyn_ast.split('/')[-3:]))}) with", pos_args, kw_args)

    def post_call(
        self,
        dyn_ast: str,
        iid: int,
        result: Any,
        call: Callable,
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

        function_name, import_path, is_target = get_import_path(call, TARGET_MODULE_PATH)
        if not is_target:
            return

        if iid not in self.call_return_pairs:
            print("ERROR: call not found")
            return

        if len(self.call_return_pairs[iid]) == 0:
            print("ERROR: call not found")
            return

        zfilled_iid = str(iid).zfill(5)
        zfilled_count = str(self.count).zfill(5)
        self.count += 1

        pickle_prefix = f"{zfilled_count}_{zfilled_iid}"
        call_pickle_file_path = os.path.join(self.log_dir, f"{pickle_prefix}_CALL.pickle")
        return_pickle_file_path = os.path.join(self.log_dir, f"{pickle_prefix}_RETURN.pickle")
        meta_file_path = os.path.join(self.log_dir, f"{pickle_prefix}_META.txt")

        _, pos_args, kw_args = self.call_return_pairs[iid].pop()


        if self.count > 200:
            # too much data for now
            return

        try:
            with open(call_pickle_file_path, "wb") as f:
                pickle.dump((call, pos_args, kw_args), f, protocol=pickle.HIGHEST_PROTOCOL)
        except:
            with open(self.error_file_path, "a") as f:
                f.write(f"Failed to dump call: {call_pickle_file_path}\n")

        try:
            with open(return_pickle_file_path, "wb") as f:
                pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)
        except:
            with open(self.error_file_path, "a") as f:
                f.write(f"Failed to dump return: {return_pickle_file_path}\n")

        # Resolve import path from module object and save it as a text file
        # The file content looks like this:
        """
        {function name}
        {import path}
        {call pickle file path}
        {return pickle file path}
        """
        with open(meta_file_path, "w") as f:
            f.write(function_name + "\n")
            f.write(import_path + "\n")
            f.write(call_pickle_file_path + "\n")
            f.write(return_pickle_file_path + "\n")
