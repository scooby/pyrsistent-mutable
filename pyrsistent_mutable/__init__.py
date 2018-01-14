from .hook import add_meta_hook
from .rewrite import rewrite


# Importing this module adds the necessary hook for .pyrmute files.
add_meta_hook(rewrite, '.pyrmute')
