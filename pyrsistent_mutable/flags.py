import __future__ as future
import sys


def find_optional_features():
    '''
    Scan for compile flags that are optional in the current version of Python.

    But just use the global ``optional_features`` rather than calling this.
    :return: yields optional feature names
    '''
    current = sys.version_info
    for name in future.all_feature_names:
        feature = getattr(future, name)
        if current < feature.mandatory:
            yield name


#: Names of ``from __future__ import feature`` statements that affect compilation.
optional_features = frozenset(find_optional_features())


def get_flags(module):
    '''
    This does some very limited work to inspect a loaded module and determine the compiler flags
    set by ``from __future__ import Feature``. In particular, if a __future__ import is overridden
    by another definition, this will not detect it.
    :param module: A compiled module.
    :return: A value suitable to be passed to `flags` in the builtin ``compile`` function.
    '''
    mod = vars(module)
    accum = 0
    for name in mod.keys() & optional_features:
        feat = mod[name]
        # noinspection PyProtectedMember
        if feat.__class__ == future._Feature:
            accum |= feat.compiler_flag
    return accum
