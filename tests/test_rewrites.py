import pyrsistent_mutable
from pyrsistent import field, pvector, pset, PRecord
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


class MockClass(PRecord):
    foo = field()
    other = field()


class MockClass2(PRecord):
    bar = field()
    other = field()


class MockClass3(PRecord):
    qux = field()
    other = field()


def test_simple_attr_assign():
    import tests.assign as test_mod

    value = MockClass(foo=7, other=33)
    actual = test_mod.simple_attr_assign(value)

    assert actual == MockClass(foo=10, other=33)


def test_complex_attr_assign():
    import tests.assign as test_mod

    value = MockClass(foo=MockClass2(bar=MockClass3(qux=7, other=11), other=22), other=33)
    actual = test_mod.complex_attr_assign(value)

    assert actual == MockClass(foo=MockClass2(bar=MockClass3(qux=20, other=11), other=22), other=33)


'''
def complex_attr_assign(value):
    value.foo.bar.qux = 20
    return value


def simple_index_assign(value):
    value['foo'] = 30
    return value


def complex_index_assign(value):
    value.foo['bar']['qux'] = 40
    return value

'''
