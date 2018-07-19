import importlib
import sys

from pip._vendor import six


def from_pip_import(path, attr=None, pre10_path=None):
    """This encapsulate pip internal imports between 10 (new) and 9 (old).
    """
    try:
        module = importlib.import_module('pip._internal.' + path)
    except ImportError:
        exc_info = sys.exc_info()
        try:
            module = importlib.import_module('pip.' + (pre10_path or path))
        except ImportError:
            six.reraise(*exc_info)  # The pip 10 exception is better.
    if not attr:
        return module
    try:
        return getattr(module, attr)
    except AttributeError:
        raise ImportError('cannot import name {!r}'.format(attr))
