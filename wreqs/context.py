import logging

from requests import Request, Response, Session, Timeout
from typing import Callable, Dict, Generator, List, Optional
from contextlib import contextmanager
from contextvars import ContextVar, Token
from wreqs.error import RetryRequestError
from wreqs.fmt import prettify_request_str, prettify_response_str

logger = logging.getLogger(__name__)

_wreqs_session: ContextVar[Optional[Session]] = ContextVar(
    "_wreqs_session", default=None
)


class RequestContext:
    def __init__(
        self,
        request: Request,
        max_retries: int = 3,
        check_retry: Optional[Callable[[Response], bool]] = None,
        retry_callback: Optional[Callable[[Response], None]] = None,
        session: Optional[Session] = None,
        timeout: Optional[float] = None,
        proxies: Optional[List[str]] = None,
    ) -> None:
        """
        A context manager for making HTTP requests with retry and timeout capabilities.

        This context manager provides a convenient way to make HTTP requests with built-in
        retry logic, timeout handling, session management, and proxy rotation.

        Args:
            request (Request): The Request object representing the HTTP request to be made.
            max_retries (int, optional): The maximum number of retry attempts. Defaults to 3.
            check_retry (Optional[Callable[[Response], bool]], optional): A function that takes
                a Response object and returns True if a retry should be attempted, False otherwise.
                If None, no retries will be attempted. Defaults to None.
            retry_callback (Optional[Callable[[Response], None]], optional): A function to be
                called before each retry attempt. It takes a Response object and returns None.
                Defaults to None.
            session (Optional[Session], optional): A requests Session object to be used for
                making the request. If None, a new Session will be created. Defaults to None.
            timeout (Optional[float], optional): The timeout in seconds for the request.
                Defaults to None.
            proxies (Optional[List[str]], optional): A list of proxy servers to use for the request.
                If provided, wreqs will rotate through these proxies for each request or retry attempt.
                Defaults to None.

        Yields:
            Response: The Response object from the successful request.

        Raises:
            RetryRequestError: If the maximum number of retries is reached without a successful response.
            Timeout: If the request times out.

        Example:
            Making a request with proxy rotation:
            ```python
            import requests
            from wreqs import wreq

            proxies = [
                "http://proxy1.example.com:8080",
                "http://proxy2.example.com:8080",
                "http://proxy3.example.com:8080",
            ]

            req = requests.Request("GET", "https://api.example.com/data")
            with wreq(req, max_retries=3, proxies=proxies) as response:
                print(response.json())
            ```

        Notes:
            - The context manager automatically closes the session when exiting the context.
            - If a custom session is provided, it will be used for all requests, including retries.
            - The retry_callback can be useful for implementing backoff strategies or logging.
            - Proxy rotation is done in a round-robin fashion if multiple proxies are provided.
        """
        self.logger = logger
        self.request = request
        self.response: Optional[Response] = None
        self.session = session or Session()
        self.max_retries = max_retries
        self.check_retry = check_retry
        self.retry_callback = retry_callback
        self.timeout = timeout
        self.proxies = proxies
        self.current_proxy_index: int = 0

        self.logger.info(f"RequestContext initialized: {prettify_request_str(request)}")
        self.logger.debug(f"Max retries: {max_retries}")

    def _get_next_proxy(self) -> Optional[Dict[str, str]]:
        """
        Fetch the next proxy in the proxies list.

        Returns:
            Optional[dict[str, str]]: Proxy data.
        """
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return {"http": proxy, "https": proxy}

    def _fetch(self) -> Response:
        """
        Prepare and send the HTTP request.

        This method prepares the request and sends it using the session object.

        Returns:
            Response: The response received from the server.
        """
        self.logger.info(f"Preparing request")
        prepared_request = self.session.prepare_request(self.request)

        proxy = self._get_next_proxy()
        if proxy:
            self.logger.info(f"Using proxy: {proxy}")

        try:
            response = self.session.send(
                prepared_request,
                timeout=self.timeout,
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
def wreq(
    req: Request,
    max_retries: int = 3,
    check_retry: Optional[Callable[[Response], bool]] = None,
    retry_callback: Optional[Callable[[Response], None]] = None,
    session: Optional[Session] = None,
    timeout: Optional[float] = None,
    proxies: Optional[List[str]] = None,
) -> Generator[Response, None, None]:
    """
    A context manager for making HTTP requests with retry and timeout capabilities.

    This context manager provides a convenient way to make HTTP requests with built-in
    retry logic, timeout handling, session management, and proxy rotation.

    Args:
        request (Request): The Request object representing the HTTP request to be made.
        max_retries (int, optional): The maximum number of retry attempts. Defaults to 3.
        check_retry (Optional[Callable[[Response], bool]], optional): A function that takes
            a Response object and returns True if a retry should be attempted, False otherwise.
            If None, no retries will be attempted. Defaults to None.
        retry_callback (Optional[Callable[[Response], None]], optional): A function to be
            called before each retry attempt. It takes a Response object and returns None.
            Defaults to None.
        session (Optional[Session], optional): A requests Session object to be used for
            making the request. If None, a new Session will be created. Defaults to None.
        timeout (Optional[float], optional): The timeout in seconds for the request.
            Defaults to None.
        proxies (Optional[List[str]], optional): A list of proxy servers to use for the request.
            If provided, wreqs will rotate through these proxies for each request or retry attempt.
            Defaults to None.

    Yields:
        Response: The Response object from the successful request.

    Raises:
        RetryRequestError: If the maximum number of retries is reached without a successful response.
        Timeout: If the request times out.

    Example:
        Making a request with proxy rotation:
        ```python
        import requests
        from wreqs import wreq

        proxies = [
            "http://proxy1.example.com:8080",
            "http://proxy2.example.com:8080",
            "http://proxy3.example.com:8080",
        ]

        req = requests.Request("GET", "https://api.example.com/data")
        with wreq(req, max_retries=3, proxies=proxies) as response:
            print(response.json())
        ```

    Notes:
        - The context manager automatically closes the session when exiting the context.
        - If a custom session is provided, it will be used for all requests, including retries.
        - The retry_callback can be useful for implementing backoff strategies or logging.
        - Proxy rotation is done in a round-robin fashion if multiple proxies are provided.
    """
    if session is None:
        session = _wreqs_session.get()

    context = RequestContext(
        req,
        max_retries,
        check_retry,
        retry_callback=retry_callback,
        session=session,
        timeout=timeout,
        proxies=proxies,
    )
    try:
        yield context.__enter__()
    finally:
        context.__exit__(None, None, None)


@contextmanager
def wreqs_session() -> Generator[Session, None, None]:
    """
    A context manager that creates and manages a requests.Session object for use with wreq functions.

    This context manager creates a new Session object, sets it as the active session for the current context,
    yields the session for use within the context, and ensures proper cleanup when the context is exited.

    Usage:
        with wreqs_session() as session:
            # Use wreq functions without explicitly passing the session
            with wreq(Request('GET', 'https://api.example.com')) as response:
                print(response.json())

    Yields:
        Session: A requests.Session object that can be used for making HTTP requests.

    Example:
        ```python
        from wreqs import wreqs_session, wreq
        from requests import Request
        >>>
        def fetch_user(user_id: int) -> dict:
            with wreqs_session():
                request = Request('GET', f'https://api.example.com/users/{user_id}')
                with wreq(request) as response:
                    return response.json()
        ...
        user_data = fetch_user(123)
        print(user_data)
        {'id': 123, 'name': 'John Doe', 'email': 'john@example.com'}
        ```

    Notes:
        - This context manager automatically handles session creation and cleanup.
        - It sets the created session as the active session for all wreq calls within its context.
        - The session is automatically closed when exiting the context, ensuring proper resource management.
        - This function is particularly useful when making multiple requests that should share a session.

    See Also:
        wreq: The main function for making HTTP requests within the wreqs framework.
    """
    session = Session()
    token: Token = _wreqs_session.set(session)
    try:
        yield session
    finally:
        _wreqs_session.reset(token)
        session.close()


def configure_logger(
    custom_logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename: Optional[str] = None,
) -> None:
    """
    Configure the logger for the wreqs module.

    This function allows customization of the logger used by the wreqs module. It can
    either use a provided custom logger or configure the default logger with specified
    parameters.

    Args:
        custom_logger (Optional[logging.Logger], optional): A custom logger to be used
            instead of the default one. If provided, all other parameters are ignored.
            Defaults to None.
        level (int, optional): The logging level to be set. Uses standard logging level
            constants (e.g., logging.INFO, logging.DEBUG). Defaults to logging.INFO.
        format (str, optional): The format string for the log messages.
            Defaults to "%(asctime)s - %(name)s - %(levelname)s - %(message)s".
        filename (Optional[str], optional): If provided, logs will be written to this file.
            If None, logs will be written to the console. Defaults to None.

    Returns:
        None

    Example:
        Using default settings:
        ```python
        from wreqs import configure_logger

        configure_logger()
        ```

        Customizing log level and format:
        ```python
        import logging
        from wreqs import configure_logger

        configure_logger(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
        ```

        Logging to a file:
        ```python
        from wreqs import configure_logger

        configure_logger(filename="wreqs.log")
        ```

        Using a custom logger:
        ```python
        import logging
        from wreqs import configure_logger

        custom_logger = logging.getLogger("my_app.wreqs")
        custom_logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        custom_logger.addHandler(handler)

        configure_logger(custom_logger=custom_logger)
        ```

    Notes:
        - This function modifies the global `logger` variable used throughout the wreqs module.
        - If a custom logger is provided, it will be used as-is, and all other parameters will be ignored.
        - When not using a custom logger, this function removes all existing handlers before adding the new one.
        - The default format includes timestamp, logger name, log level, and message.
    """
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
