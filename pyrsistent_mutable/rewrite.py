from ast import (
    AST, Assign, Attribute, BinOp, Call, Delete, Expr, ExtSlice, ImportFrom, Index, Load, Name, NameConstant,
    NodeTransformer, NodeVisitor, Slice, Store, Str, Subscript, Tuple, alias, copy_location as cl, dump,
    fix_missing_locations as fml, iter_fields
)
from collections import defaultdict
from copy import deepcopy

from pyrsistent import plist


def rewrite(module):
    with Names(module) as imports:
        RewriteAssignments(imports).visit(module)
    return fml(module)


def scan(node, path=plist()):
    if isinstance(node, list):
        for elem in node:
            yield from scan(elem, path)
    elif isinstance(node, AST):
        yield node, path
        for name, value in iter_fields(node):
            yield from scan(value, path.cons(node))
    else:
        yield node, path


def match_ast(pattern, node):
    '''
    Matches a node against a pattern and returns the values of placeholders.
    :param pattern: An AST node with child nodes or strings as placeholders.
    :param node: The node to match against.
    :return: A dictionary of placeholders with values seen, or None to indicate a failure.
    '''
    # print(f'{ast_repr(pattern)}  --vs--  {ast_repr(node)}')

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

    if isinstance(pattern, AST):
        result = {}
        for field, expect in iter_fields(pattern):
            found = getattr(node, field, None)
            found = match_ast(expect, found)
            if found is None:
                return None
            result.update(found)
        return result

    if pattern == node:
        return {}
    else:
        return None


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


_slice = Attribute(value=Name(id='__builtins__', ctx=Load()), attr='slice', ctx=Load())


def deslicify(subscript):
    def fix_none(node):
        if node is None:
            return cl(NameConstant(None), subscript)
        else:
            return node

    def fix_slice(node):
        if isinstance(node, Slice):
            return cl(Call(func=_slice, args=[fix_none(node.lower), fix_none(node.upper), fix_none(node.step)],
                           keywords=[]), node)
        else:
            return fix_none(node)

    if isinstance(subscript, Index):
        return subscript.value
    elif isinstance(subscript, ExtSlice):
        elems = map(fix_slice, subscript.dims)
        return cl(Tuple(elts=list(elems), ctx=Load()), subscript)
    elif isinstance(subscript, Slice):
        return cl(fix_slice(subscript), subscript)
    else:
        raise TypeError(f'Expected {dump(subscript)} to be a subscript expression.')


class RewriteAssignments(NodeTransformer):
    def __init__(self, names):
        self.names = names

    def call_global(self, name, args, keywords=None, src=None):
        func = Name(id=self.names.dotted('pyrsistent_mutable', 'globals', name), ctx=Load())
        if keywords is None:
            keywords = []
        call = Call(func=func, args=args, keywords=keywords)
        if src is not None:
            cl(call, src)
        return call

    def visit_AugAssign(self, node):
        node = cl(Assign(
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
            return self.call_global('set_via_attr', [Context.set(Load, lhs), Str(s=attr), rhs], src=node)

        def set_sub(lhs, sub, rhs):
            return self.call_global('set_via_slice', [Context.set(Load, lhs), deslicify(sub), rhs], src=node)

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
            cl(lhs, target)
            cl(rhs, node.value)
            assign = cl(Assign(targets=[Context.set(Store, lhs)], value=rhs), node)
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
        d = match_ast(self._method_pattern, node.value)
        if d is None:
            return cl(Expr(value=self.generic_visit(node.value)), node)
        subject = d['subject']
        args = [subject, Str(s=d['method'])] + d['arguments']
        assign = Assign(targets=[Context.set(Store, subject)],
                        value=self.call_global('invoke', args, d['keywords']))
        return self.visit_Assign(cl(assign, node))

    def visit_Delete(self, node):
        out = []
        unchanged = []

        def clear_unchanged():
            nonlocal out, unchanged
            if unchanged:
                out.append(cl(Delete(targets=list(unchanged)), node))
                del unchanged[:]

        def change(func, subject, tail, target):
            nonlocal out
            clear_unchanged()
            value = self.call_global(func, [Context.set(Load, subject), tail], src=target)
            stmts = self.visit_Assign(cl(Assign(targets=[Context.set(Store, subject)], value=value), target))
            out.extend(stmts)

        for target in node.targets:
            if isinstance(target, Attribute):
                change('del_attr', target.value, Str(s=target.attr), target)
            elif isinstance(target, Subscript):
                change('del_slice', target.value, deslicify(target.slice), target)
            else:
                unchanged.append(target)

        clear_unchanged()
        return out
