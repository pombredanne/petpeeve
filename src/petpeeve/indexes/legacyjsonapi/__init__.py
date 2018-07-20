import functools
import posixpath

from pip._vendor import requests
from pip._vendor.packaging.version import parse as parse_version

from petpeeve._compat.functools import lru_cache

from ..exceptions import APIError, PackageNotFound, VersionNotFound
from ..utils import is_version_specified
from .providers import DependencyMapping


# Should be reasonable?
PYPI_PACKAGE_CACHE_SIZE = 64
PYPI_VERSION_CACHE_SIZE = 1024


class IndexServer(object):

    def __init__(self, base_url):
        self.base_url = base_url

    def _get(self, *parts):
        """Access an API endpoint.
        """
        url = posixpath.join(posixpath.join(self.base_url, *parts), 'json')
        response = requests.get(url)
        return response

    @lru_cache(maxsize=PYPI_VERSION_CACHE_SIZE)
    def _get_version_info(self, package, ver):
        response = self._get(package, ver)
        if response.status_code == 404:
            raise VersionNotFound(package)
        elif not response.ok:
            raise APIError(response.reason)
        data = response.json()
        return data['info']

    @lru_cache(maxsize=PYPI_PACKAGE_CACHE_SIZE)
    def get_version_info_getters(self, requirement):
        package = requirement.name
        response = self._get(package)
        if response.status_code == 404:
            raise PackageNotFound(package)
        elif not response.ok:
            raise APIError(response.reason)
        data = response.json()
        return {
            v: functools.partial(self._get_version_info, package, k)
            for k, v in ((k, parse_version(k)) for k in data['releases'])
            if is_version_specified(requirement.specifier, v)
        }

    def get_dependencies(self, requirement):
        """Discover dependencies for this requirement.

        Returns an object that behaves like a ``collection.OrderedDict``. Each
        key is a version matching the requirement (latest version first); each
        value is a list of requirements representing dependencies specified by
        that version.

        :param requirement: A :class:`packaging.requirements.Requirement`
            instance specifying a package requirement.
        """
        getters = self.get_version_info_getters(requirement)
        return DependencyMapping(version_info_getters=getters)
