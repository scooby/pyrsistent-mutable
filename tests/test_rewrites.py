from pyrsistent import PRecord, field, pset, pvector, pmap

from pyrsistent_mutable import pyrmute


@pyrmute
def plus(left, right):
    left += right
    return left


@pyrmute
def union(left, right):
    left |= right
    return left


def test_aug_assign_plus():
    "Test left += right."
    left = pvector([1, 2, 3])
    right = pvector([10, 20, 30])

    actual = plus(left, right)

    assert actual == pvector([1, 2, 3, 10, 20, 30])


def test_aug_assign_union():
    "Test left |= right"

    left = pset([1, 2, 3])
    right = pset([3, 2, 4])

    actual = union(left, right)

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


@pyrmute
def simple_attr_assign(value):
    value.foo = 10
    return value


def test_simple_attr_assign():
    "Test value.foo = 10"
    value = MockClass(foo=7, other=33)
    actual = simple_attr_assign(value)

    assert actual == MockClass(foo=10, other=33)


@pyrmute
def complex_attr_assign(value):
    value.foo.bar.qux = 20
    return value


def test_complex_attr_assign():
    "Test value.foo.bar.qux = 20"

    value = MockClass(foo=MockClass2(bar=MockClass3(qux=7, other=11), other=22), other=33)
    actual = complex_attr_assign(value)

    assert actual == MockClass(foo=MockClass2(bar=MockClass3(qux=20, other=11), other=22), other=33)


@pyrmute
def simple_index_assign(value):
    value['foo'] = 30
    return value


def test_simple_index_assign():
    "Test value['foo'] = 30"

    value = MockClass(foo=7, other=33)
    actual = simple_index_assign(value)

    assert actual == MockClass(foo=30, other=33)


@pyrmute
def complex_index_assign(value):
    value.foo['bar']['qux'] = 40
    return value


def test_complex_index_assign():
    "Test value.foo['bar']['qux'] = 40"

    value = MockClass(foo=MockClass2(bar=MockClass3(qux=7, other=11), other=22), other=33)
    actual = complex_index_assign(value)

    assert actual == MockClass(foo=MockClass2(bar=MockClass3(qux=40, other=11), other=22), other=33)


@pyrmute
def simple_invoke(value):
    value.append(20)
    return value


def test_simple_method():
    "Test value.append(20)"

    value = pvector([1, 2, 3])
    actual = simple_invoke(value)

    assert actual == pvector([1, 2, 3, 20])


@pyrmute
def complex_invoke(value):
    value.foo.extend([20, 30, 40])
    return value


def test_complex_method():
    "Test value.foo.extend([20, 30, 40])"

    value = MockClass(foo=pvector([1, 2, 3]), other=44)
    actual = complex_invoke(value)

    assert actual == MockClass(foo=pvector([1, 2, 3, 20, 30, 40]), other=44)


@pyrmute
def regular_deletes_work():
    a = 1
    b = 2
    del a, b
    try:
        a_val = a * 10
    except NameError:
        a_val = None
    try:
        b_val = b * 10
    except NameError:
        b_val = None
    return a_val, b_val


def test_deletes_ignore_names():
    "Test that rewrites ignore non-subscripted del statements"

    actual = regular_deletes_work()

    assert actual == (None, None)


@pyrmute
def delete_by_attr_simple(value):
    a = 1
    del value.foo, a
    try:
        a_val = a * 10
    except NameError:
        a_val = None
    return value, a_val


def test_delete_by_attr():
    "Test del value.foo"

    actual = delete_by_attr_simple(MockClass(foo=33, other=44))

    assert actual == (MockClass(other=44), None)


@pyrmute
def delete_by_attr_complex(value):
    del value.foo.bar
    return value


def test_delete_by_attr_complex():
    "Test del value.foo.bar"

    actual = delete_by_attr_complex(MockClass(foo=MockClass2(bar=33, other=44), other=44))

    assert actual == MockClass(foo=MockClass2(other=44), other=44)


@pyrmute
def delete_by_index(value):
    value.foo = {'this': 'that', 'bar': 'qux'}
    del value.foo['bar']
    return value


def test_delete_by_index():
    "Test del value.foo['bar']"

    actual = delete_by_index(MockClass(foo='yup', other=44))

    assert actual == MockClass(foo=pmap({'this': 'that'}), other=44)
