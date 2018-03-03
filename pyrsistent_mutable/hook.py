import ast
from contextlib import contextmanager
from importlib.abc import MetaPathFinder
from importlib.machinery import FileFinder, SourceFileLoader
import sys

from astunparse import Printer


class HookLoader(SourceFileLoader):
    write_transformed = False

    def source_to_code(self, data, path, *, _optimize=-1):
        module = ast.parse(data, filename=path)
        module = self.modify_ast(module)
        ast.fix_missing_locations(module)
        if self.write_transformed:
            debug_path = path.with_name(path.stem + '-dump').with_suffix(path.suffix)
            with open(debug_path, 'w') as fh:
                Printer(file=fh).visit(module)
        return super().source_to_code(module, path, _optimize=_optimize)

    def modify_ast(self, module):
        raise NotImplementedError()


class HookPathFinder(MetaPathFinder):
    def __init__(self, loader, extensions, matcher):
        self.cache = {}
        self.loader_class = loader
        self.extensions = list(extensions)
        self.matcher = matcher

    def finder(self, path):
        try:
            return self.cache[path]
        except KeyError:
            finder = self.cache[path] = FileFinder(path, (self.loader_class, self.extensions))
            return finder

    def find_spec(self, fullname, path=None, target=None):
        if path is None:
            path = sys.path
        for one_path in path:
            spec = self.finder(one_path).find_spec(fullname, target)
            if spec is not None and self.matcher(spec):
                return spec
        return None

    def invalidate_caches(self):
        self.cache.clear()


def subclass_hook_loader(modify_ast_func):
    class HookLoaderSub(HookLoader):
        modify_ast = staticmethod(modify_ast_func)

    return HookLoaderSub


def make_meta_hook(modify_ast_func, *extensions, matcher=lambda _: True):
    hook_loader = subclass_hook_loader(modify_ast_func)
    return HookPathFinder(hook_loader, extensions, matcher)


def add_meta_hook(meta_hook):
    sys.meta_path.append(meta_hook)


@contextmanager
def meta_hook_before(hook):
    sys.meta_path.insert(0, hook)
    yield
    sys.meta_path.remove(hook)
