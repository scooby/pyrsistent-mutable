from pyrsistent_mutable.hook import make_meta_hook
from pyrsistent_mutable.rewrite import rewrite

rewrite_hook = make_meta_hook(rewrite, '.pyrmut')
