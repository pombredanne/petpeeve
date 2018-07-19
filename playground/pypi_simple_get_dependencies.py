from __future__ import print_function

import argparse

from petpeeve.pypi.simpleapi import IndexServer
from pip._vendor.packaging.requirements import Requirement


parser = argparse.ArgumentParser()
parser.add_argument('requirement')
parser.add_argument('--offline', action='store_true')
options = parser.parse_args()


requirement = Requirement(options.requirement)
index = IndexServer('https://pypi.org/simple')

dependency_provider = index.get_dependencies(
    requirement, None, offline=options.offline,
)
latest_version = max(dependency_provider.keys())

depset = dependency_provider[latest_version]
print('Version {}:'.format(latest_version))
for requirement in depset.requirements:
    print('  {}'.format(requirement))
