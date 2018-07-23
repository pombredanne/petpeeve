import warnings

from .indexes.exceptions import APIError
from .links import parse_link
from .requirements import RequirementSpecification
from .utils import is_version_specified


class Candidate(object):
    """A "pinned" dependency.
    """
    def __init__(self, name, version, extras=None, url=None):
        self.name = name
        self.extras = extras
        self.url = url
        self.version = version

    @classmethod
    def pin_from(cls, requirement, version):
        if not is_version_specified(requirement.specifier, version):
            raise ValueError('{v} does not satisfy {r}'.format(
                v=version, r=requirement,
            ))
        return cls(
            name=requirement.name,
            extras=requirement.extras,
            url=requirement.url,
            version=version,
        )

    def __repr__(self):
        return 'Candidate({!r})'.format(self)

    def __str__(self):
        parts = [self.name]
        if self.extras:
            parts.append('[{}]'.format(','.join(sorted(self.extras))))
        parts.append('=={}'.format(self.version))
        if self.url:
            parts.append(' @ {}'.format(self.url))
        return ''.join(parts)

    def get_dependencies(self, indexes, offline=False):
        if self.url:
            wheel = parse_link(self.url, None).as_wheel(offline=offline)
            return RequirementSpecification.from_wheel(wheel)
        for index in indexes:
            try:
                return index.get_dependencies(self, offline=offline)
            except APIError:
                pass
        warnings.warn('failed to retrieve dependencies for {}'.format(self))
        RequirementSpecification.empty()
