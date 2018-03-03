from ast import parse, Expr, Module, Num, Subscript, Name, Tuple, Call, Attribute, Load, NameConstant
from pyrsistent_mutable.rewrite import deslicify, match_ast
# from astunparse import dump

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
                NameConstant(value={'start'}),
                Num(n={'stop'}),
                Num(n={'step'})
            ]
        ), actual
    )
    assert check == {'start': None, 'stop': 44, 'step': 3}
