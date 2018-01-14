import pyrsistent_mutable
from pyrsistent import pvector, pset, PRecord
pyrsistent_mutable.set_debug(True, True)


def test_aug_assign_plus():
    import tests.aug_assign as test_mod

    left = pvector([1, 2, 3])
    right = pvector([10, 20, 30])

    actual = test_mod.plus(left, right)

    assert actual == pvector([1, 2, 3, 10, 20, 30])


def test_aug_assign_union():
    import tests.aug_assign as test_mod

    left = pset([1, 2, 3])
    right = pset([3, 2, 4])

    actual = test_mod.union(left, right)

    assert actual == pset([1, 2, 3, 4])


#def test_attr_assign():
