from __future__ import print_function

import sys

from petpeeve.pypi.simpleapi import IndexServer
from pip._vendor.packaging.requirements import Requirement


try:
    req_str = sys.argv[1]
except IndexError:
    print('example usage: {} requests'.format(sys.argv[0]), file=sys.stderr)
    sys.exit(1)


requirement = Requirement(req_str)
index = IndexServer('https://pypi.org/simple')
for version, links in index._get_versioned_links(requirement).items():
    print('Version {}:'.format(version))
    for link in links:
        try:
            compatible = link.is_binary_compatible()
        except AttributeError:
            bmarker = ' '
        else:
            bmarker = 'o' if compatible else 'x'
        pmarker = 'o' if link.is_python_compatible(sys.version_info) else 'x'
        print('    {} {} {}'.format(bmarker, pmarker, link.filename))
