import logging

from pip._vendor import six

from petpeeve.wheels import WheelNotFoundError

from . import legacyjsonapi, simpleapi
from .exceptions import APIError


logger = logging.getLogger('petpeeve.indexes')


class JSONEnabledIndex(object):
    """An index server, maybe with "legacy" JSON API available. Like pypi.org.
    """
    def __init__(self, simple_url, json_url):
        self.simple = simpleapi.IndexServer(simple_url)
        self.legacy_json = legacyjsonapi.IndexServer(json_url)

    def get_dependencies(self, candidate, offline=False):
        try:
            logger.debug('Trying Wheel cache...')
            return self.simple.get_dependencies(candidate, offline=True)
        except WheelNotFoundError:
            pass
        try:
            logger.debug('Trying JSON API...')
            return self.legacy_json.get_dependencies(candidate)
        except APIError:    # JSON API is not available.
            if offline:
                raise
        logger.debug('Trying to download an artifact for inspection...')
        return self.simple.get_dependencies(candidate, offline=False)


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
