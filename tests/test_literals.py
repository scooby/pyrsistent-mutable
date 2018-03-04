from mock import patch

from pyrsistent import pmap, PMap, PVector, pvector, PSet, pset
import pytest
from pytest import raises
import sys

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
    with raises(ValueError):
        @pyrmute
        def subject():
            return {}

        subject()


@pytest.mark.skipif(sys.version_info < (3, 0), reason="Requires python3")
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
    with raises(ValueError):
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
