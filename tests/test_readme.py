import pyrsistent_mutable as pm
pm.set_debug(True, True)

from tests.readme_example import example_func, Simple
from pyrsistent import pvector, pmap


def test_validate_readme():
    "Test that the example shown in the readme actually works."
    # Test
    my_precord, my_vector, with_vector, my_map = example_func()

    # Verification
    assert my_precord == Simple(attr=Simple(attr=5, other=11), other=22)
    assert my_vector == pvector([0, 10, 20, 40, 50])
    assert with_vector == Simple(attr=pvector([1, 2, 3, 20]), other=33)
    assert my_map == pmap({'other': 'value', 'apple': 'banana'})
