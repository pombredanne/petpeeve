class APIError(RuntimeError):
    pass


class PackageNotFound(APIError, ValueError):
    pass


class VersionNotFound(APIError, KeyError):
    pass


class WheelNotFoundError(OSError):
    pass
