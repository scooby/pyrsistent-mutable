from mock import patch
import pytest
from pytest import raises

from pyrsistent import PMap, pmap, PSet, pset
from pyrsistent_mutable import pyrmute

import sys


if sys.version_info >= (3, 1, 0):
    import tests.py3funcs as funcs
else:
    funcs = None

python3_only = pytest.mark.skipif(funcs is None, reason="requires Python3.1")


@python3_only
def test_dict_comprehension():
    "Test that {a:b for a, b in ...} is translated to a pmap."

    subject = funcs.dict_comprehension
    print(subject.__source__)

    actual = subject({'a': 'b', 'c': 'd'})

    assert isinstance(actual, PMap)
    assert actual == pmap({'b': 'a', 'e': 'f'})


@python3_only
def test_set_literal():
    "Test that {1, 2, 3} is translated to a pset."

    subject = funcs.set_literal
    print(subject.__source__)

    actual = subject()

    assert isinstance(actual, PSet)
    assert actual == pset([1, 2, 2, 3, 3, 4, 5])


@python3_only
@patch('pyrsistent._pset.pset', side_effect=ValueError)
def test_patching_pset(_):
    "Test that our patch correctly identifies pset."
    with raises(ValueError):
        subject = pyrmute(funcs.set_literal_not_translated)

        subject()


@python3_only
def test_set_comprehension():
    "Test that {a for a in ...} is translated to a pset."

    subject = funcs.set_comprehension
    print(subject.__source__)

    actual = subject([10, 15, 20, 25, 30, 35, 40, 45])

    assert isinstance(actual, PSet)
    assert actual == pset([1, 2, 3, 4, 40, 50, 60])
