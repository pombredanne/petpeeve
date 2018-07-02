import collections
import functools
import posixpath

from pip._vendor.packaging import (
    specifiers as packaging_specifiers,
    version as packaging_version,
)
from pip._vendor import requests, six

from wheel import pep425tags

from petpeeve._compat.functools import lru_cache


def is_specified(specifier, version):
    for _ in specifier.filter([version]):
        return True
    return False


class Link(object):
    """Represents a link in the simple API page.
    """
    def __init__(
            self, url, checksum,
            file_stem, file_extension,
            python_specifier):
        self.url = url
        self.checksum = checksum
        self.file_stem = file_stem
        self.extension = file_extension
        self.python_specifier = python_specifier
        self.info = self.parse_for_info()

    def __repr__(self):
        return '<{type} {filename}>'.format(
            type=type(self).__name__,
            filename=self.filename,
        )

    @property
    def filename(self):
        return self.file_stem + self.extension

    def parse_for_info(self):
        raise NotImplementedError

    def available_for(self, requirement, python_version_info):
        if not python_version_info:
            return True
        python_version = packaging_version.parse('.'.join(
            str(i) for i in python_version_info[:3]
        ))
        return is_specified(self.python_specifier, python_version)


SourceInformation = collections.namedtuple('SourceInformation', [
    'distribution_name',
    'version',
])


class SourceDistributionLink(Link):
    """Link to an sdist.
    """
    def parse_for_info(self):
        name, ver = self.file_stem.rsplit('-', 1)
        return SourceInformation(name, packaging_version.parse(ver))

    def available_for(self, requirement, python_version_info):
        ok = super(SourceDistributionLink, self).available_for(
            requirement, python_version_info,
        )
        return ok and is_specified(requirement.specifier, self.info.version)


WheelInformation = collections.namedtuple('WheelInformation', [
    'distribution_name',
    'version',
    'build_tag',
    'language_implementation_tag',
    'abi_tag',
    'platform_tag',
])


class WheelDistributionLink(Link):
    """Link to a wheel.
    """
    def parse_for_info(self):
        """Parse the wheel's file name according to PEP427.

        https://www.python.org/dev/peps/pep-0427/#file-name-convention
        """
        parts = self.file_stem.split('-')
        if len(parts) == 6:
            name, ver, build, impl, abi, plat = parts
            build = int(build)
        elif len(parts) == 5:
            name, ver, impl, abi, plat = parts
            build = None
        version = packaging_version.parse(ver)
        return WheelInformation(name, version, build, impl, abi, plat)

    def available_for(self, requirement, python_version_info):
        ok = super(WheelDistributionLink, self).available_for(
            requirement, python_version_info,
        )
        if not ok:
            return False
        if not is_specified(requirement.specifier, self.info.version):
            return False
        supported_tags = pep425tags.get_supported()
        wheel_tag = (
            self.info.language_implementation_tag,
            self.info.abi_tag,
            self.info.platform_tag,
        )
        if wheel_tag not in supported_tags:
            return False
        return True


class UnwantedLink(ValueError):
    pass


WANTED_EXTENSIONS = [
    ('.whl', WheelDistributionLink),
    ('.tar.gz', SourceDistributionLink),
    ('.zip', SourceDistributionLink),
]


def select_link_constructor(filename):
    """Parse the file name to recognize an artifact type.

    This is important because we need to somehow handle the sdist .tar.gz
    extension. We also exclude packages we don't want here.
    """
    for ext, klass in WANTED_EXTENSIONS:
        if filename.endswith(ext):
            return functools.partial(
                klass,
                file_stem=filename[:-len(ext)],
                file_extension=ext,
            )
    raise UnwantedLink(filename)


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


class APIError(RuntimeError):
    pass


class PackageNotFound(APIError, ValueError):
    pass


PYPI_PAGE_CACHE_SIZE = 50   # Should be reasonable?


class IndexServer(object):

    def __init__(self, base_url):
        self.base_url = base_url

    @lru_cache(maxsize=PYPI_PAGE_CACHE_SIZE)
    def get_package_links(self, package):
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

    def iter_links(self, requirement, python_version_info):
        """Iterate through links matching this requirement.

        :param requirement: A :class:`packaging.requirements.Requirement`
            instance specifying a package requirement.
        :param python_version_info: If truthy, should be a 3+-tuple (e.g.
            ``sys.version_info``), and is used to compare against the link's
            requires-python info, and excludes those not matching. If falsy,
            the comparison is skipped.
        """
        links = self.get_package_links(requirement.name)

        # Optimization: Latest packages are preferred, and usually listed last.
        for link in reversed(links):
            if not link.available_for(requirement, python_version_info):
                continue
            yield link
