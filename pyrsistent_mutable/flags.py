import __future__ as future
import sys


def features():
    current = sys.version_info
    for name in future.all_feature_names:
        feature = getattr(future, name)
        if current < feature.mandatory:
            yield name


# Find the names of features that aren't already mandatory.
_optional = frozenset(features())


def get_flags(module):
    mod = vars(module)
    accum = 0
    for name in mod.keys() & _optional:
        feat = mod[name]
        # noinspection PyProtectedMember
        if feat.__class__ == future._Feature:
            accum |= feat.compiler_flag
    return accum
