import os
from datetime import datetime
import logging
import pickle
from typing import Any, Callable, Dict, Optional, Tuple
from .BaseAnalysis import BaseAnalysis

import inspect

LOG_BASE = "/Users/keita/projects/DynaPyt/logs"
# TARGET_MODULE_PATH = "/projects/casanova/casanova"
# TARGET_MODULE_PATH = "/Users/keita/projects/flair/flair"
TARGET_MODULE_PATH = "/Users/keita/projects/pdfrw/pdfrw"

NOT_CLASS_METHOD_NAME = "NOT_A_CLASS_METHOD"

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

def get_import_path(module: Callable, target_module_path: Optional[str] = None) -> Tuple[Optional[str], Optional[str], Optional[str], bool]:
    """
    Returns 4 values:
        - module name
        - class name if it's class/instance method, otherwise None
        - import path of the module or class,
        - whether or not the module is under specified target path
    If `target_module_path` is not specified or None, the last return value is always False.
    If it fails to resolve the module import path,
    it returns `"{module_name}", "{class_name}", None, False`.

    Example:
        >>> get_import_path(getmodule, "versions/3.11.0/lib/python3.11/inspect.py")
        "getmodule", None, "from inspect import getmodule", True
        >>> get_import_path(accumulate, "versions/3.11.0/lib/python3.11/inspect.py")
        "accumulate", None, "from itertools import accumulate", False
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
        return None, None, None, False

    class_name = None
    if inspect.ismethod(module):
        try:
            class_name = module.__self__.__name__
        except:
            # TODO(k1832): Revisit if skipping instance method is a good idea
            # TODO(k1832): Revisit if it's sufficient to conclude it's instance method
            # Exclude instance methods (i.e. methods in a class without @classmethod)
            return module_name, None, None, False
    else:
        try:
            qualname = module.__qualname__
            if not isinstance(module_name, str):
                raise Exception("qualname is not a string")
        except:
            return module_name, None, None, False

        period_split = qualname.split(".")

        if len(period_split) > 2:
            # Now it can only handle {Class name}.{static method name}
            logging.warning(f"qualname: {qualname} not supported")
            return module_name, None, None, False

        if len(period_split) == 2:
            class_name = period_split[0]

    parent_module = inspect.getmodule(module)

    # This cannot be done by simply comparing 2 names
    # Example: from datetime import datetime
    if parent_module == module:

        file_path = get_module_file_path(module)
        return (module_name,
                class_name,
                f"import {class_name if class_name else module_name}",
                is_target_module(module_name, target_module_path))

    file_path = get_module_file_path(parent_module)
    try:
        parent_module_name = parent_module.__name__
    except:
        return module_name, class_name, None, False

    return (module_name,
            class_name,
            f"from {parent_module_name} import {class_name if class_name else module_name}",
            is_target_module(file_path, target_module_path))



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

        # key: iid, value: List[(pos_args, kw_args)]
        self.call_return_pairs = {}

        self.count = 0

        self.log_dir = os.path.join(LOG_BASE, self.running_time)
        self.error_file_path = os.path.join(self.log_dir, "error.txt")

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

        function_name, _, _, is_target = get_import_path(function, TARGET_MODULE_PATH)
        if not function_name:
            return
        if not is_target:
            return

        if iid not in self.call_return_pairs:
            self.call_return_pairs[iid] = []

        self.call_return_pairs[iid].append((pos_args, kw_args))
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

        function_name, class_name, import_path, is_target = get_import_path(call, TARGET_MODULE_PATH)

        if not function_name:
            logging.warning(f"Failed to get function name")
            return

        if not is_target:
            return

        if iid not in self.call_return_pairs:
            logging.error(f"ERROR: call not found for iid: {iid}")
            return

        if len(self.call_return_pairs[iid]) == 0:
            logging.error(f"ERROR: call not found for iid: {iid}")
            return

        zfill_len = 6
        zfilled_iid = str(iid).zfill(zfill_len)
        zfilled_count = str(self.count).zfill(zfill_len)
        self.count += 1

        # Create a directory for the log files
        os.makedirs(self.log_dir, exist_ok=True)

        pickle_prefix = f"{zfilled_count}_{zfilled_iid}"
        call_pickle_file_path = os.path.join(self.log_dir, f"{pickle_prefix}_CALL.pickle")
        return_pickle_file_path = os.path.join(self.log_dir, f"{pickle_prefix}_RETURN.pickle")
        meta_file_path = os.path.join(self.log_dir, f"{pickle_prefix}_META.txt")

        pos_args, kw_args = self.call_return_pairs[iid].pop()

        try:
            with open(call_pickle_file_path, "wb") as f:
                pickle.dump((pos_args, kw_args), f, protocol=pickle.HIGHEST_PROTOCOL)
        except:
            with open(self.error_file_path, "a") as f:
                f.write(f"Failed to dump call: {call_pickle_file_path}\n")

        try:
            with open(return_pickle_file_path, "wb") as f:
                pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)
        except:
            with open(self.error_file_path, "a") as f:
                f.write(f"Failed to dump return: {return_pickle_file_path}\n")

        if not class_name:
            class_name = NOT_CLASS_METHOD_NAME
        # Resolve import path from module object and save it as a text file
        # The file content looks like this:
        """
        {function name}
        {class name if it's a class/instance method, otherwise `NOT_CLASS_METHOD_NAME`}
        {import path}
        {call pickle file path}
        {return pickle file path}
        """
        with open(meta_file_path, "w") as f:
            f.write(function_name + "\n")
            f.write(class_name + "\n")
            f.write(import_path + "\n")
            f.write(call_pickle_file_path + "\n")
            f.write(return_pickle_file_path + "\n")

    # def begin_execution(self) -> None:
    #     """Hook for the start of execution."""
    #     # self.log(-1, "Execution started")

    #     pass

    # def end_execution(self) -> None:
    #     """Hook for the end of execution."""
    #     # self.log(-1, "Execution ended")

    #     pass
