from ast import parse, Expr, Module, Num, Subscript, Name, Tuple
from pyrsistent_mutable.rewrite import deslicify, match_ast

pattern = Module(body=[Expr(value=Subscript(value=Name(id={'name'}), slice={'slice'}))])


def test_simple_index():
    result = match_ast(pattern, parse('x[42]'))
    actual = deslicify(result['slice'])

    check = match_ast(Num(n={'num'}), actual)
    assert check == {'num': 42}


def test_ext_slice():
    result = match_ast(pattern, parse('x[0, 1, 2]'))
    actual = deslicify(result['slice'])

    check = match_ast(Tuple(elts=[Num(n={'n1'}), Num(n={'n2'}), Num(n={'n3'})]), actual)
    assert check == {'n1': 0, 'n2': 1, 'n3': 2}
