from petpeeve._compat import collections_abc
from petpeeve.dependencies import DependencySet


class DependencyMapping(collections_abc.Mapping):
    """A lazy-evaluated dependency mapping.

    This behaves like a ``collection.OrderedDict``. Each key is a version
    matching the requirement (latest version first); each value is a
    `DependencySet` containing requirements, representing dependencies
    specified by the given requirement at that version.
    """
    def __init__(self, version_info_getters):
        self.versions = sorted(version_info_getters, reverse=True)
        self.getters = version_info_getters

    def __contains__(self, key):
        return key in self.getters

    def __getitem__(self, key):
        if key not in self.getters:
            raise KeyError(key)
        return self._get_dependencies(self.getters[key]())

    def __iter__(self):
        return iter(self.versions)

    def __len__(self):
        return len(self.versions)

    def _get_dependencies(self, info):
        requires_dist = info.get('requires_dist')
        if requires_dist is None:
            requires_dist = []
        return DependencySet.from_data(requires_dist)
