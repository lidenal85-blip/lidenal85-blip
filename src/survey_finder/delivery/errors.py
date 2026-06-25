class DeliveryError(Exception):
    pass


class RateLimitError(DeliveryError):
    pass


class ExternalAPIError(DeliveryError):
    pass
