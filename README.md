<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://www.munozarturo.com/assets/wreqs/logo-github-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://www.munozarturo.com/assets/wreqs/logo-github-light.svg">
    <img alt="wreqs" src="https://www.munozarturo.com/assets/wreqs/logo-github-light.svg" width="50%" height="40%">
  </picture>
</div>

<!-- omit from toc -->
# wreqs: wrapped requests

The **wreqs** module is a powerful wrapper around the popular `requests` library, designed to simplify and enhance HTTP request handling in Python. It provides a context manager for making HTTP requests with built-in retry logic, timeout handling, and session management.

<!-- omit from toc -->
## Table of Contents

- [Installation](#installation)
- [Quick Start Guide](#quick-start-guide)
- [Advanced Usage](#advanced-usage)
  - [Making Multiple Requests with the Same Session](#making-multiple-requests-with-the-same-session)
  - [Implementing Custom Retry Logic](#implementing-custom-retry-logic)
  - [Handling Timeouts](#handling-timeouts)
  - [Using Retry Callbacks](#using-retry-callbacks)
  - [Using Proxy Rotation](#using-proxy-rotation)
- [Logging Configuration](#logging-configuration)
  - [Default Logging](#default-logging)
  - [Configuring the Logger](#configuring-the-logger)
  - [Using a Custom Logger](#using-a-custom-logger)
- [Error Handling](#error-handling)
  - [`wreqs` Specific Errors](#wreqs-specific-errors)
    - [RetryRequestError](#retryrequesterror)
  - [Common `requests` Exceptions](#common-requests-exceptions)
  - [Other Exceptions](#other-exceptions)
- [Development and Publishing](#development-and-publishing)
  - [Testing](#testing)
  - [CI/CD](#cicd)
  - [Publishing a New Version](#publishing-a-new-version)

## Installation

To install the `wreqs` module, use pip:

```bash
pip install wreqs
```

## Quick Start Guide

Getting started with the `wreqs` module is simple. Follow these steps to make your first wrapped request:

1. First, install the module:

   ```bash
   pip install wreqs
   ```

2. Import the necessary components:

   ```python
   from wreqs import wreq
   import requests
   ```

3. Create a request object:

   ```python
   req = requests.Request("GET", "https://api.example.com/data")
   ```

4. Use the `wreq` context manager to make the request:

   ```python
   with wreq(req) as response:
       print(response.status_code)
       print(response.json())
   ```

That's it! You've now made a request using `wreqs`. This simple example demonstrates the basic usage, but `wreqs` offers much more functionality, including retry mechanisms, timeout handling, and custom session management.

Here's a slightly more advanced example that includes a retry check:

```python
from wreqs import wreq
import requests

def check_retry(response: requests.Response) -> bool:
    return response.status_code >= 500

req = requests.Request("GET", "https://api.example.com/data")
with wreq(req, max_retries=3, check_retry=check_retry) as response:
    print(response.json())
```

This example will retry the request up to 3 times if it receives a 5xx status code. If all requests fail it will throw a `RequestRetryError` see [Error Handling](#error-handling) for more information on errors.

For more advanced usage and configuration options, please refer to the subsequent sections of this documentation.

## Advanced Usage

The `wreqs` module offers several advanced features to handle complex scenarios and improve your HTTP request workflow.

### Making Multiple Requests with the Same Session

`wreqs` provides a convenient `wreqs_session` context manager that automatically manages session creation, use, and cleanup. This simplifies the process of making multiple requests with the same session.

Here's an example that demonstrates how to use `wreqs_session` for authentication and subsequent data retrieval:

```python
from wreqs import wreq, wreqs_session
from requests import Request

with wreqs_session():
    # authentication request
    auth_req = Request("POST", "https://api.example.com/login", json={
        "username": "user",
        "password": "pass"
    })
    with wreq(auth_req) as auth_response:
        if auth_response.status_code != 200:
            raise Exception("Failed to authenticate.")

    # data request using the same authenticated session
    data_req = Request("GET", "https://api.example.com/protected-data")
    with wreq(data_req) as data_response:
        print(data_response.json())
```

In this example, the `wreqs_session` context manager automatically creates and manages a session for all requests within its block. The first request authenticates the user, and the second request uses the same session to access protected data. The session automatically handles cookies and other state information between requests.

This approach is equivalent to manually creating and managing a session, as shown in the following example:

```python
import requests
from wreqs import wreq

session = requests.Session()

auth_req = requests.Request(...)
with wreq(auth_req, session=session) as auth_response: # session explicitly defined
    ...

data_req = requests.Request(...)
with wreq(data_req, session=session) as data_response: # session explicitly defined
    ...
```

It is still possible to use a different session within a `wreqs_session` context so long as it is explicitly defined.

```python
from wreqs import wreq, wreqs_session
from requests import Request, Session

with wreqs_session():
    auth_req = Request(...)
    with wreq(auth_req) as auth_response: # will use wreqs_session
        ...

    other_session = Session()
    data_req = Request(...)
    with wreq(data_req, session=other_session) as data_response: # will use other_session
        ...
```

### Implementing Custom Retry Logic

The `wreqs` module allows you to implement custom retry logic using the `check_retry` parameter. This function should return `True` if a retry should be attempted, and `False` otherwise.

Here's an example that retries on specific status codes and implements an exponential backoff:

```python
import time
from wreqs import wreq
import requests

def check_retry_with_backoff(response: requests.Response) -> bool:
    if response.status_code in [429, 500, 502, 503, 504]:
        retry_after = int(response.headers.get("Retry-After", 0))
        time.sleep(max(retry_after, 2 ** (response.request.retry_count - 1)))
        return True
    return False

req = requests.Request("GET", "https://api.example.com/data")
with wreq(req, max_retries=5, check_retry=check_retry_with_backoff) as response:
    print(response.json())
```

This example retries on specific status codes and implements an exponential backoff strategy.

### Handling Timeouts

`wreqs` allows you to set timeouts for your requests to prevent them from hanging indefinitely. Here"s how you can use the timeout feature:

```python
from wreqs import wreq
import requests

req = requests.Request("GET", "https://api.example.com/slow-endpoint")

try:
    with wreq(req, timeout=5) as response:
        print(response.json())
except requests.Timeout:
    print("The request timed out after 5 seconds")
```

This example sets a 5-second timeout for the request. If the server doesn't respond within 5 seconds, a `Timeout` exception is raised.

### Using Retry Callbacks

You can use the `retry_callback` parameter to perform actions before each retry attempt. This can be useful for logging, updating progress bars, or implementing more complex backoff strategies.

```python
import time
from wreqs import wreq
import requests

def check_retry(response: requests.Response) -> bool:
    return response.status_code != 200

def retry_callback(response):
    print(f"Retrying request. Previous status code: {response.status_code}")
    time.sleep(2)  # Wait 2 seconds before retrying

req = requests.Request("GET", "https://api.example.com/unstable-endpoint")
with wreq(req, check_retry=check_retry, retry_callback=retry_callback) as res:
    print(res.json())
```

This example prints a message and waits for 2 seconds before each retry attempt.

These advanced usage examples demonstrate the flexibility and power of the `wreqs` module. By leveraging these features, you can create robust and efficient HTTP request handling in your Python applications.

### Using Proxy Rotation

`wreqs` now supports proxy rotation, allowing you to distribute your requests across multiple proxies. This can be useful for avoiding rate limits or accessing region-restricted content. Here's how to use this feature:

```python
from wreqs import wreq
import requests

proxies = [
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080",
    "http://proxy3.example.com:8080",
]

req = requests.Request("GET", "https://api.example.com/data")

with wreq(req, max_retries=3, proxies=proxies) as response:
    print(response.json())
```

In this example, wreqs will rotate through the provided list of proxies for each request or retry attempt. If a request fails, it will automatically use the next proxy in the list for the retry.

Note:

- Proxies should be provided as a list of strings in the format "<http://host:port>" or "<https://host:port>".
- The proxy rotation is done in a round-robin fashion.
- If no proxies are provided, wreqs will use the default network connection.

## Logging Configuration

The `wreqs` module provides flexible logging capabilities to help you track and debug your HTTP requests. You can configure logging at the module level, which will apply to all subsequent uses of `wreq`.

### Default Logging

Out of the box, `wreqs` uses a default logger with minimal configuration:

```python
import wreqs

context = wreqs.wreq(some_request)
```

This will use the default logger, which outputs to the console at the INFO level.

### Configuring the Logger

You can configure the logger using the `configure_logger` function:

```python
import logging
import wreqs

wreqs.configure_logger(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="wreqs.log"
)

# all subsequent calls will use this logger configuration
context1 = wreqs.wreq(some_request)
context2 = wreqs.wreq(another_request)
```

### Using a Custom Logger

For more advanced logging needs, you can create and configure your own logger and set it as the module logger:

```python
import logging
import wreqs

# create and configure a custom logger
custom_logger = logging.getLogger("my_app.wreqs")
custom_logger.setLevel(logging.INFO)

# create handlers, set levels, create formatter, and add handlers to the logger
# ... (configure your custom logger as needed)

# set the custom logger as the module logger
wreqs.configure_logger(custom_logger=custom_logger)

# all subsequent calls will use this custom logger
context = wreqs.wreq(some_request)
```

## Error Handling

The `wreqs` module is designed for simplicity and doesn't include complex error handling mechanisms. The context manager re-throws any errors that occur inside the wrapped request.

### `wreqs` Specific Errors

#### RetryRequestError

Thrown when all retry attempts have failed.

```python
from wreqs import wreq, RetryRequestError
import requests

def check_retry(response):
    return response.status_code >= 500

req = requests.Request("GET", "https://api.example.com/unstable-endpoint")

try:
    with wreq(req, max_retries=3, check_retry=check_retry) as response:
        print(response.json())
except RetryRequestError as e:
    print(f"All retry attempts failed: {e}")
```

### Common `requests` Exceptions

`wreqs` uses the `requests` library internally, so you may encounter these common exceptions:

1. `requests.exceptions.Timeout`: Raised when the request times out.
2. `requests.exceptions.ConnectionError`: Raised when there's a network problem (e.g., DNS failure, refused connection).
3. `requests.exceptions.RequestException`: The base exception class for all `requests` exceptions.

### Other Exceptions

Any other exceptions that can be raised by the code inside the `with wreq(...) as response:` block will be propagated as-is.

Example of handling multiple exception types:

```python
from wreqs import wreq, RetryRequestError
import requests

req = requests.Request("GET", "https://api.example.com/data")

try:
    with wreq(req, timeout=5) as response:
        data = response.json()
        process_data(data)
except DataProcessingError as e: # error thrown by process_data
    ...
```

This approach allows you to handle specific exceptions as needed while keeping error management straightforward.

## Development and Publishing

### Testing

Run tests locally:

```bash
pip install .[dev]
pytest
```

### CI/CD

This project uses GitHub Actions for Continuous Integration and Continuous Deployment:

1. **Pull Request Checks**: Automatically run tests on all pull requests to the main branch.
2. **Automated Publishing**: Triggers package build and publication to PyPI when a new version tag is pushed.

### Publishing a New Version

1. Create a new branch for the version bump:

   ```bash
   git checkout -b bump-vx.y.z
   ```

2. Update the version in `setup.py` following [Semantic Versioning](https://semver.org/).

3. Commit changes:

   ```bash
   git add setup.py
   git commit -m "pack: bump version to x.y.z"
   ```

4. Create and push a new tag on the bump branch:

   ```bash
   git tag vx.y.z
   git push origin bump-vx.y.z --tags
   ```

   Replace `x.y.z` with the new version number.

5. Push the branch and create a pull request:

   ```bash
   git push origin bump-vx.y.z
   ```

   Then create a pull request on GitHub from this branch to main.

6. After the pull request is approved and merged, the tag will be part of the main branch.

7. To publish the new version to PyPI:
   - Go to the "Actions" tab in your GitHub repository
   - Select the "Publish Python distribution to PyPI" workflow
   - Click "Run workflow"
   - Enter the version tag you created (e.g., v1.2.3) and click "Run workflow"

8. The GitHub Action will build, test, and publish the new version to PyPI based on the specified tag.

Note: This process allows you to control exactly when the package is published. You can create and push tags on feature branches without triggering the publish process, and you can choose to publish specific tags at any time using the manual workflow trigger. The tag becomes part of the main branch history when the pull request is merged.
