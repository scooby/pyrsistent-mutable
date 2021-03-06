from pyrsistent_mutable import pyrmute
from pyrsistent import PRecord, field


class Simple(PRecord):
    attr = field()
    other = field()


@pyrmute
def example_func():
    # Built in referential integrity
    save_vector = my_vector = [0, 1, 2, 3, 4]  # Mapped to a pvector
    del my_vector[3]  # Does *not* change save_vector

    # Evolve nested attributes
    my_precord = Simple(attr=Simple(), other=[])
    my_precord.attr.attr = 5
    my_precord.other.append(20)

    # Transforms literals and comprehensions
    my_maps = [{'filling': key} for key in ('apple', 'banana')]
    my_maps[0]['crust'] = 'flaky'

    return my_vector, save_vector, my_precord, my_maps


def test_validate_readme():
    "Test that the example shown in the readme actually works."

    # Import locally so we can copypasta the README.
    from pyrsistent import pvector, pmap, PVector

    # Test
    my_vector, save_vector, my_precord, my_maps = example_func()

    # Verification
    assert my_vector == pvector([0, 1, 2, 4])
    assert isinstance(my_vector, PVector)
    assert save_vector == pvector([0, 1, 2, 3, 4])
    assert my_precord == Simple(attr=Simple(attr=5), other=pvector([20]))
    assert my_maps == pvector([pmap({'filling': 'apple', 'crust': 'flaky'}),
                               pmap({'filling': 'banana'})])
