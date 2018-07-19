import itertools

from pip._vendor.packaging.markers import Marker
from pip._vendor.packaging.requirements import Requirement


def _iter_requirements(entry):
    try:
        requires = entry['requires']
    except KeyError:
        return
    req_iter = (Requirement(s) for s in requires)
    environment = entry.get('environment')
    extra = entry.get('extra')
    if not environment and not extra:
        return req_iter
    requirements = list(req_iter)
    for r in requirements:
        mparts = []
        if r.marker:
            mparts.append(r.marker)
        if environment:
            mparts.append(environment)
        if extra:
            mparts.append('extra == {!r}'.format(extra))
        if len(mparts) > 1:
            m = Marker(' and '.join('({})'.format(p) for p in mparts))
        else:
            m = Marker(mparts[0])
        r.marker = m
    return iter(requirements)


class DependencySet(object):
    """A representation of dependencies of a distribution.

    This representation is abstract, i.e. completely independent from the
    execution environment. Our resolver needs this to give a machine-agnostic
    dependency tree.
    """
    def __init__(self, requirements):
        self.requirements = list(requirements)
        # TODO: We probably want to include some other metadata as well?

    @classmethod
    def from_wheel(cls, wheel):
        """Build a dependency set from a wheel.

        `wheel` is a `distlib.wheel.Wheel` instance. The metadata is read to
        build the instance.
        """
        return cls(itertools.chain.from_iterable(
            _iter_requirements(entry)
            for entry in wheel.metadata.run_requires
        ))

    @classmethod
    def from_data(cls, info):
        """Build a dependency set with data obtained from an API.

        `info` is a dict-like object, e.g. decoded from a JSON API.
        """
        return cls(Requirement(s) for s in (info['requires_dist'] or []))

    def __repr__(self):
        return 'DependencySet(requirements={!r})'.format(self.requirements)
