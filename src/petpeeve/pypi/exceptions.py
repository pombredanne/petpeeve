class APIError(RuntimeError):
    pass


class PackageNotFound(APIError, ValueError):
    pass
