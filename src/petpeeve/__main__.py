import argparse
import logging
import sys

from ._compat import urllib_parse


pip_logger = logging.getLogger('pip')


def create_url_entry(url):
    parsed = urllib_parse.urlparse(url)
    return {
        'url': url,
        'verify_ssl': parsed.scheme.endswith('s'),
        'name': parsed.hostname,
    }


def parse_args():
    parser = argparse.ArgumentParser(prog='petpeeve')
    parser.add_argument('requirements.txt', dest='requirements_filename')
    parser.add_argument('--pypi-mirror', default=None)
    parser.add_argument('--verbose', store_const=True, default=False)
    parser.add_argument('--pre', store_const=True, default=False)
    parser.add_argument('--clear', store_const=True, default=False)
    parser.add_argument('--debug', store_const=True, default=False)
    parser.add_argument('--system', store_const=True, default=False)
    return parser.parse_known_args()


def main():
    options, unknown_args = parse_args()
    sys.argv = [sys.argv[0]] + unknown_args

    if options.verbose:
        pip_logger.setLevel(logging.INFO)
    if options.debug:
        pip_logger.setLevel(logging.DEBUG)

    with open(options.requirements_filename) as f:
        package_lines = [
            line for line in (raw_line.strip() for raw_line in f)
            if line and not line.startswith('#') and not line.startswith('--')
        ]

    if options.pypi_mirror:
        pypi_mirror_entry = create_url_entry(options.pypi_mirror)
    else:
        pypi_mirror_entry = None


if __name__ == '__main__':
    main()
