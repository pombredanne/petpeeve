from petpeeve._compat import Collection


class DependencySet(Collection):

    def __init__(self):
        super(DependencySet, self).__init__()
        self._items = set()

    def __contains__(self, dep):
        return dep in self._items

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    @classmethod
    def from_iterable(cls, it):
        instance = cls()
        for d in it:
            instance.add(d)
        return instance

    def add(self, dependency):
        self._items.add(dependency)
