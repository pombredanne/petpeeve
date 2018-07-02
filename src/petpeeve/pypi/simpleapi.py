import collections
import functools
import posixpath

from pip._vendor.packaging import (
    specifiers as packaging_specifiers,
    version as packaging_version,
)
from pip._vendor import requests, six


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
        return '<{type} {url}>'.format(type=type(self).__name__, url=self.url)

    def parse_for_info(self):
        raise NotImplementedError

    def is_python_match(self, version_info):
        python_version = packaging_version.parse('.'.join(
            str(i) for i in version_info[:3]
        ))
        return bool(self.python_specifier.filter([python_version]))


SourceInformation = collections.namedtuple('SourceInformation', [
    'distribution_name',
    'version',
])


class SourceDistributionLink(Link):
    def parse_for_info(self):
        name, ver = self.file_stem.rsplit('-', 1)
        return SourceInformation(name, packaging_version.parse(ver))


WheelInformation = collections.namedtuple('WheelInformation', [
    'distribution_name',
    'version',
    'build_tag',
    'language_implementation_tag',
    'abi_tag',
    'platform_tag',
])


class WheelDistributionLink(Link):
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


class IndexServer(object):

    def __init__(self, base_url):
        self.base_url = base_url

    def _get_links(self, package):
        url = posixpath.join(self.base_url, package)
        response = requests.get(url)
        if response.status_code == 404:
            raise PackageNotFound(package)
        elif not response.ok:
            raise APIError(response.reason)
        parser = SimplePageParser()
        parser.feed(response.text)
        return parser.links
