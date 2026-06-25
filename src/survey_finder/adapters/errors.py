class AdapterError(Exception):
    pass


class AuthError(AdapterError):
    pass


class RateLimitError(AdapterError):
    pass


class SchemaDriftError(AdapterError):
    pass


class ProxyError(AdapterError):
    pass
