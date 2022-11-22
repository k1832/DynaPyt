# DYNAPYT: DO NOT INSTRUMENT


from dynapyt.runtime import _catch_
from dynapyt.runtime import _sub_, _write_, _gen_, _int_, _read_, _enter_if_, _return_, _aug_assign_, _str_, _call_, _comp_op_, _exit_for_, _exit_if_

_dynapyt_ast_ = __file__ + ".orig"
try:
    def binary_to_decimal(s):
        ret = _write_(_dynapyt_ast_, 1, _int_(_dynapyt_ast_, 0, 0), [lambda: ret])
        # Not elegant but for branching test...
        for i in _gen_(_dynapyt_ast_, 14, _call_(_dynapyt_ast_, 4, range, False, [("", _call_(_dynapyt_ast_, 3, len, False, [("", _read_(_dynapyt_ast_, 2, lambda: s))], {}))], {})):
            ret <<= _aug_assign_(_dynapyt_ast_, 6, lambda: ret, 6, _int_(_dynapyt_ast_, 5, 1))
            if _enter_if_(_dynapyt_ast_, 13, _comp_op_(_dynapyt_ast_, 10, _sub_(_dynapyt_ast_, 9, _read_(_dynapyt_ast_, 7, lambda: s), [_read_(_dynapyt_ast_, 8, lambda: i)]), [(0, '1')])):
                ret += _aug_assign_(_dynapyt_ast_, 12, lambda: ret, 0, _int_(_dynapyt_ast_, 11, 1))
                _exit_if_(_dynapyt_ast_, 13)
        else:
            _exit_for_(_dynapyt_ast_, 14)
        return _return_(_dynapyt_ast_, 16, return_val = _read_(_dynapyt_ast_, 15, lambda: ret))

    def main():
        _call_(_dynapyt_ast_, 20, print, False, [("", _call_(_dynapyt_ast_, 19, _read_(_dynapyt_ast_, 17, lambda: binary_to_decimal), False, [("", _str_(_dynapyt_ast_, 18, "101011"))], {}))], {})

    if _enter_if_(_dynapyt_ast_, 24, _comp_op_(_dynapyt_ast_, 21, __name__, [(0, "__main__")])):
        _call_(_dynapyt_ast_, 23, _read_(_dynapyt_ast_, 22, lambda: main), False, [], {})
        _exit_if_(_dynapyt_ast_, 24)
except Exception as _dynapyt_exception_:
    _catch_(_dynapyt_exception_)
