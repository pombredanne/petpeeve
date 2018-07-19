import functools
import warnings

from petpeeve._compat import collections_abc
from petpeeve.dependencies import DependencySet


def get_links_sort_key(link, python_version_info):
    try:
        is_binary_compatible = link.is_binary_compatible
    except AttributeError:
        binary_compatibility = 0
    else:
        binary_compatibility = 1 if is_binary_compatible() else -1
    return (
        binary_compatibility,
        link.is_python_compatible(python_version_info),
    )


class DependencyMapping(collections_abc.Mapping):
    """A lazy-evaluated dependency mapping.

    This behaves like a ``collection.OrderedDict``. Each key is a version
    matching the requirement (latest version first); each value is a
    `DependencySet` containing requirements, representing dependencies
    specified by the given requirement at that version.
    """
    def __init__(self, version_links, python_version_info, offline=False):
        self.versions = sorted(version_links, reverse=True)
        self.links = version_links
        self.python_version_info = python_version_info
        self.offline = offline

    def __contains__(self, key):
        return key in self.links

    def __getitem__(self, key):
        if key not in self.links:
            raise KeyError(key)
        return self._get_dependencies(self.links[key])

    def __iter__(self):
        return iter(self.versions)

    def __len__(self):
        return len(self.versions)

    def _get_dependencies(self, links):
        links_sort_key = functools.partial(
            get_links_sort_key,
            python_version_info=self.python_version_info,
        )
        for link in sorted(links, key=links_sort_key):
            wheel = link.as_wheel(offline=self.offline)
            if not wheel:
                continue
            return DependencySet.from_wheel(wheel)
        warnings.warn('failed to find dependencies in link')
        return []
