def is_version_specified(specifier, version):
    for _ in specifier.filter([version]):
        return True
    return False
