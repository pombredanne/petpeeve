import collections
import re
import warnings

from pip._vendor.packaging.markers import Marker
from pip._vendor.packaging.requirements import Requirement


# I heard Warehouse currently always only put the extra marker at the end,
# and the operator is always ==, so we cheat a little (a lot?) here.
# https://github.com/pypa/wheel/blob/f3855494f20724f1ae84/wheel/metadata.py#L53
EXTRA_RE = re.compile(r"^(?P<requirement>.+?)(?:extra == '(?P<extra>.+?)')?$")


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
    """A representation of dependencies of a distribution.

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

    @classmethod
    def from_data(cls, info):
        """Build a dependency set with data obtained from an API.

        `info` is a dict-like object, e.g. decoded from a JSON API.
        """
        requires = info['requires_dist']
        if not requires:
            return cls([], {})

        base = []
        extras = collections.defaultdict(list)
        for s in requires:
            requirement = Requirement(s)
            if not requirement.marker:
                base.append(requirement)
                continue
            match = EXTRA_RE.match(s)
            if not match:
                warnings.warn('unrecognized dependency {!r}'.format(s))
                continue
            extra_name = match.group('extra')
            if not extra_name:
                base.append(requirement)
                continue
            s = match.group('requirement').strip()
            if s.endswith('and'):
                s = s[:-3].rstrip()
            if s.endswith(';'):
                s = s[:-1].rstrip()
            extra_reqs = extras[extra_name]
            extra_reqs.append(Requirement(s))
            extras[extra_name] = extra_reqs
        return cls(base, extras)
