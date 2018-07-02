# Solve a circular import in pip._vendor.requests in pip 10.
try:
    from pip._internal import compat
    del compat
except ImportError:
    pass
