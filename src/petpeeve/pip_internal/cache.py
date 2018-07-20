__all__ = ['SimpleWheelCache']

import sys

from pip._vendor import six

from ._not import from_pip_import

try:
    SimpleWheelCache = from_pip_import('cache', 'SimpleWheelCache')
except ImportError:     # Even older versions.
    exc_info = sys.exc_info()
    try:
        from pip.wheel import WheelCache, _cache_for_link
    except ImportError:
        six.reraise(*exc_info)
    class SimpleWheelCache(WheelCache):     # noqa
        def get_path_for_link(self, link):
            return _cache_for_link(self._cache_dir, link)
