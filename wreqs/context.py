import logging

from requests import Request, Response, Session, Timeout
from typing import Any, Callable, Generator, Optional
from contextlib import contextmanager
from wreqs.error import RetryRequestError
from wreqs.fmt import prettify_request_str, prettify_response_str

logger = logging.getLogger(__name__)


# todo: configure checks for rate limiting bypass


class RequestContext:
    def __init__(
        self,
        request: Request,
        max_retries: int = 3,
        check_retry: Optional[Callable[[Response], bool]] = None,
        retry_callback: Optional[Callable[[Response], None]] = None,
        session: Optional[Session] = None,
        timeout: Optional[float] = None,
        **send_config: dict[str, Any],
    ) -> None:
        self.logger = logger
        self.request = request
        self.response: Optional[Response] = None
        self.session = session or Session()
        self.max_retries = max_retries
        self.check_retry = check_retry
        self.retry_callback = retry_callback
        self.timeout = timeout
        self.send_config = send_config

        self.logger.info(f"RequestContext initialized: {prettify_request_str(request)}")
        self.logger.debug(f"Max retries: {max_retries}")

    def _fetch(self) -> Response:
        """
        Prepare and send the HTTP request.

        This method prepares the request and sends it using the session object.

        Returns:
            Response: The response received from the server.
        """
        self.logger.info(f"Preparing request")
        prepared_request = self.session.prepare_request(self.request)

        try:
            response = self.session.send(
                prepared_request, timeout=self.timeout, **self.send_config
            )
            self.logger.info(f"Received response: {prettify_response_str(response)}")
        except Timeout:
            self.logger.error(f"Request timed out after {self.timeout}s")
            raise

        return response

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
            self.logger.info(f"Attempt {retries + 1}/{self.max_retries}")
            self.response = self._fetch()
            if not self.check_retry or not self.check_retry(self.response):
                self.logger.info("Request successful, no retry needed")
                return self.response
            retries += 1

            self.logger.warning(
                f"Retry attempt {retries}/{self.max_retries}: {prettify_request_str(self.request)}"
            )

            if self.retry_callback:
                self.logger.info(f"Calling `retry_callback` before retry.")
                self.retry_callback(self.response)

        self.logger.error(f"Max retries ({self.max_retries}) reached without success")
        raise RetryRequestError(
            f"Failed after {self.max_retries} retries for request {prettify_request_str(self.request)}."
        )

    def __enter__(self) -> Response:
        self.logger.info(
            f"Entering RequestContext: {prettify_request_str(self.request)}"
        )
        try:
            if self.check_retry:
                self.logger.info(
                    "Retry check function provided, handling potential retries"
                )
                return self._handle_retry()
            else:
                self.logger.info("No retry check function, performing single fetch")
                return self._fetch()
        except Exception as e:
            self.logger.error(f"Error during request: {str(e)}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.logger.info("Exiting RequestContext")

        if self.response:
            self.logger.info(
                f"Exiting RequestContext: {prettify_response_str(self.response)}"
            )

        self.logger.debug("Closing session")
        self.session.close()

        if exc_type:
            self.logger.error(
                f"Exception occurred: {exc_type.__name__}: {str(exc_val)}"
            )


@contextmanager
def wrapped_request(
    req: Request,
    max_retries: int = 3,
    check_retry: Optional[Callable[[Response], bool]] = None,
    retry_callback: Optional[Callable[[Response], None]] = None,
    session: Optional[Session] = None,
    timeout: Optional[float] = None,
) -> Generator[Response, None, None]:
    context = RequestContext(
        req,
        max_retries,
        check_retry,
        retry_callback=retry_callback,
        session=session,
        timeout=timeout,
    )
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
