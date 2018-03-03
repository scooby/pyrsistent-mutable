from pyrsistent_mutable import pyrmute

from pyrsistent import PRecord, field, pvector, pmap


class Simple(PRecord):
    attr = field()
    other = field()


@pyrmute
def example_func():
    my_precord = Simple(attr=Simple(attr=10, other=11), other=22)
    my_vector = [0, 10, 20, 30, 40, 50]
    with_vector = Simple(attr=[1, 2, 3], other=33)
    my_map = {'other': 'value'}
    value = 'banana'

    my_precord.attr.attr = 5
    del my_vector[3]
    with_vector.attr.append(20)
    my_map['apple'] = value

    return my_precord, my_vector, with_vector, my_map


def test_validate_readme():
    "Test that the example shown in the readme actually works."

    # Test
    my_precord, my_vector, with_vector, my_map = example_func()

    # Verification
    assert my_precord == Simple(attr=Simple(attr=5, other=11), other=22)
    assert my_vector == pvector([0, 10, 20, 40, 50])
    assert with_vector == Simple(attr=pvector([1, 2, 3, 20]), other=33)
    assert my_map == pmap({'other': 'value', 'apple': 'banana'})
