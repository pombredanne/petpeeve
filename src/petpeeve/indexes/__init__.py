from pip._vendor import six

from petpeeve._compat import collections_abc

from . import legacyjsonapi, simpleapi
from .exceptions import APIError, WheelNotFoundError


class JSONEnabledDependencyMapping(collections_abc.Mapping):
    """Wraps mappings from simple and JSON indexes to do the optimal thing.
    """
    def __init__(
            self, version_info_getters, version_links,
            python_version_info, offline=False):
        self.mappings = [simpleapi.DependencyMapping(
            version_links, python_version_info, offline=True,
        )]
        if offline:
            return
        self.mappings += [
            legacyjsonapi.DependencyMapping(version_info_getters),
            simpleapi.DependencyMapping(
                version_links, python_version_info, offline=False,
            ),
        ]

    def __contains__(self, key):
        return key in self.mappings[0].links

    def __getitem__(self, key):
        try:
            return self.mappings[0][key]
        except (KeyError, WheelNotFoundError):
            pass
        for mapping in self.mappings[1:]:
            try:
                value = mapping[key]
            except KeyError:
                continue
            return value

    def __iter__(self):
        return iter(self.mappings[0].versions)

    def __len__(self):
        return len(self.mappings[0].versions)


class JSONEnabledIndex(object):
    """An index server, maybe with "legacy" JSON API available. Like pypi.org.
    """
    def __init__(self, simple_url, json_url):
        self.simple = simpleapi.IndexServer(simple_url)
        self.legacy_json = legacyjsonapi.IndexServer(json_url)

    def get_dependencies(
            self, requirement, python_version_info, offline=False):
        version_links = self.simple.get_versioned_links(requirement)
        try:
            getters = self.legacy_json.get_version_info_getters(requirement)
        except APIError:    # JSON API is not available; use simple.
            return simpleapi.DependencyMapping(
                version_links=version_links,
                python_version_info=python_version_info,
                offline=offline,
            )
        return JSONEnabledDependencyMapping(
            version_info_getters=getters, version_links=version_links,
            python_version_info=python_version_info, offline=offline,
        )


class SimpleIndex(simpleapi.IndexServer):
    """A "simple" index server, with only simple API available.
    """


def build_index(url):
    """Introspect the URL to choose an appropriate index.

    If the URL's path is "/simple", we assume it provides the JSON API.
    Otherwise we use it as a simple-only API.
    """
    ps = six.moves.urllib_parse.urlsplit(url)
    if ps.path in ('/simple', '/simple/'):
        json_url = six.moves.urllib_parse.urlunsplit(ps._replace(path='/pypi'))
        return JSONEnabledIndex(url, json_url)
    return SimpleIndex(url)
