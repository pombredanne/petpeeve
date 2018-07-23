import posixpath

from pip._vendor import requests

from petpeeve._compat.functools import lru_cache
from petpeeve.requirements import RequirementSpecification

from ..exceptions import APIError, VersionNotFound


PYPI_VERSION_CACHE_SIZE = 1024  # Should be reasonable?


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

    def get_dependencies(self, candidate):
        """Discover dependencies for this candidate.

        Returns a collection of `Requirement` instances.
        """
        info = self._get_version_info(candidate.name, str(candidate.version))
        requires_dist = info.get('requires_dist')
        if requires_dist is None:
            return set()
        reqset = RequirementSpecification.from_data(requires_dist)
        return reqset.get_dependencies(candidate.extras)
