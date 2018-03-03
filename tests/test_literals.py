from unittest.mock import patch

from pyrsistent import pmap, PMap, PVector, pvector, PSet, pset
import pytest

from pyrsistent_mutable import pyrmute


def test_dict_literal():
    "Test that {a:b, c:d} is translated to a pmap."

    @pyrmute
    def subject():
        local = {'a': 'b', 'c': 'd'}
        del local['c']
        local['e'] = 'f'
        return local

    print(subject.__source__)

    actual = subject()

    assert isinstance(actual, PMap)
    assert actual == pmap({'a': 'b', 'e': 'f'})


@patch('pyrsistent._pmap.pmap', side_effect=ValueError)
def test_patching_pmap(_):
    "Test that our patch correctly identifies pmap."
    with pytest.raises(ValueError):
        @pyrmute
        def subject():
            return {}

        subject()


@patch('pyrsistent._pmap.pmap', side_effect=AssertionError)
def test_dict_literal_in_splat(_):
    "Test that **{a:b, c:d} is *not* translated to a pmap."

    @pyrmute
    def subject():
        def simple_func(**kw):
            return len(kw)

        return simple_func(**{'a': 'b', 'c': 'd'})

    print(subject.__source__)

    assert subject() == 2


def test_dict_comprehension():
    "Test that {a:b for a, b in ...} is translated to a pmap."

    @pyrmute
    def subject(m):
        local = {v: k for k, v in m.items()}
        del local['d']
        local['e'] = 'f'
        return local

    print(subject.__source__)

    actual = subject({'a': 'b', 'c': 'd'})

    assert isinstance(actual, PMap)
    assert actual == pmap({'b': 'a', 'e': 'f'})


def test_list_literal():
    "Test that [1, 2, 3] is translated to a pvector."

    @pyrmute
    def subject():
        local = [1, 2, 3]
        del local[1]
        local += [4, 5, 6]
        return local

    print(subject.__source__)

    actual = subject()

    assert isinstance(actual, PVector)
    assert actual == pvector([1, 3, 4, 5, 6])


@patch('pvectorc.pvector', side_effect=ValueError)
def test_patching_pvector(_):
    "Test that our patch correctly identifies pvector."
    with pytest.raises(ValueError):
        @pyrmute
        def subject():
            return []

        subject()


def test_list_comprehension():
    "Test that [a for a in ...] is translated to a pvector."

    @pyrmute
    def subject(m):
        local = [n * 10 for n in m]
        del local[2]
        local.append(42)
        return local

    print(subject.__source__)

    actual = subject([1, 2, 3, 4])

    assert isinstance(actual, PVector)
    assert actual == pvector([10, 20, 40, 42])


def test_set_literal():
    "Test that {1, 2, 3} is translated to a pset."

    @pyrmute
    def subject():
        local = {1, 2, 2, 3}
        local |= {3, 4, 5}
        return local

    print(subject.__source__)

    actual = subject()

    assert isinstance(actual, PSet)
    assert actual == pset({1, 2, 2, 3, 3, 4, 5})


@patch('pyrsistent._pset.pset', side_effect=ValueError)
def test_patching_pset(_):
    "Test that our patch correctly identifies pset."
    with pytest.raises(ValueError):
        @pyrmute
        def subject():
            return {1, 2}

        subject()


def test_set_comprehension():
    "Test that {a for a in ...} is translated to a pset."

    @pyrmute
    def subject(m):
        local = {n // 10 for n in m}
        local |= {40, 50, 60}
        return local

    print(subject.__source__)

    actual = subject([10, 15, 20, 25, 30, 35, 40, 45])

    assert isinstance(actual, PSet)
    assert actual == pset([1, 2, 3, 4, 40, 50, 60])
