from ast import (
    Assign, Attribute, BinOp, Delete, Dict, DictComp, Expr, ImportFrom, Load, Name,
    NodeTransformer, NodeVisitor, Store, Str, Subscript, alias, copy_location as cl, fix_missing_locations as fml
)
from collections import defaultdict

from pyrsistent_mutable.ast6 import match_ast, Context, deslicify, Cap
from .ast6 import call6

from pyrsistent import pmap, pset, pvector
from pyrsistent_mutable import globals


def rewrite(module):
    with Names(module) as imports:
        RewriteAssignments(imports).visit(module)
    return fml(module)


class NamesInUse(NodeVisitor):
    """
    Identifies names in use within an AST to ensure transformations are hygenic.

    The use case for this is to be able to synthesize global names without collisions, so it's
    very dumb (and hopefully robust as a result) and doesn't know where names are actually in
    scope.
    """
    def __init__(self):
        self.names = set()

    def visit_Name(self, node):
        self.names.add(node.id)

    def visit_alias(self, node):
        self.names.add(node.asname or (node.name.split('.')[0]))

    def visit_AsyncFunctionDef(self, node):
        self.names.add(node.name)

    def visit_ClassDef(self, node):
        self.names.add(node.name)

    def visit_FunctionDef(self, node):
        self.names.add(node.name)


class Names:
    '''
    A context manager that generates unique names for locals and imports, and can
    add the import statements on exit.
    '''
    def __init__(self, module, prefix='_'):
        self.module = module
        self.imports = {}
        self.prefix = prefix

    def __enter__(self):
        niu = NamesInUse()
        niu.visit(self.module)
        self.names = niu.names
        return self

    def dotted(self, *parts):
        '''
        Import a global name and give it a unique name within this module.
        :param parts: Either the parts of the dotted name, or a callable.
        :return: a unique name referencing the global name.
        '''
        if len(parts) == 1 and hasattr(parts[0], '__name__'):
            parts = name_of(parts[0])
        if len(parts) < 2:
            raise TypeError('Expect at least two parts to a fully qualified name.')
        if parts in self.imports:
            return self.imports[parts]
        name = self.unique(parts[-1])
        self.imports[parts] = name
        return name

    def unique(self, part):
        '''
        Get a unique local or global name within this context given part of a name.
        :param part: A name that is suggestive of the actual name, to make reading the transformed source easier.
        :return: The unique name.
        '''
        prefix = self.prefix
        name = prefix + str(part)
        counter = 0
        while True:
            if name not in self.names:
                self.names.add(name)
                return name
            name = prefix + str(part) + str(counter)
            counter += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            return
        modules = defaultdict(list)
        for parts, name in self.imports.items():
            modules[parts[:-1]].append((parts[-1], name))
        stmts = []
        for mod, aliases in sorted(modules.items()):
            aliases = [alias(name=name, asname=asname)
                       for name, asname in sorted(aliases)]
            stmts.append(ImportFrom(module='.'.join(mod), names=aliases,
                                    lineno=1, col_offset=0, level=0))
        self.module.body[0:0] = stmts

    def call_global(self, name, args, keywords=None, src=None):
        '''
        Import and call a function we're providing to the rewritten module.
        :param name: Either a tuple of the name parts or a function to get its name.
        :param args: A list of positional arguments.
        :param keywords: A dictionary of keyword arguments.
        :param src: A source node to copy the location of this call from.
        :return: The AST node calling the function as requested.
        '''
        func = Name(id=self.dotted(name), ctx=Load())
        if keywords is None:
            keywords = []
        call = call6(func=func, args=args, keywords=keywords)
        if src is not None:
            cl(call, src)
        return call


def name_of(func):
    parts = func.__module__.split('.')
    parts.append(func.__name__)
    return tuple(parts)


_slice = Attribute(value=Name(id='__builtins__', ctx=Load()), attr='slice', ctx=Load())


class RewriteAssignments(NodeTransformer):
    '''
    The main transformer, this converts assignments and literals. See methods for details.
    '''
    def __init__(self, names):
        self.names = names

    def visit_AugAssign(self, node):
        '''
        Rewrite augmented assignment as regular assignment.

        TODO: This degrades all augmented assignment which is not what we want.
        :param node: An AugAssign node.
        :return: The same node transformed into a regular assignment.
        '''
        node = cl(Assign(
            targets=[Context.set(Store, node.target)],
            value=BinOp(
                left=Context.set(Load, node.target),
                op=node.op,
                right=self.visit(node.value)
            )
        ), node)
        return self.visit_Assign(node)

    def visit_Assign(self, node):
        '''
        Rewrite attribute and slice assignment as invocations of functions that can
        attempt evolution.

        Say we read the left-hand side of an assignment as AST:

            name.attr1.attr2 = new_value

            Attr(Attr(Name('name'), 'attr1'), 'attr2')

        The destructuring enforces these productions:

            destruct(Attr(VALUE, ATTR), RHS) -> destructure(VALUE, set_attr(VALUE, ATTR, RHS))
            destruct(LHS, RHS) -> LHS, RHS

        So we our example is effectively rewriting via these steps:

            destruct(name.attr1.attr2, new_value)
                destruct(name.attr1, setattr(name.attr1, 'attr2', new_value))
                    destruct(name, setattr(name, 'attr1', setattr(name.attr1, 'attr2', new_value)))
                        Done.

        :param node: An assignment node.
        :return: A destructured assignment.
        '''
        def set_attr(lhs, attr, rhs):
            return self.names.call_global(globals.set_via_attr,
                                          [Context.set(Load, lhs), Str(s=attr), rhs],
                                          src=node)

        def set_sub(lhs, sub, rhs):
            return self.names.call_global(globals.set_via_slice,
                                          [Context.set(Load, lhs), deslicify(sub), rhs],
                                          src=node)

        def destructure(lhs, rhs):
            if isinstance(lhs, Attribute):
                return destructure(lhs.value, set_attr(lhs.value, lhs.attr, rhs))
            elif isinstance(lhs, Subscript):
                return destructure(lhs.value, set_sub(lhs.value, lhs.slice, rhs))
            else:
                return lhs, rhs

        out = []
        node_val = self.visit(node.value)
        for target in node.targets:
            lhs, rhs = destructure(target, node_val)
            cl(lhs, target)
            cl(rhs, node_val)
            assign = cl(Assign(targets=[Context.set(Store, lhs)], value=rhs), node)
            out.append(assign)
        return out

    #: A pattern to match a method call.
    _method_pattern = call6(
        func=Attribute(
            value=Cap('subject'),
            attr=Cap('method'),
            ctx=Load()
        ), args=Cap('arguments'),
        keywords=Cap('keywords')
    )

    def visit_Expr(self, node):
        '''Rewrite foo.append(...) as foo = invoke(foo, 'append', ...).

        This depends on the `invoke` method simply knowing which method invocations ought to be saved, thus this is
        tightly coupled to the pyrsistent API.
        '''
        match = match_ast(self._method_pattern, self.visit(node.value))
        if match is None:
            return cl(Expr(value=self.visit(node.value)), node)
        subject = match['subject']
        args = [subject, Str(s=match['method'])] + match['arguments']
        assign = Assign(targets=[Context.set(Store, subject)],
                        value=self.names.call_global(globals.invoke, args, match['keywords']))
        return self.visit_Assign(cl(assign, node))

    def visit_Delete(self, node):
        '''
        Rewrites a delete using an evolver.
        '''
        out = []
        unchanged = []

        def clear_unchanged():
            if unchanged:
                out.append(cl(Delete(targets=list(unchanged)), node))
                del unchanged[:]

        def change(func, subject, tail, target):
            clear_unchanged()
            value = self.names.call_global(func, [Context.set(Load, subject), tail], src=target)
            stmts = self.visit_Assign(cl(Assign(targets=[Context.set(Store, subject)], value=value), target))
            out.extend(stmts)

        for target in node.targets:
            if isinstance(target, Attribute):
                change(globals.del_attr, target.value, Str(s=target.attr), target)
            elif isinstance(target, Subscript):
                change(globals.del_slice, target.value, deslicify(target.slice), target)
            else:
                unchanged.append(target)

        clear_unchanged()
        return out

    def literal(self, node, con):
        '''Wrap a literal node with a call to the appropriate global constructor.'''
        return self.names.call_global(con, [self.generic_visit(node)], src=node)

    def visit_Dict(self, node):
        return self.literal(node, pmap)

    def visit_DictComp(self, node):
        return self.literal(node, pmap)

    def visit_List(self, node):
        return self.literal(node, pvector)

    def visit_ListComp(self, node):
        return self.literal(node, pvector)

    def visit_Set(self, node):
        return self.literal(node, pset)

    def visit_SetComp(self, node):
        return self.literal(node, pset)

    def visit_keyword(self, node):
        '''
        Prevent transforming a literal dictionary in a splat to a `pmap`.

        Rationale: in a function call like ``foo(**{...})`` we should not transform the dictionary.
        '''
        if node.arg is None and isinstance(node.value, (Dict, DictComp)):
            # When arg is None, it's a `**` construct.
            node.value = self.generic_visit(node.value)
            return node
        else:
            return self.generic_visit(node)
