import logging
from typing import Any, Callable, Dict, Tuple
from .BaseAnalysis import BaseAnalysis


class MyCallGraph(BaseAnalysis):

    def __init__(self) -> None:
        super().__init__()
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        handler = logging.FileHandler("output.log", "w", "utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        root_logger.addHandler(handler)

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
        function_name = "FAILED_TO_GET_NAME"
        try:
            function_name = function.__name__
        except:
            pass

        self.log(iid, f"Before function call: {function_name} ({'/'.join(list(dyn_ast.split('/')[-3:]))}) with", pos_args, kw_args)

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
        self.log(iid, "After function call, result: ", result)
