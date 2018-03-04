from pyrsistent_mutable import pyrmute


@pyrmute
def dict_comprehension(m):
    local = {v: k for k, v in m.items()}
    del local['d']
    local['e'] = 'f'
    return local


@pyrmute
def set_literal():
    local = {1, 2, 2, 3}
    local |= {3, 4, 5}
    return local


def set_literal_not_translated():
    return {1, 2}


@pyrmute
def set_comprehension(m):
    local = {n // 10 for n in m}
    local |= {40, 50, 60}
    return local
