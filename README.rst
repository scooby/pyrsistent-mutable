Imperative modifications of immutable collections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Overview
========

The `pyrsistent-mutable` package presents a decorator that will transform a decorated function to use the
`pyrsistent <https://pypi.python.org/pypi/pyrsistent>`_ API.

This means that a set of specific operations are transformed:

* Construction of literal ``set``\s, ``dict``\s and ``list``\s are transformed into calls to ``pset``\, ``pvector``
  and ``pmap``\.
* Assignments are rewritten to handle:
    * Assignments to attributes become evolve calls; nesting is handled correctly.
    * Augmented assignments are transformed into regular assignments.
* Standalone method invocations are transformed into assignments.

.. code-block:: python

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
        my_map = {key: {} for key in ('apple', 'banana')}
        my_map['apple']['pie'] = 'tasty'

        return my_vector, save_vector, my_precord, my_map

*This example is tested in ``tests/test_readme.py``\.*

What's the point?
-----------------

It's entirely that the imperative form is easier to read, and that pyrsistent's API is tedious for nested collections,
at least compared to native Python syntax.

Also, I'm working on a language that uses this technique more extensively, so this was an opportunity to turn a
prototype into something more generally useful.

Installing
----------

Installation should just be:

.. code-block:: bash

    # Install via pip, preferred.
    pip3 install pyrsistent-mutable

    # Install traditionally.
    python3 setup.py install

Usage
-----

Beyond the example shown above, the main things to keep in mind when using this module:

* You function still needs to return values.
* A "copy" can be made by simple assignment.
* Lists, dicts and sets literals and comprehensions are transformed.
* Tuples are *not* transformed, nor are generators.
* Method calls are *only* transformed if they are standalone expressions.
* Rewritten operations should fall back to normal behavior for non-`pyrsistent` values.
* The decorated function can't allow ``nonlocal`` names.
* ``global`` may not work.

Troubleshooting
===============

This is really just trying to take a prototype and do something useful with it.

If a function isn't calling something in a useful manner, the culprit is probably my very lame implementations in
``pyrsistent_mutable.globals``.

Don't forget to ``return``
--------------------------

This only munges assignments and expression statements.

Read the ``__source__``
-----------------------

The transformed code is written into your function under ``__source__``\, and may be helpful in debugging.

Known limits
------------

Most of these are because I've only done very preliminary work to map imperative operations to pyrsistent values.

* Assignment of slices uses the evolver framework, which doesn't handle complex slices.
* Deletion of slices similarly doesn't work.
* Augmented assignment generally requires a pyrsistent value on the rhs.
    * This is mitigated now that the module translates literals.
* It is not tested on asynchronous functions or generators. It shouldn't care about them, though.
* It's all or nothing.
* The top level function can't have ``nonlocal`` names. Embedded functions can, though.

Debugging
---------

By default, the decorator will write the transformed source to your function as ``__source__``\. I just pulled that name
out my hat. You can call the decorator with ``write_source=False`` to disable this.

Using an import hook
====================

I originally wrote this as an import hook. This works, and most of the tests are still using it, but it requires
a separate file extension, and to let it see ``.py`` files means either inspecting *all* files for decorators or
registering certain modules. Either way, patching the import mechanism is not great, so this uses ``inspect.getsource``
and reparses entirely.

The hook is pretty careful to do the least possible to patch the import mechanism. I'm not sure if it's kosher to
write out the rewritten files the way I do for the debugging mechanism, so debugging is off by default.

You may need to ``touch`` the files for the import hook to rerun, but this is how the tests set it up:

.. code-block:: python

    from pyrsistent_mutable.hook import make_meta_hook
    from pyrsistent_mutable.rewrite import rewrite

    rewrite_hook = make_meta_hook(rewrite, '.pyrmut')
    rewrite_hook.write_transformed = True

Notes on using it
-----------------

Generally, you create a module in the same directory structure as your ``.py`` modules, but it's named ``.pyrmut``
instead.

* Modules to be transformed must be named ``*.pyrmut`` instead of ``.py``
* You must install the hook with ``import pyrsistent_mutable`` before you import your module.
* This probably won't work in zip files, so mark your package as not zip safe.
* It does take a ``matcher`` argument if you want to use ``.py`` and select files.

Package maintainer notes
========================

.. code-block:: bash

    pip install twine
    python setup.py bdist_wheel
    twine upload dist/pyrsistent_mutable-0.0.x-py3-none-any.whl
