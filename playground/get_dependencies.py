from __future__ import print_function

import argparse

from petpeeve.indexes import build_index
from pip._vendor.packaging.requirements import Requirement


parser = argparse.ArgumentParser()
parser.add_argument('requirement')
parser.add_argument('--url', action='store', default='https://pypi.org/simple')
parser.add_argument('--offline', action='store_true')
options = parser.parse_args()


requirement = Requirement(options.requirement)
index = build_index(options.url)
print('Using {!r}...'.format(type(index).__name__))

dependency_mapping = index.get_dependencies(
    requirement, None, offline=options.offline,
)

latest_version = next(iter(dependency_mapping.keys()))

depset = dependency_mapping[latest_version]
print('Version {}:'.format(latest_version))
for requirement in depset.base:
    print('    {}'.format(requirement))
print()
for key, requirements in depset.extras.items():
    print('  Extra {!r}'.format(key))
    for requirement in requirements:
        print('    {}'.format(requirement))
    print()
