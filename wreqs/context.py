from requests import Request, Response, Session
from typing import Callable, Generator, Optional, Union
import logging
from contextlib import contextmanager
from wreqs.error import RetryRequestError
from wreqs.fmt import prettify_request_str

logger = logging.getLogger(__name__)


class RequestContext:
    def __init__(
        self,
        request: Request,
        max_retries: int = 3,
        check_retry: Optional[Callable[[Response], bool]] = None,
        session: Optional[Session] = None,
    ) -> None:
        self.logger = logger
        self.request = request
        self.response: Optional[Response] = None
        self.session = session or Session()
        self.max_retries = max_retries
        self.check_retry = check_retry

    def _fetch(self) -> Response:
        """
        Prepare and send the HTTP request.

        This method prepares the request and sends it using the session object.

        Returns:
            Response: The response received from the server.
        """
        prepared_request = self.session.prepare_request(self.request)
        return self.session.send(prepared_request)

    def _handle_retry(self) -> Response:
        """
        Handle the retry logic for the request.

        This method attempts to send the request and retry if necessary, based on
        the check_retry function and max_retries limit.

        Returns:
            Response: The successful response after retries.

        Raises:
            RetryRequestError: If the maximum number of retries is reached without a
                successful response.
        """
        retries = 0
        while retries < self.max_retries:
            self.response = self._fetch()
            if not self.check_retry or not self.check_retry(self.response):
                return self.response
            retries += 1
            self.logger.warning(f"Retrying request ({retries}/{self.max_retries})")
        raise RetryRequestError(
            f"Failed after {self.max_retries} retries for request {prettify_request_str(self.request)}."
        )

    # todo: add access to send for configuring stuff like proxies
    # todo: configure checks for rate limiting bypass (do this on wrapped_session)
    def __enter__(self) -> Response:
        try:
            if self.check_retry:
                return self._handle_retry()
            else:
                return self._fetch()
        except Exception as e:
            self.logger.error(f"Error during request: {str(e)}")
            raise

    # todo: add configuration for error handling
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.response:
            self.response.close()
        self.session.close()


@contextmanager
def wrapped_request(
    req: Request,
    max_retries: int = 3,
    check_retry: Optional[Callable[[Response], bool]] = None,
    session: Optional[Session] = None,
) -> Generator[Response, None, None]:
    context = RequestContext(req, max_retries, check_retry, session)
    try:
        yield context.__enter__()
    finally:
        context.__exit__(None, None, None)


def configure_logger(
    custom_logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename: Optional[str] = None,
) -> None:
    global logger
    if custom_logger:
        logger = custom_logger
    else:
        logger.setLevel(level)
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        handler = logging.FileHandler(filename) if filename else logging.StreamHandler()
        formatter = logging.Formatter(format)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
