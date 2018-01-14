from ast import (
    Assign, Attribute, BinOp, Call, Delete, ImportFrom, Load, Name, NameConstant, NodeTransformer, NodeVisitor,
    Store, Str, Subscript, Tuple, alias, copy_location, iter_fields, fix_missing_locations
)
from collections import defaultdict
from copy import deepcopy


def rewrite(module):
    with Names(module) as imports:
        RewriteAssignments(imports).visit(module)
    return fix_missing_locations(module)


def match_ast(pattern, node):
    '''
    Matches a node against a pattern and returns the values of placeholders.
    :param pattern: An AST node with child nodes or strings as placeholders.
    :param node: The node to match against.
    :return: A dictionary of placeholders with values seen, or None to indicate a failure.
    '''
    if isinstance(pattern, set) and len(pattern) == 1:
        return {next(iter(pattern)): node}

    if not isinstance(node, type(pattern)):
        return None

    if isinstance(pattern, list):
        if len(pattern) != len(node):
            return None
        result = {}
        for pelem, nelem in zip(pattern, node):
            found = match_ast(pelem, nelem)
            if found is None:
                return None
            result.update(found)
        return result

    result = {}
    for field, expect in iter_fields(pattern):
        found = getattr(node, field, None)
        found = match_ast(expect, found)
        if found is None:
            return None
        result.update(found)

    return result


class NamesInUse(NodeVisitor):
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
    Generates unique names for locals and imports.
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
        if len(parts) < 2:
            raise TypeError('Expect at least two parts to a fully qualified name.')
        if parts in self.imports:
            return self.imports[parts]
        name = self.unique(parts[-1])
        self.imports[parts] = name
        return name

    def unique(self, part):
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


class _NodeTransformer(NodeTransformer):
    @classmethod
    def go(cls, node):
        node = deepcopy(node)
        cls().visit(node)
        return node


class Context(NodeTransformer):
    def __init__(self, ctx):
        self._ctx = ctx

    @classmethod
    def set(cls, ctx, node):
        node = deepcopy(node)
        cls(ctx).visit(node)
        return node

    def visit_AugLoad(self, _):
        return self._ctx()

    def visit_AugStore(self, _):
        return self._ctx()

    def visit_Del(self, _):
        return self._ctx()

    def visit_Store(self, _):
        return self._ctx()

    def visit_Load(self, _):
        return self._ctx()

    def visit_Param(self, _):
        return self._ctx()


class Deslicify(_NodeTransformer):
    def visit_Index(self, node):
        return self.generic_visit(node.value)

    def visit_ExtSlice(self, node):
        elems = map(self.generic_visit, node.dims)
        return Tuple(elts=list(elems), ctx=Load())

    _slice = Attribute(value=Name(id='__builtins__', ctx=Load()), attr='slice', ctx=Load())

    def visit_Slice(self, node):
        def visit(what):
            if what is None:
                return NameConstant(None)
            else:
                return self.generic_visit(what)

        call = Call(func=self._slice, args=[visit(node.lower), visit(node.upper), visit(node.step)], keywords=[])
        return copy_location(call, node)


class RewriteAssignments(NodeTransformer):
    def __init__(self, names):
        self.names = names

    def call_global(self, name, args, keywords=None, src=None):
        func = Name(id=self.names.dotted('pyrsistent_mutable', 'globals', name), ctx=Load())
        if keywords is None:
            keywords = []
        call = Call(func=func, args=args, keywords=keywords)
        if src is not None:
            copy_location(call, src)
        return call

    def visit_AugAssign(self, node):
        node = copy_location(Assign(
            targets=[Context.set(Store, node.target)],
            value=BinOp(
                left=Context.set(Load, node.target),
                op=node.op,
                right=node.value
            )
        ), node)
        return self.visit_Assign(node)

    def visit_Assign(self, node):
        def set_attr(lhs, attr, rhs):
            return self.call_global('set_via_attr', [Context.set(Load, lhs), Str(s=attr), rhs])

        def set_sub(lhs, sub, rhs):
            return self.call_global('set_via_slice', [Context.set(Load, lhs), Deslicify.go(sub), rhs])

        def destructure(lhs, rhs):
            if isinstance(lhs, Attribute):
                return destructure(lhs.value, set_attr(lhs.value, lhs.attr, rhs))
            elif isinstance(lhs, Subscript):
                return destructure(lhs.value, set_sub(lhs.value, lhs.slice, rhs))
            else:
                return lhs, rhs

        out = []
        for target in node.targets:
            lhs, rhs = destructure(target, node.value)
            copy_location(lhs, target)
            copy_location(rhs, node.value)
            assign = copy_location(Assign(targets=[lhs], value=rhs), node)
            out.append(assign)
        return out

    _method_pattern = Call(
        func=Attribute(
            value={'subject'},
            attr={'method'},
            ctx=Load()
        ), args={'arguments'},
        keywords={'keywords'}
    )

    def visit_Expr(self, node):
        # Rewrite foo.append(...) as foo = invoke(foo, 'append', ...)
        d = match_ast(self._method_pattern, node)
        if d is None:
            return self.generic_visit(node)
        out = []
        subject = d['subject']
        if not isinstance(subject, Name):
            # For something more complex than a simple name, assign to a local to avoid side-effects
            rename = self.names.unique()
            out.append(copy_location(Assign(targets=[Name(id=rename, ctx=Store())], value=subject), node))
            subject = copy_location(Name(id=rename, ctx=Load()), subject)
        args = [subject, Str(s=d['method'])] + d['arguments']
        assign = Assign(targets=[Context.set(Store, subject)],
                        value=self.call_global('invoke', args, d['keywords']))
        out.append(copy_location(assign, node))
        return out

    def visit_Delete(self, node):
        out = []
        unchanged = []

        def clear_unchanged():
            if unchanged:
                out.append(copy_location(Delete(targets=unchanged), node))
                del unchanged[:]

        def change(func, subject, tail, target):
            value = self.call_global(func, [Context.set(Load, subject), tail], src=target)
            stmt = copy_location(Assign(targets=[Context.set(Store, subject)], value=value), target)
            clear_unchanged()
            out.append(stmt)

        for target in node.targets:
            if isinstance(target, Attribute):
                change('del_attr', target.value, Str(s=target.attr), target)
            elif isinstance(target, Subscript):
                change('del_slice', target.value, Deslicify.go(target.slice), target)
            else:
                unchanged.append(target)

        clear_unchanged()
        return out
