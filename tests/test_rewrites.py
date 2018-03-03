from pyrsistent import PRecord, field, pset, pvector

from tests import rewrite_hook
from pyrsistent_mutable.hook import meta_hook_before


def test_aug_assign_plus():
    with meta_hook_before(rewrite_hook):
        import tests.aug_assign as test_mod

    left = pvector([1, 2, 3])
    right = pvector([10, 20, 30])

    actual = test_mod.plus(left, right)

    assert actual == pvector([1, 2, 3, 10, 20, 30])


def test_aug_assign_union():
    with meta_hook_before(rewrite_hook):
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
    with meta_hook_before(rewrite_hook):
        from tests.assign import simple_attr_assign

    value = MockClass(foo=7, other=33)
    actual = simple_attr_assign(value)

    assert actual == MockClass(foo=10, other=33)


def test_complex_attr_assign():
    with meta_hook_before(rewrite_hook):
        from tests.assign import complex_attr_assign

    value = MockClass(foo=MockClass2(bar=MockClass3(qux=7, other=11), other=22), other=33)
    actual = complex_attr_assign(value)

    assert actual == MockClass(foo=MockClass2(bar=MockClass3(qux=20, other=11), other=22), other=33)


def test_simple_index_assign():
    with meta_hook_before(rewrite_hook):
        from tests.assign import simple_index_assign

    value = MockClass(foo=7, other=33)
    actual = simple_index_assign(value)

    assert actual == MockClass(foo=30, other=33)


def test_complex_index_assign():
    with meta_hook_before(rewrite_hook):
        from tests.assign import complex_index_assign

    value = MockClass(foo=MockClass2(bar=MockClass3(qux=7, other=11), other=22), other=33)
    actual = complex_index_assign(value)

    assert actual == MockClass(foo=MockClass2(bar=MockClass3(qux=40, other=11), other=22), other=33)


def test_simple_method():
    with meta_hook_before(rewrite_hook):
        from tests.method import simple_invoke

    value = pvector([1, 2, 3])
    actual = simple_invoke(value)

    assert actual == pvector([1, 2, 3, 20])


def test_complex_method():
    with meta_hook_before(rewrite_hook):
        from tests.method import complex_invoke

    value = MockClass(foo=pvector([1, 2, 3]), other=44)
    actual = complex_invoke(value)

    assert actual == MockClass(foo=pvector([1, 2, 3, 20, 30, 40]), other=44)


def test_deletes_ignore_names():
    with meta_hook_before(rewrite_hook):
        from tests.delete import regular_deletes_work

    actual = regular_deletes_work()

    assert actual == (None, None)
