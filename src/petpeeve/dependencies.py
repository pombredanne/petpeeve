import collections

from pip._vendor.packaging.markers import Marker
from pip._vendor.packaging.requirements import Requirement


def _add_requirements(entry, reqlist):
    try:
        requires = entry['requires']
    except KeyError:
        return reqlist
    req_iter = (Requirement(s) for s in requires)
    environment = entry.get('environment')
    if environment:
        requirements = list(req_iter)
        for r in requirements:
            if r.marker:
                m = Marker('({}) and ({})'.format(environment, r.marker))
            else:
                m = Marker(environment)
            r.marker = m
        req_iter = iter(requirements)
    reqlist.extend(req_iter)
    return reqlist


class DependencySet(object):
    """A representation of dependencies of a package.

    This representation is abstract, i.e. completely independent from the
    execution environment. Our resolver needs this to give a machine-agnostic
    dependency tree.
    """
    def __init__(self, base, extras):
        self.base = base
        self.extras = extras

    @classmethod
    def from_wheel(cls, wheel):
        """Build a dependency set from a wheel.

        `wheel` is a `distlib.wheel.Wheel` instance. The metadata is read to
        build the instance.
        """
        base = []
        extras = collections.defaultdict(list)
        for entry in wheel.metadata.run_requires:
            if 'extra' in entry:
                name = entry['extra']
                extras[name] = _add_requirements(entry, extras[name])
                continue
            if list(entry.keys()) == ['requires']:
                base = _add_requirements(entry, base)
                continue
        return cls(base, extras)
