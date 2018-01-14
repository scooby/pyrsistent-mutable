from pyrsistent_mutable.rewrite import Names
from ast import parse

check_mod = parse('''
import mod_name.bar.qux
from .relative_name import relative_name
import another.module as aliased_module
from some.mod import imported_name
from some.mod import thing as aliased_name

global_name = 1
async def async_func():
    local_name = 2
def func_name(param_name):
    del some_name
class class_name:
    pass
''')


def test_sees_names():
    expected = {'aliased_module', 'aliased_name', 'async_func', 'class_name',
                'func_name', 'global_name', 'imported_name', 'mod_name', 'relative_name'}
    with Names(check_mod) as subj:
        assert subj.names == expected


def test_skips_existent():
    with Names(check_mod, prefix='') as subj:
        assert subj.dotted('test', 'mod', 'func_name') == 'func_name0'
        assert subj.dotted('test', 'mod2', 'func_name') == 'func_name1'
        assert subj.dotted('test', 'mod', 'func_name') == 'func_name0'
        assert subj.dotted('test', 'mod2', 'func_name') == 'func_name1'

