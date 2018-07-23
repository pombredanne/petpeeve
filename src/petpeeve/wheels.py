import atexit
import os
import shutil
import subprocess
import sys
import tempfile
import warnings

from petpeeve.pip_internal import cache, index, locations
from petpeeve.pip_internal.utils.misc import unpack_file

from .utils import download_file


class PipLink(object):
    """A pip-compatible link object.
    """
    def __init__(self, link):
        """Create a pip-compatible link object from our own link class.
        """
        self.__link = link

    @property
    def url(self):
        return '{}#{}'.format(self.__link.url, self.__link.checksum)

    @property
    def url_without_fragment(self):
        return self.__link.url

    @property
    def hash_name(self):
        return self.__link.checksum.split('=', 1)[0]

    @property
    def hash(self):
        return self.__link.checksum.split('=', 1)[-1]


def get_wheel_path(link, offline):
    """Get the wheel from cache, or download it into the cache and return it.
    """
    wheel_cache = cache.SimpleWheelCache(
        locations.USER_CACHE_DIR,
        index.FormatControl(set(), set()),
    )
    cache_dir = wheel_cache.get_path_for_link(PipLink(link))
    cache_path = os.path.join(cache_dir, link.filename)
    if os.path.exists(cache_path):
        return cache_path
    elif offline:
        return None
    downloaded_path = download_file(
        link.url, filename=link.filename, check=link.check_download,
    )
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    shutil.move(downloaded_path, cache_path)
    return cache_path


def get_built_wheel_path(link):
    """Download an sdist from link, and build a wheel out of it.
    """
    sdist_path = download_file(
        link.url, filename=link.filename, check=link.check_download,
    )
    container = os.path.dirname(sdist_path)

    unpacked_dir = tempfile.mkdtemp()
    atexit.register(shutil.rmtree, unpacked_dir, ignore_errors=True)
    unpack_file(sdist_path, unpacked_dir, None, PipLink(link))

    wheel_content_dir = tempfile.mkdtemp()
    atexit.register(shutil.rmtree, wheel_content_dir, ignore_errors=True)
    proc = subprocess.Popen(
        [sys.executable, 'setup.py', 'bdist_wheel', '-d', container],
        cwd=unpacked_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        warnings.warn('failed to build wheel\n{}'.format(stderr))
        return None
    for fn in os.listdir(container):
        if fn != os.path.basename(sdist_path):
            return os.path.join(container, fn)
    warnings.warn('failed to find built wheel')
    return None
