class APIError(RuntimeError):
    pass


class PackageNotFound(APIError, ValueError):
    pass


class VersionNotFound(APIError, KeyError):
    def __init__(self, package, version):
        super(VersionNotFound, self).__init__(
            '{}=={}'.format(package, version),
        )
