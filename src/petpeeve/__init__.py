__version__ = '0.0.0.dev0'


import pip
x_y = tuple(int(p) for p in pip.__version__.split('.', 2)[:2])

if x_y < (8, 1):
    raise RuntimeError('pip>=8.1.0 is required')
elif x_y >= (10, 0):
    # Solve a circular import in pip._vendor.requests in pip 10.
    from pip._internal import compat    # noqa
    del compat

del x_y
del pip
