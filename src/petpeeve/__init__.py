__version__ = '0.0.0.dev0'


import pip
major = int(pip.__version__.split('.')[0])

if major < 9:
    raise RuntimeError('pip>=9.0.0 is required')
elif major >= 10:
    # Solve a circular import in pip._vendor.requests in pip 10.
    from pip._internal import compat    # noqa
    del compat

del major
del pip
