from ast import parse
import inspect
from io import StringIO
from textwrap import dedent
from astunparse import Unparser

from .flags import get_flags
from .rewrite import rewrite

_in_pyrmute = 0


def pyrmute(target=None, *, write_source=True):
    '''
    Rewrite a decorated function using imperative commands to use the pyrsistent API.
    :param target: A function to rewrite.
    :param write_source: By default, write the translated source to `__source__`, set this to false to disable.
    :return: the rewritten function.
    '''
    def dec(func):
        global _in_pyrmute
        if _in_pyrmute:
            # inspect.getsource returns this decorator as well. It's easiest to let python
            # invoke this decorator and simply have it do nothing by setting a global flag.
            return func
        source = dedent(inspect.getsource(func))
        filename = inspect.getsourcefile(func)
        _check_closure(inspect.getclosurevars(func))
        module = inspect.getmodule(func)
        flags = get_flags(module)
        tree = parse(source, filename)
        transformed = rewrite(tree)

        code = compile(transformed, filename=filename, mode='exec', flags=flags)
        module = dict(vars(module))
        _in_pyrmute = True
        try:
            exec(code, module)
        finally:
            _in_pyrmute = False

        result = module[func.__name__]
        if write_source:
            result.__source__ = show_ast(transformed)
        return result

    return dec if target is None else dec(target)


def _check_closure(closure):
    if closure.nonlocals:
        # To do nonlocals, we'll need to reevaluate a larger function. So what we want is a
        # top-level decorator that does the rewrite and inner decorators that mark the code
        # to be rewritten.
        raise TypeError('Top level function has nonlocals {}; not supported yet.'
                        .format(', '.join(closure.nonlocals)))


def show_ast(node):
    with StringIO() as fh:
        Unparser(node, file=fh)
        return fh.getvalue()
