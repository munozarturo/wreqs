import json
from typing import Any, Dict, Union

from requests import Request, Response


def _format_content(content: Any) -> Any:
    """
    Formats the given content for consistent representation.

    This method attempts to parse strings as JSON, leaves dictionaries and
    iterables unchanged, and converts other types to strings.

    Args:
        content (Any): The content to be formatted.

    Returns:
        Any: The formatted content. If the input is a valid JSON string,
            it returns the parsed JSON. For dict, list, or tuple, it
            returns the input unchanged. For all other types, it
            returns their string representation.
    """
    if isinstance(content, (dict, list, tuple)):
        return content
    elif isinstance(content, str):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content
    else:
        return str(content)


def prettify_request_str(
    request: Request, verbose: Union[bool, Dict[str, bool]] = False
) -> str:
    """
    Formats a Request object into a human-readable string representation.

    This method takes a Request object and returns a string that summarizes its contents.
    The level of detail in the output is controlled by the 'verbose' parameter.

    Args:
        request (Request): The Request object to be formatted.
        verbose (bool, Dict[str, bool], optional): Controls the verbosity of the output.
            - If False (default), returns a compact single-line summary.
            - If True, returns a detailed multi-line representation.
            - If a dict, allows fine-grained control over which fields are verbose.
            Keys are field names, values are booleans indicating verbosity.

    Returns:
        str: A formatted string representation of the request.

    The output always starts with "[METHOD] URL", followed by a JSON object (single-line
    or multi-line, depending on verbosity) containing request details.

    Fields included in the output:
    - headers: Request headers
    - cookies: Request cookies
    - params: URL parameters
    - data: Request body data
    - json: JSON payload
    - auth: Authentication information

    For non-verbose output, the JSON object contains the length of each field (or "present" for non-length fields).
    For verbose output, it contains the full content of each field.

    Examples:
        # Non-verbose output
        req = Request('POST', 'https://api.example.com/users', json={"name": "John"})
        print(RequestContext._prettify_request_str(req))
        # Output: [POST] https://api.example.com/users {"headers":1,"json":1}

        # Verbose output
        print(RequestContext._prettify_request_str(req, verbose=True))
        # Output:
        # [POST] https://api.example.com/users
        # {
        #   "headers": {
        #     "Content-Type": "application/json"
        #   },
        #   "json": {
        #     "name": "John"
        #   }
        # }

        # Selectively verbose output
        print(RequestContext._prettify_request_str(req, verbose={"headers": False, "json": True}))
        # Output:
        # [POST] https://api.example.com/users
        # {
        #   "headers": 1,
        #   "json": {
        #     "name": "John"
        #   }
        # }
    """
    basic_info = f"[{request.method}] {request.url}"

    request_dict = {
        "headers": _format_content(request.headers) if request.headers else {},
        "cookies": _format_content(request.cookies) if request.cookies else {},
        "params": _format_content(request.params) if request.params else {},
        "data": _format_content(request.data) if request.data else {},
        "json": _format_content(request.json) if request.json else {},
        "auth": str(request.auth) if request.auth else None,
    }

    request_dict = {k: v for k, v in request_dict.items() if v}

    if isinstance(verbose, dict):
        default_verbose = True
        json_dict = {
            k: (
                v
                if verbose.get(k, default_verbose)
                else len(v) if isinstance(v, (dict, list, str)) else "present"
            )
            for k, v in request_dict.items()
        }
        json_str = json.dumps(json_dict, indent=2, sort_keys=True)
        return f"{basic_info}\n{json_str}"
    elif verbose:
        json_str = json.dumps(request_dict, indent=2, sort_keys=True)
        return f"{basic_info}\n{json_str}"
    else:
        summary_dict = {
            key: (len(value) if isinstance(value, (dict, list, str)) else "present")
            for key, value in request_dict.items()
        }
        json_str = json.dumps(summary_dict, separators=(",", ":"))
        return f"{basic_info} {json_str}"


def prettify_response_str(
    response: Response, verbose: Union[bool, Dict[str, bool]] = False
) -> str:
    """
    Formats a Response object into a human-readable string representation.

    This method takes a Response object and returns a string that summarizes its contents.
    The level of detail in the output is controlled by the 'verbose' parameter.

    Args:
        response (Response): The Response object to be formatted.
        verbose (bool, Dict[str, bool], optional): Controls the verbosity of the output.
            - If False (default), returns a compact single-line summary.
            - If True, returns a detailed multi-line representation.
            - If a dict, allows fine-grained control over which fields are verbose.
            Keys are field names, values are booleans indicating verbosity.

    Returns:
        str: A formatted string representation of the response.

    The output always starts with "[STATUS_CODE] URL", followed by a JSON object (single-line
    or multi-line, depending on verbosity) containing response details.

    Fields included in the output:
    - headers: Response headers
    - cookies: Response cookies
    - elapsed: Time elapsed for the request
    - encoding: Response encoding
    - reason: Reason phrase for the status code
    - content: Response body content

    For non-verbose output, the JSON object contains the length of each field (or the actual value for 'elapsed').
    For verbose output, it contains the full content of each field.

    Examples:
        # Non-verbose output
        resp = Response()
        resp.status_code = 200
        resp.url = 'https://api.example.com/users'
        resp.elapsed = timedelta(seconds=0.5)
        resp._content = b'{"id": 1, "name": "John"}'
        print(RequestContext._prettify_response_str(resp))
        # Output: [200] https://api.example.com/users {"headers":0,"elapsed":"0:00:00.500000","content":24}

        # Verbose output
        print(RequestContext._prettify_response_str(resp, verbose=True))
        # Output:
        # [200] https://api.example.com/users
        # {
        #   "content": {
        #     "id": 1,
        #     "name": "John"
        #   },
        #   "elapsed": "0:00:00.500000",
        #   "headers": {}
        # }

        # Selectively verbose output
        print(RequestContext._prettify_response_str(resp, verbose={"headers": False, "content": True}))
        # Output:
        # [200] https://api.example.com/users
        # {
        #   "content": {
        #     "id": 1,
        #     "name": "John"
        #   },
        #   "elapsed": "0:00:00.500000",
        #   "headers": 0
        # }
    """
    basic_info = f"[{response.status_code}] {response.url}"

    response_dict = {
        "headers": dict(response.headers),
        "cookies": dict(response.cookies),
        "elapsed": str(response.elapsed),
        "encoding": response.encoding,
        "reason": response.reason,
        "content": _format_content(response.text),
    }

    response_dict = {k: v for k, v in response_dict.items() if v}

    if isinstance(verbose, dict):
        default_verbose = True
        json_dict = {
            k: (
                v
                if verbose.get(k, default_verbose) or k == "elapsed"
                else len(v) if isinstance(v, (dict, list, str)) else "present"
            )
            for k, v in response_dict.items()
        }
        json_str = json.dumps(json_dict, indent=2, sort_keys=True)
        return f"{basic_info}\n{json_str}"
    elif verbose:
        json_str = json.dumps(response_dict, indent=2, sort_keys=True)
        return f"{basic_info}\n{json_str}"
    else:
        summary_dict = {
            key: (
                value
                if key == "elapsed"
                else (len(value) if isinstance(value, (dict, list, str)) else "present")
            )
            for key, value in response_dict.items()
        }
        json_str = json.dumps(summary_dict, separators=(",", ":"))
        return f"{basic_info} {json_str}"
