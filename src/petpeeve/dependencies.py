import collections
import re

from pip._vendor import six
from pip._vendor.packaging.markers import Marker
from pip._vendor.packaging.requirements import Requirement


# I heard Warehouse and Wheel always put the extra marker at the end, and the
# operator is always ==, so we cheat a little (a lot?) here.
EXTRA_RE = re.compile(
    r"""^(?P<requirement>.+?)(?:extra\s*==\s*['"](?P<extra>.+?)['"])$""",
)


def _parse_requirement(s):
    """Helper function to parse both modern and "legacy" requirement styles.

    Old requirements append the extra key at the end of the environment
    markers, e.g.::

        PySocks (!=1.5.7,>=1.5.6); extra == 'socks'

    This uses a very naive pattern-matching logic to strip that last part out
    of the environment markers.

    This kind of formats are used in old wheels and the PyPI's JSON API.

    Returns a 2-tuple `(requirement, extra)`. The first member is a
    `Requirement` instance, and the second the extra's name. If no extra is
    detected, the second member will be `None`.
    """
    requirement = Requirement(s)
    if not requirement.marker:  # Short circuit to favour the common case.
        return requirement, None
    match = EXTRA_RE.match(s)
    if not match:   # No final "extra" expression, yay.
        return requirement, None
    extra = match.group('extra')
    if not extra:
        return requirement, None
    s = match.group('requirement').rstrip()
    if s.endswith('and'):
        s = s[:-3].rstrip()
    if s.endswith(';'):
        s = s[:-1].rstrip()
    return Requirement(s), extra


def _add_requires(entry, base, extras):
    """Append all requirements in an entry to the list.

    This combines the `environment` key's content into the requirement's
    existing markers, and append them to the appropriate list(s).
    """
    requires = entry.get('requires')
    if not requires:
        return
    environment = entry.get('requirement')
    e_extra = entry.get('extra')
    for s in requires:
        r, r_extra = _parse_requirement(s)
        if environment:
            if r.marker:
                m = Marker('({}) and ({})'.format(environment, r.marker))
            else:
                m = Marker(environment)
            r.marker = m
        if not e_extra and not r_extra:
            base.append(r)
        elif e_extra:
            extras[e_extra].append(r)
        elif r_extra:
            extras[r_extra].append(r)


class DependencySet(object):
    """A representation of dependencies of a distribution.

    This representation is abstract, i.e. completely independent from the
    execution environment. Our resolver needs this to give a machine-agnostic
    dependency tree.
    """
    def __init__(self, base, extras):
        self.base = base
        self.extras = extras
        # TODO: We probably want to include some other metadata as well?

    @classmethod
    def from_wheel(cls, wheel):
        """Build a dependency set from a wheel.

        `wheel` is a `distlib.wheel.Wheel` instance. The metadata is read to
        build the instance.
        """
        base = []
        extras = collections.defaultdict(list)
        for entry in wheel.metadata.run_requires:
            if isinstance(entry, six.text_type):
                entry = {'requires': [entry]}
            _add_requires(entry, base, extras)
        return cls(base, extras)

    @classmethod
    def from_data(cls, info):
        """Build a dependency set with data obtained from an API.

        `info` is a dict-like object, e.g. decoded from a JSON API.
        """
        base = []
        extras = collections.defaultdict(list)
        for s in info['requires_dist']:
            requirement, extra = _parse_requirement(s)
            if not extra:
                base.append(requirement)
            else:
                extra_reqs = extras[extra]
                extra_reqs.append(requirement)
                extras[extra] = extra_reqs
        return cls(base, extras)
