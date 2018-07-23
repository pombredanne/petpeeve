import posixpath

from pip._vendor import requests
from pip._vendor.packaging.version import parse as parse_version

from petpeeve._compat.functools import lru_cache
from petpeeve.candidates import Candidate
from petpeeve.requirements import RequirementSpecification

from ..exceptions import APIError, PackageNotFound, VersionNotFound


# Should be reasonable?
PYPI_PACKAGE_CACHE_SIZE = 512
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
            raise VersionNotFound(package, ver)
        elif not response.ok:
            raise APIError(response.reason)
        data = response.json()
        try:
            return data['info']
        except KeyError:
            raise APIError('non-comforming JSON API')

    @lru_cache(maxsize=PYPI_PACKAGE_CACHE_SIZE)
    def _get_versions(self, package):
        response = self._get(package)
        if response.status_code == 404:
            raise PackageNotFound(package)
        elif not response.ok:
            raise APIError(response.reason)
        data = response.json()
        try:
            releases = data['releases']
        except KeyError:
            raise APIError('non-comforming JSON API')
        return [parse_version(k) for k, v in releases.items() if v]

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

    def get_candidates(self, requirement):
        """Find candidates for this requirement.

        Returns a collection of `Candidate` instances.
        """
        return set(
            Candidate.pin_from(requirement, version)
            for version in self._get_versions(requirement.name)
        )
