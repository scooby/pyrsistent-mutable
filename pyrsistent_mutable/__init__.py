from .hook import add_meta_hook, set_debug
from .rewrite import rewrite


EXTENSION = '.pyrmut'

# Importing this module adds the necessary hook for .pyrmute files.
add_meta_hook(rewrite, EXTENSION)
