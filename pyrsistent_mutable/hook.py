import ast
from importlib.abc import MetaPathFinder
from importlib.machinery import FileFinder, PathFinder, SourceFileLoader
from os.path import isdir
import sys

try:
    from astunparse import Unparser, Printer
except ImportError:
    Unparser = Printer = None


class HookLoader(SourceFileLoader):
    _debug_dump = False
    _debug_rewrite = False

    def source_to_code(self, data, path, *, _optimize=-1):
        module = ast.parse(data, filename=path)
        module = self.modify_ast(module)
        ast.fix_missing_locations(module)
        if self._debug_dump:
            with open(path + '-dump', 'w') as fh:
                # fh.write(ast.dump(module, False, True))
                Printer(file=fh).visit(module)
        if self._debug_rewrite:
            with open(path + '-rewrite', 'w') as fh:
                Unparser(module, file=fh)
        return super().source_to_code(module, path, _optimize=_optimize)

    def modify_ast(self, module):
        raise NotImplementedError()


class HookPathFinder(MetaPathFinder):
    def __init__(self, loader, extensions):
        self.cache = {}
        self.loader_class = loader
        self.extensions = list(extensions)

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
            if spec is not None:
                return spec
        return None

    def invalidate_caches(self):
        self.cache.clear()


def subclass_hook_loader(modify_ast_func):
    class HookLoaderSub(HookLoader):
        modify_ast = staticmethod(modify_ast_func)

    return HookLoaderSub


def add_path_hook(modify_ast_func, *extensions):
    hook_loader = subclass_hook_loader(modify_ast_func)

    def path_hook(path):
        # None is treated as pwd by bootstrap.
        if path is not None and not isdir(path):
            raise ImportError('only directories are supported, got ' + str(path))
        return FileFinder(path, (hook_loader, *extensions))

    sys.path_hooks.insert(0, path_hook)
    PathFinder.invalidate_caches()


def add_meta_hook(modify_ast_func, *extensions):
    hook_loader = subclass_hook_loader(modify_ast_func)

    sys.meta_path.append(HookPathFinder(hook_loader, extensions))


def set_debug(dump, rewrite):
    '''
    Enable or disable (globally) the printing of an AST dump or the rewrite code.
    Requires that the module was installed as pyrsistent-import-hook[debug] or that astunparse
    is available.
    :param dump: print an AST dump.
    :param rewrite: print the python code being compiled
    :return dump, rewrite: the new values set; may be False if astunparse is unavailable.
    '''
    dump = HookLoader._debug_dump = dump and Printer is not None
    rewrite = HookLoader._debug_rewrite = rewrite and Unparser is not None
    return dump, rewrite
