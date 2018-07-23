import atexit
import os
import shutil
import tempfile


class DownloadIntegrityError(ValueError):
    pass


def download_file(url, filename=None, container=None, check=None):
    from pip._vendor import requests
    response = requests.get(url, stream=True)
    response.raise_for_status()

    if not filename:
        filename = url.rsplit('/', 1)[-1]
    data = response.content
    if callable(check):
        try:
            check(data)
        except ValueError as e:
            raise DownloadIntegrityError(str(e))
    if container is None:
        container = tempfile.mkdtemp()
        atexit.register(shutil.rmtree, container, ignore_errors=True)
    else:
        os.makedirs(container)
    path = os.path.join(container, filename)
    with open(path, 'wb') as f:
        f.write(data)
    return path


def is_version_specified(specifier, version):
    for _ in specifier.filter([version]):
        return True
    return False
