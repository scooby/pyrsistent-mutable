'''
Some functions to work around incompatibilities between the AST in python 2 and 3.
'''
from _ast import AST, Slice, Index, ExtSlice, Tuple, Load
from ast import Name, Call, iter_fields, NodeTransformer, copy_location, dump
from copy import deepcopy

from pyrsistent_mutable.rewrite import _slice

try:
    from ast import NameConstant
except ImportError:
    def NameConstant(value):
        return Name(id=repr(value))


def cl(node, loc):
    return copy_location(node, loc) if loc is not None else node


def name_constant(value, loc=None):
    return cl(NameConstant(value), loc)


def call6(func, args=None, keywords=None, loc=None):
    '''
    Construct a Call node with the given args or keywords list.

    This doesn't handle foo(*args, **args); dummy values for the `starargs` and `kwargs` fields are present
    to support python2.7
    :param func: the function name or expression
    :param args: a list of expressions as positional arguments.
    :param keywords: a list of `keyword` nodes.
    :param loc: The source location node.
    :return: a Call node.
    '''
    return cl(Call(func=func, args=args or [], keywords=keywords or [], starargs=None, kwargs=None), loc)


class Cap(str):
    '''
    Use in match_ast to capture a variable in a pattern.
    '''
    __slots__ = ()


def match_ast(pattern, node):
    '''
    Matches a node against a pattern and returns the values of placeholders.
    :param pattern: An AST node with child nodes or strings as placeholders.
    :param node: The node to match against.
    :return: A dictionary of placeholders with values seen, or None to indicate a failure.
    '''

    if isinstance(pattern, Cap) and len(pattern) == 1:
        return {str(pattern): node}

    if not isinstance(node, type(pattern)):
        return None

    if isinstance(pattern, list):
        if len(pattern) != len(node):
            return None
        result = {}
        for pelem, nelem in zip(pattern, node):
            found = match_ast(pelem, nelem)
            if found is None:
                return None
            result.update(found)
        return result

    if isinstance(pattern, AST):
        result = {}
        for field, expect in iter_fields(pattern):
            found = getattr(node, field, None)
            found = match_ast(expect, found)
            if found is None:
                return None
            result.update(found)
        return result

    if pattern == node:
        return {}
    else:
        return None


class Context(NodeTransformer):
    '''
    Copy some AST and transform the context to be Store, Load, etc.

    This is so that we can do surgery with expressions and assignments, translating context
    from Store to Load or vice versa.
    '''
    def __init__(self, ctx):
        self._ctx = ctx

    @classmethod
    def set(cls, ctx, node):
        node = deepcopy(node)
        cls(ctx).visit(node)
        return node

    def visit_AugLoad(self, _):
        return self._ctx()

    def visit_AugStore(self, _):
        return self._ctx()

    def visit_Del(self, _):
        return self._ctx()

    def visit_Store(self, _):
        return self._ctx()

    def visit_Load(self, _):
        return self._ctx()

    def visit_Param(self, _):
        return self._ctx()


def deslicify(subscript):
    '''
    Rewrite a subscript expression as a call to the builtin `slice` function.

    The result should be what your `__getitem__` method would see.
    :param subscript: The AST node for a subscript expression.
    :return: A literal equivalent to the subscript expression.
    '''
    def fix_none(node):
        if node is None:
            return name_constant(None, loc=subscript)
        else:
            return node

    def fix_slice(node):
        if isinstance(node, Slice):
            return call6(func=_slice, args=[fix_none(node.lower), fix_none(node.upper), fix_none(node.step)], loc=node)
        else:
            return fix_none(node)

    if isinstance(subscript, Index):
        return subscript.value
    elif isinstance(subscript, ExtSlice):
        elems = map(fix_slice, subscript.dims)
        return cl(Tuple(elts=list(elems), ctx=Load()), subscript)
    elif isinstance(subscript, Slice):
        return fix_slice(subscript)
    else:
        raise TypeError('Expected {} to be a subscript expression.'.format(dump(subscript)))
