"""Resolver implementating the "latest" strategy.

When there is a dependency with an open version (e.g. "*", "<=5.0", ">3"),
always choose the latest version available.

This is similar to pip-tools's implementation.
"""


from petpeeve.dependencies import DependencySet


class MaxRoundExceeded(RuntimeError):
    pass


class Resolver(object):

    def _resolve_one_round(self, dependency_set):
        """Run through the set, adding second-level dependencies.
        """

    def resolve(self, dependencies, max_rounds=16):
        """Convert a set of abstract dependencies into a set of concrete ones.
        """
        dependency_set = DependencySet.from_iterable(dependencies)

        rounds_done = 0
        while not dependency_set.is_concrete():
            if rounds_done > max_rounds:
                raise MaxRoundExceeded(dependency_set)
            dependency_set = self._resolve_one_round(dependency_set)
            rounds_done += 1

        return dependency_set.as_set()
