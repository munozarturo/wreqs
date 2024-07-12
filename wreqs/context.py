import json
from requests import Request, Response, Session
from typing import Any, Callable, Dict, Optional
import logging


class RequestContext:
    def __init__(self, request: Request) -> None:
        self.request = request
        self.response: Optional[Response] = None

        self.logger: logging.Logger = logging.getLogger(__name__)

        self.session = Session()

    def __enter__(self) -> Response:
        prepared_request = self.session.prepare_request(self.request)
        self.response = self.session.send(prepared_request)
        return self.response

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.response:
            self.response.close()
        self.session.close()


def wrapped_request(req: Request) -> RequestContext:
    return RequestContext(req)
