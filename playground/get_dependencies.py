from __future__ import print_function

import argparse

from petpeeve.candidates import Candidate
from petpeeve.indexes import build_index, SimpleIndex
from pip._vendor.packaging.version import parse as parse_version


class VersionAction(argparse.Action):
    def __call__(self, parser, options, value, option_string=None):
        setattr(options, self.dest, parse_version(value))


parser = argparse.ArgumentParser()
parser.add_argument('name')
parser.add_argument('version', action=VersionAction)
parser.add_argument('--url', action='store', default='https://pypi.org/simple')
parser.add_argument('--simple', action='store_true')
parser.add_argument('--offline', action='store_true')
options = parser.parse_args()


candidate = Candidate(name=options.name, version=options.version)
if options.simple:
    index = SimpleIndex(options.url)
else:
    index = build_index(options.url)
print('Using {!r}...'.format(type(index).__name__))

depset = index.get_dependencies(candidate, offline=options.offline)

print('Version {}:'.format(options.version))
for requirement in depset.base:
    print('    {}'.format(requirement))
print()
for key, requirements in depset.extras.items():
    print('  Extra {!r}'.format(key))
    for requirement in requirements:
        print('    {}'.format(requirement))
    print()
