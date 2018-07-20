import importlib
import sys

from pip._vendor import six


def from_pip_import(path, attr=None, prepath=None):
    """This encapsulate pip imports between the introduction of pip._internal.
    """
    try:
        module = importlib.import_module('pip._internal.' + path)
    except ImportError:
        exc_info = sys.exc_info()
        try:
            module = importlib.import_module('pip.' + (prepath or path))
        except ImportError:
            six.reraise(*exc_info)  # The pip 10 exception is better.
    if not attr:
        return module
    try:
        return getattr(module, attr)
    except AttributeError:
        raise ImportError('cannot import name {!r}'.format(attr))
