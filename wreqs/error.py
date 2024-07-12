class WrappedRequestError(Exception):
    pass


class RetryRequestError(WrappedRequestError):
    pass
