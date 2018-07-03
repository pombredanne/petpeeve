from petpeeve._compat import collections_abc


class LazyDependencyProvider(collections_abc.Mapping):
    """A lazy-evaluated dependency provider.

    This behaves like a ``collection.OrderedDict``. Each key is a version
    matching the requirement; each value is a list of requirements representing
    dependencies specified by the given requirement at that version.
    """
    def __init__(self, version_links, python_version_info):
        self.versions = sorted(self.version_links, reverse=True)
        self.links = version_links
        self.python_version_info = python_version_info

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
        # TODO: Do the hard work.
        # 1. Sort the links by preference.
        # 2. Download them one by one until we get dependencies succesfully.
        # 3. For each, look into the package to find dependencies.
        def links_sort_key(link):
            try:
                is_binary_compatible = link.is_binary_compatible
            except AttributeError:
                binary_compatibility = 0
            else:
                binary_compatibility = 1 if is_binary_compatible() else -1
            return (
                binary_compatibility,
                link.is_python_compatible(self.python_version_info),
            )

        for link in sorted(links, key=links_sort_key):
            dist = link.as_distribution()
            return dist.get_dependencies()
