'''
These functions are used to invoke pyrsistent mutators in a way that fails gracefully when not dealing with
pyrsistent types.
'''
from pyrsistent import PBag, PClass, PDeque, PList, PMap, PSet, PVector

#: A map of method names to types such that the methods are known to return an evolution of the object.
returns_self = {
    'add': (PBag, PSet),
    'append': (PDeque, PVector),
    'appendleft': (PDeque,),
    'cons': (PList,),
    'delete': (PVector,),
    'difference': (PSet,),
    'discard': (PMap, PSet),
    'extend': (PDeque, PVector),
    'extendleft': (PDeque,),
    'intersection': (PSet,),
    'mcons': (PList,),
    'mset': (PVector,),
    'pop': (PDeque,),
    'popleft': (PDeque,),
    'remove': (PBag, PClass, PDeque, PList, PMap, PSet, PVector),
    'reverse': (PDeque, PList),
    'rotate': (PDeque,),
    'set': (PClass, PMap, PVector),
    'symmetric_difference': (PSet,),
    'transform': (PClass, PMap, PVector),
    'union': (PSet,),
    'update': (PBag, PMap, PSet),
    'update_with': (PMap,),
}


def set_via_attr(obj, attr, value):
    """Attempt to set an attribute by evolution, but fall back to ordinary attribute setting."""
    try:
        setter = obj.set
    except AttributeError:
        pass  # Avoid "in this error another error occured" annoyance.
    else:
        return setter(attr, value)
    obj.attr = value
    return obj


def set_via_slice(obj, index, value):
    """Attempt to set a slice by evolution, but fall back to ordinary setitem."""
    try:
        evolver = obj.evolver
    except AttributeError:
        pass
    else:
        evolver = evolver()
        evolver[index] = value
        return evolver.persistent()
    obj[index] = value
    return obj


def del_attr(obj, attr):
    """Attempt to delete an attribute by evolution, but fall back to ordinary del attr."""
    try:
        evolver = obj.evolver
    except AttributeError:
        pass
    else:
        evolver = evolver()
        delattr(evolver, attr)
        return evolver.persistent()
    delattr(obj, attr)
    return obj


def del_slice(obj, index):
    """Attempt to delete keys by evolution, but fall back to ordinary delitem."""
    try:
        evolver = obj.evolver
    except AttributeError:
        pass
    else:
        evolver = evolver()
        del evolver[index]
        return evolver.persistent()
    del obj[index]
    return obj


def invoke(obj, method, *args, **kw):
    '''
    Invokes a method with the arguments and returns the result, or the original object.
    '''
    result = getattr(obj, method)(*args, **kw)
    if isinstance(obj, returns_self.get(method, ())):
        return result
    else:
        return obj
