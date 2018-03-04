from ast import Attribute, Call, Expr, Load, Module, Name, Num, Subscript, Tuple, parse
from pyrsistent_mutable.ast6 import name_constant
from pyrsistent_mutable.rewrite import deslicify, match_ast


pattern = Module(body=[Expr(value=Subscript(value=Name(id=set(['name'])), slice=set(['slice'])))])


def test_simple_index():
    result = match_ast(pattern, parse('x[42]'))
    actual = deslicify(result['slice'])

    check = match_ast(Num(n=set(['num'])), actual)
    assert check == {'num': 42}


def test_ext_slice():
    result = match_ast(pattern, parse('x[0, 1, 2]'))
    actual = deslicify(result['slice'])

    check = match_ast(Tuple(elts=[Num(n=set(['n1'])),
                                  Num(n=set(['n2'])),
                                  Num(n=set(['n3']))]), actual)
    assert check == {'n1': 0, 'n2': 1, 'n3': 2}


def test_slice():
    result = match_ast(pattern, parse('x[:44:3]'))
    actual = deslicify(result['slice'])

    check = match_ast(
        Call(
            func=Attribute(
                value=Name(id='__builtins__', ctx=Load()),
                attr='slice',
                ctx=Load()
            ), args=[
                name_constant(value=set(['start'])),
                Num(n=set(['stop'])),
                Num(n=set(['step']))
            ]
        ), actual
    )
    assert check == {'start': None, 'stop': 44, 'step': 3} or check == {'start': 'None', 'stop': 44, 'step': 3}
