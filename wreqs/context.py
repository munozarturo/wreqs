from requests import Request, Response, Session
from typing import Callable, Optional
import logging

from wreqs.error import RetryRequestError
from wreqs.fmt import prettify_request_str


# Default logger
logger = logging.getLogger(__name__)


class RequestContext:
    def __init__(self, request: Request) -> None:
        self.logger = logger

        self.request = request
        self.response: Optional[Response] = None
        self.session = Session()

    # todo: add access to send for configuring stuff like proxies
    # todo: configure checks for rate limiting bypass (do this on wrapped_session)
    def __enter__(
        self, check_retry: Optional[Callable[[Response], bool]], max_retries: int = 3
    ) -> Response:
        prepared_request = self.session.prepare_request(self.request)

        def fetch() -> Response:
            response = self.session.send(prepared_request)
            return response

        self.response = fetch()

        if check_retry:
            retries: int = 0
            if check_retry(self.response):
                if retries <= max_retries:
                    self.response = fetch()
                    retries += 1
                else:
                    raise RetryRequestError(
                        f"Failed {retries}/{max_retries} for request {prettify_request_str(self.request)}."
                    )

        return self.response

    # todo: add configuration for error handling
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.response:
            self.response.close()
        self.session.close()


def wrapped_request(req: Request) -> RequestContext:
    return RequestContext(req)


def configure_logger(
    custom_logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename: Optional[str] = None,
) -> None:
    """
    Configure the logger for the module.

    Args:
        custom_logger (Optional[logging.Logger]): A custom logger to use. If None, configures the default logger.
        level (int): The logging level (e.g., logging.INFO, logging.DEBUG)
        format (str): The log message format
        filename (Optional[str]): If provided, logs will be written to this file
    """
    global logger

    if custom_logger:
        logger = custom_logger
    else:
        logger.setLevel(level)

        # Remove any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        if filename:
            handler = logging.FileHandler(filename)
        else:
            handler = logging.StreamHandler()

        formatter = logging.Formatter(format)
        handler.setFormatter(formatter)

        logger.addHandler(handler)
