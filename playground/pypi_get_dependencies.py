from __future__ import print_function

import argparse

from petpeeve.pypi import legacyjsonapi, simpleapi
from pip._vendor.packaging.requirements import Requirement


parser = argparse.ArgumentParser()
parser.add_argument('requirement')
parser.add_argument('--api', action='store', choices=['simple', 'json'])
parser.add_argument('--offline', action='store_true')
options = parser.parse_args()


requirement = Requirement(options.requirement)

print('Using the {!r} API...'.format(options.api))
if options.api == 'simple':
    index = simpleapi.IndexServer('https://pypi.org/simple')
    dependency_mapping = index.get_dependencies(
        requirement, None, offline=options.offline,
    )
elif options.api == 'json':
    index = legacyjsonapi.IndexServer('https://pypi.org/pypi')
    dependency_mapping = index.get_dependencies(requirement)

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
