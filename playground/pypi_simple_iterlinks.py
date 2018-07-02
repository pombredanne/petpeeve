import sys

from petpeeve.pypi.simpleapi import IndexServer
from pip._vendor.packaging.requirements import Requirement


requirement = Requirement('aiohttp==3.3.2')

index = IndexServer('https://pypi.org/simple')

for i, link in enumerate(index.iter_links(requirement)):
    binary_marker = 'o' if link.is_binary_compatible() else 'x'
    python_marker = 'o' if link.is_python_compatible(sys.version_info) else 'x'
    print(binary_marker, python_marker, link.filename)
