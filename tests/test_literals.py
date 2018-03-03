from unittest.mock import patch

from pyrsistent import pmap, PMap
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
def test_the_patch(_):
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
