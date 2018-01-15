# Imperative modifications of immutable collections

## Overview

The `pyrsistent-mutable` package presents an import hook that will transform code in `.pyrmut` files into the standard `pyrsistent` API.

This generally means that a set of specific operations are transformed:

    my_precord.attr.attr = 5
    del my_vector[3]
    with_vector.attr.append(20)
    my_map['apple'] = value

_This example is tested in `tests/readme_example.pyrmut`, and invoked in `tests/test_readme.py`._

### What's the point?

It's entirely that the imperative form is easier to read, and that pyrsistent's API is unintuitive for any kind of
nested collections.

Also, I'm working on a language that uses this technique more extensively, so this was an opportunity to turn a
prototype into something more generally useful.

### Installing

Installation should just be:

    pip3 install pyrsistent-mutable
    pip3 install pyrsistent-mutable[debug]  # Add dependencies to enable debugging.
    python3 setup.py install  # If you want to download and install traditionally.

### How do I use it?

Generally, you create a module in the same directory structure as your `.py` modules, but it's named `.pyrmut` instead.

* Modules to be transformed must be named `*.pyrmut` instead of `.py`
* You must install the hook with `import pyrsistent_mutable` before you import your module.
* This probably won't work in zip files, so mark your package as not zip safe.

## Troubleshooting

This is really just trying to take a prototype and do something useful with it.

If a function isn't calling something in a useful manner, the culprit is probably my very lame implementations in
`pyrsistent_mutable.globals`.

### Known limits

Most of these are because I've done very preliminary work to map imperative operations to pyrsistent values

* Assignment of slices uses the evolver framework, which doesn't handle complex slices.
* Deletion of slices similarly doesn't work
* Augmented assignment generally requires a pyrsistent value on the rhs

### Don't forget to `return`

It only munges assignments and expression statements.

### Debugging

The module is pretty careful to do the least possible to patch the import mechanism. I'm not sure if it's kosher to
write out the rewritten files the way I do for the debugging mechanism, so debugging is off by default.

You may need to `touch` the files to the import hook to rerun, but do this:

    from pyrsistent_mutable import set_debug
    print(repr(set_debug(True, True)))
    import your_module  # You don't need the .pyrmut extension.

If that didn't return `(True, True)`, double check that you've got `astunparse` installed. It's included if you install
`pyrsistent-mutable[debug]`.

## Package maintainer notes

For my own notes:

    pip install twine
    python setup.py bdist_whee
    twine upload dist/pyrsistent_mutable-0.0.1-py3-none-any.whl
