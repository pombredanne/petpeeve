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
        if self.version:
            parts.append('=={}'.format(self.version))
        if self.url:
            parts.append(' @ {}'.format(self.url))
        return ''.join(parts)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)
