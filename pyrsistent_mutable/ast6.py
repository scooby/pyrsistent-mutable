'''
Some functions to work around incompatibilities between the AST in python 2 and 3.
'''

from ast import Name, Call

try:
    from ast import NameConstant as name_constant
except ImportError:
    def name_constant(value):
        if value in (None, True, False):
            return Name(id=repr(value))
        else:
            return Name(id=value)


if 'starargs' in Call._fields or 'kwargs' in Call._fields:
    def call6(func, args=None, keywords=None):
        return Call(func=func, args=args or [], keywords=keywords or [], starargs=None, kwargs=None)
else:
    def call6(func, args=None, keywords=None):
        return Call(func=func, args=args or [], keywords=keywords or [])
