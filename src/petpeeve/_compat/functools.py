from __future__ import absolute_import

import functools


try:
    lru_cache = functools.lru_cache
except AttributeError:
    def lru_cache(maxsize=None):    # Noop.
        def _decorator(f):
            return f
        return _decorator
