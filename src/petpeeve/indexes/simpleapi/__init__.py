import collections
import posixpath

from pip._vendor import requests, six
from pip._vendor.packaging import specifiers as packaging_specifiers

from petpeeve._compat.functools import lru_cache

from ..exceptions import APIError, PackageNotFound
from .links import select_link_constructor, UnwantedLink
from .providers import DependencyMapping


class SimplePageParser(six.moves.html_parser.HTMLParser):
    """Parser to scrap links from a simple API page.
    """
    def __init__(self):
        super(SimplePageParser, self).__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        url = None
        python_specifier = packaging_specifiers.SpecifierSet('')
        for attr, value in attrs:
            if attr == 'href':
                url_parts = six.moves.urllib_parse.urlsplit(value)
                checksum = url_parts.fragment
                url = six.moves.urllib_parse.urlunsplit(
                    url_parts._replace(fragment=''),
                )
            elif attr == 'data-requires-python':
                python_specifier = packaging_specifiers.SpecifierSet(value)
        if not url:
            return
        try:
            link_ctor = select_link_constructor(url.rsplit('/', 1)[-1])
        except UnwantedLink:
            return
        self.links.append(link_ctor(
            url=url, checksum=checksum,
            python_specifier=python_specifier,
        ))


PYPI_PAGE_CACHE_SIZE = 64   # Should be reasonable?


class IndexServer(object):

    def __init__(self, base_url):
        self.base_url = base_url

    @lru_cache(maxsize=PYPI_PAGE_CACHE_SIZE)
    def _get_package_links(self, package):
        """Get links on a simple API page.
        """
        url = posixpath.join(self.base_url, package)
        response = requests.get(url)
        if response.status_code == 404:
            raise PackageNotFound(package)
        elif not response.ok:
            raise APIError(response.reason)
        parser = SimplePageParser()
        parser.feed(response.text)
        return parser.links

    def get_versioned_links(self, requirement):
        version_links = collections.defaultdict(list)
        for link in self._get_package_links(requirement.name):
            if not link.is_specified_by_requirement(requirement):
                continue
            try:
                version = link.info.version
            except AttributeError:
                continue
            version_links[version].append(link)
        return version_links

    def get_dependencies(
            self, requirement, python_version_info, offline=False):
        """Discover dependencies for this requirement.

        Returns an object that behaves like a ``collection.OrderedDict``. Each
        key is a version matching the requirement (latest version first); each
        value is a list of requirements representing dependencies specified by
        that version.

        :param requirement: A :class:`packaging.requirements.Requirement`
            instance specifying a package requirement.
        :param python_version_info: A 3+ tuple of integers, or `None`.
        """
        return DependencyMapping(
            version_links=self.get_versioned_links(requirement),
            python_version_info=python_version_info,
            offline=offline,
        )
