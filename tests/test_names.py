from pyrsistent_mutable.rewrite import Names
from pyrsistent_mutable.ast6 import match_ast
from ast import parse, ImportFrom, alias, dump

import sys


def check_mod():
    return parse('''
import mod_name.bar.qux
from .relative_name import relative_name
import another.module as aliased_module
from some.mod import imported_name
from some.mod import thing as aliased_name

global_name = 1
{}def async_func():
    local_name = 2
def func_name(param_name):
    del some_name
class class_name:
    pass
'''.format('async ' if sys.version_info > (3, 4) else ''))


def test_sees_names():
    expected = set(['aliased_module', 'aliased_name', 'async_func', 'class_name', 'func_name', 'global_name',
                    'imported_name', 'mod_name', 'relative_name'])
    with Names(check_mod()) as subj:
        assert subj.names == expected


def test_skips_existent():
    module = check_mod()
    with Names(module, prefix='') as subj:
        assert subj.dotted('test', 'mod', 'func_name') == 'func_name0'
        assert subj.dotted('test', 'mod2', 'func_name') == 'func_name1'
        assert subj.dotted('test', 'mod', 'func_name') == 'func_name0'
        assert subj.dotted('test', 'mod2', 'func_name') == 'func_name1'

    expect = ImportFrom(
        module=set(['mod']),
        names=[alias(
            name=set(['name']),
            asname=set(['asname'])
        )])
    print(dump(module))
    assert match_ast(expect, module.body[0]) == {'asname': 'func_name0', 'mod': 'test.mod', 'name': 'func_name'}
    assert match_ast(expect, module.body[1]) == {'asname': 'func_name1', 'mod': 'test.mod2', 'name': 'func_name'}
