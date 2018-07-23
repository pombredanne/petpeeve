from __future__ import print_function

import argparse

from petpeeve.candidates import Candidate
from petpeeve.indexes import build_index, SimpleIndex
from pip._vendor.packaging.version import parse as parse_version


class PackageAction(argparse.Action):
    def __call__(self, parser, options, name, option_string=None):
        extras = []
        parts = name.rsplit('[', 1)
        if len(parts) > 1:
            name = parts[0]
            extras = [e.strip() for e in parts[-1].rstrip(']').split(',')]
        options.name = name
        options.extras = extras


class VersionAction(argparse.Action):
    def __call__(self, parser, options, value, option_string=None):
        setattr(options, self.dest, parse_version(value))


parser = argparse.ArgumentParser()
parser.add_argument('package', action=PackageAction)
parser.add_argument('version', action=VersionAction)
parser.add_argument('--url', action='store', default='https://pypi.org/simple')
parser.add_argument('--simple', action='store_true')
parser.add_argument('--offline', action='store_true')
options = parser.parse_args()


if options.simple:
    ctor = SimpleIndex
else:
    ctor = build_index
index = ctor(options.url)

candidate = Candidate(
    name=options.name,
    extras=options.extras,
    version=options.version,
)

print(candidate)
for r in index.get_dependencies(candidate, offline=options.offline):
    print('  {}'.format(r))
