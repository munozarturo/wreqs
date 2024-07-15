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

Key features:

- Easy-to-use context manager for HTTP requests
- Configurable retry mechanism
- Timeout handling
- Session management
- Flexible logging capabilities

<!-- omit from toc -->
## Table of Contents

- [Installation](#installation)
- [Quick Start Guide](#quick-start-guide)
- [Advanced Usage](#advanced-usage)
  - [Making Multiple Requests with the Same Session](#making-multiple-requests-with-the-same-session)
  - [Implementing Custom Retry Logic](#implementing-custom-retry-logic)
  - [Handling Timeouts](#handling-timeouts)
  - [Using Retry Callbacks](#using-retry-callbacks)
- [Logging Configuration](#logging-configuration)
  - [Default Logging](#default-logging)
  - [Configuring the Logger](#configuring-the-logger)
  - [Using a Custom Logger](#using-a-custom-logger)
- [Error Handling](#error-handling)
  - [RetryRequestError](#retryrequesterror)
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
   from wreqs import wrapped_request
   import requests
   ```

3. Create a request object:

   ```python
   req = requests.Request('GET', 'https://api.example.com/data')
   ```

4. Use the `wrapped_request` context manager to make the request:

   ```python
   with wrapped_request(req) as response:
       print(response.status_code)
       print(response.json())
   ```

That's it! You've now made a request using `wreqs`. This simple example demonstrates the basic usage, but `wreqs` offers much more functionality, including retry mechanisms, timeout handling, and custom session management.

Here's a slightly more advanced example that includes a retry check:

```python
from wreqs import wrapped_request
import requests

def check_retry(response):
    return response.status_code >= 500

req = requests.Request('GET', 'https://api.example.com/data')

with wrapped_request(req, max_retries=3, check_retry=check_retry) as response:
    if response.status_code == 200:
        print("Success:", response.json())
    else:
        print("Failed after retries. Status code:", response.status_code)
```

This example will retry the request up to 3 times if it receives a 5xx status code.

For more advanced usage and configuration options, please refer to the subsequent sections of this documentation.

## Advanced Usage

The `wreqs` module offers several advanced features to handle complex scenarios and improve your HTTP request workflow. This section covers some of these advanced use cases.

### Making Multiple Requests with the Same Session

One of the powerful features of `wreqs` is the ability to use the same session for multiple requests. This is particularly useful when you need to maintain state between requests, such as for authentication or when dealing with cookies.

Here's an example that demonstrates how to use a single session for authentication and subsequent data retrieval:

```python
import requests
from wreqs import wrapped_request

# Create a session
session = requests.Session()

# Authentication request
auth_req = requests.Request('POST', 'https://api.example.com/login', json={
    'username': 'user',
    'password': 'pass'
})

with wrapped_request(auth_req, session=session) as auth_response:
    if auth_response.status_code == 200:
        print("Authentication successful")
    else:
        print("Authentication failed")
        exit(1)

# Data request using the same authenticated session
data_req = requests.Request('GET', 'https://api.example.com/protected-data')

with wrapped_request(data_req, session=session) as data_response:
    if data_response.status_code == 200:
        print("Data retrieved successfully:", data_response.json())
    else:
        print("Failed to retrieve data. Status code:", data_response.status_code)
```

In this example, the first request authenticates the user, and the second request uses the same session to access protected data. The session automatically handles cookies and other state information between requests.

### Implementing Custom Retry Logic

The `wreqs` module allows you to implement custom retry logic using the `check_retry` parameter. This function should return `True` if a retry should be attempted, and `False` otherwise.

Here's an example that retries on specific status codes and implements an exponential backoff:

```python
import time
from wreqs import wrapped_request
import requests

def check_retry_with_backoff(response):
    if response.status_code in [429, 500, 502, 503, 504]:
        retry_after = int(response.headers.get('Retry-After', 0))
        time.sleep(max(retry_after, 2 ** (response.request.retry_count - 1)))
        return True
    return False

req = requests.Request('GET', 'https://api.example.com/data')

with wrapped_request(req, max_retries=5, check_retry=check_retry_with_backoff) as response:
    print(response.status_code)
    print(response.json())
```

This example retries on specific status codes and implements an exponential backoff strategy.

### Handling Timeouts

`wreqs` allows you to set timeouts for your requests to prevent them from hanging indefinitely. Here's how you can use the timeout feature:

```python
from wreqs import wrapped_request
import requests

req = requests.Request('GET', 'https://api.example.com/slow-endpoint')

try:
    with wrapped_request(req, timeout=5) as response:
        print(response.json())
except requests.Timeout:
    print("The request timed out after 5 seconds")
```

This example sets a 5-second timeout for the request. If the server doesn't respond within 5 seconds, a `Timeout` exception is raised.

### Using Retry Callbacks

You can use the `retry_callback` parameter to perform actions before each retry attempt. This can be useful for logging, updating progress bars, or implementing more complex backoff strategies.

```python
import time
from wreqs import wrapped_request
import requests

def retry_callback(response):
    print(f"Retrying request. Previous status code: {response.status_code}")
    time.sleep(2)  # Wait 2 seconds before retrying

req = requests.Request('GET', 'https://api.example.com/unstable-endpoint')

with wrapped_request(req, max_retries=3, check_retry=lambda r: r.status_code >= 500, retry_callback=retry_callback) as response:
    print("Final response status code:", response.status_code)
```

This example prints a message and waits for 2 seconds before each retry attempt.

These advanced usage examples demonstrate the flexibility and power of the `wreqs` module. By leveraging these features, you can create robust and efficient HTTP request handling in your Python applications.

## Logging Configuration

The `wreqs` module provides flexible logging capabilities to help you track and debug your HTTP requests. You can configure logging at the module level, which will apply to all subsequent uses of `wrapped_request`.

### Default Logging

Out of the box, `wreqs` uses a default logger with minimal configuration:

```python
import wreqs

context = wreqs.wrapped_request(some_request)
```

This will use the default logger, which outputs to the console at the INFO level.

### Configuring the Logger

You can configure the logger using the `configure_logger` function:

```python
import logging
import wreqs

wreqs.configure_logger(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='wreqs.log'
)

# All subsequent calls will use this logger configuration
context1 = wreqs.wrapped_request(some_request)
context2 = wreqs.wrapped_request(another_request)
```

### Using a Custom Logger

For more advanced logging needs, you can create and configure your own logger and set it as the module logger:

```python
import logging
import wreqs

# Create and configure a custom logger
custom_logger = logging.getLogger('my_app.wreqs')
custom_logger.setLevel(logging.INFO)

# Create handlers, set levels, create formatter, and add handlers to the logger
# ... (configure your custom logger as needed)

# Set the custom logger as the module logger
wreqs.configure_logger(custom_logger=custom_logger)

# All subsequent calls will use this custom logger
context = wreqs.wrapped_request(some_request)
```

## Error Handling

Understanding and properly handling errors is crucial when working with HTTP requests. The `wreqs` module is designed to simplify error handling while still providing you with the flexibility to manage various error scenarios.

### RetryRequestError

The primary exception you'll encounter when using `wreqs` is the `RetryRequestError`. This error is raised when all retry attempts have been exhausted without a successful response.

Here's an example of how to handle this error:

```python
from wreqs import wrapped_request, RetryRequestError
import requests

def check_retry(response):
    return response.status_code >= 500

req = requests.Request('GET', 'https://api.example.com/unstable-endpoint')

try:
    with wrapped_request(req, max_retries=3, check_retry=check_retry) as response:
        print("Success:", response.json())
except RetryRequestError as e:
    print(f"All retry attempts failed: {e}")
    # You can access the last response if needed
    last_response = e.last_response
    print(f"Last status code: {last_response.status_code}")
    print(f"Last response content: {last_response.text}")
```

In this example, if all retry attempts fail, a `RetryRequestError` is raised. The error message provides information about the failed request. You can also access the last received response through the `last_response` attribute of the exception.

### Other Exceptions

While `RetryRequestError` is specific to `wreqs`, you should also be prepared to handle other exceptions that may occur during the request process. These are typically exceptions from the underlying `requests` library:

1. `requests.exceptions.Timeout`: Raised when the request times out.
2. `requests.exceptions.ConnectionError`: Raised when there's a network problem (e.g., DNS failure, refused connection).
3. `requests.exceptions.RequestException`: The base exception class for all `requests` exceptions.

Here's an example of how to handle these exceptions:

```python
from wreqs import wrapped_request, RetryRequestError
import requests

req = requests.Request('GET', 'https://api.example.com/data')

try:
    with wrapped_request(req, timeout=5) as response:
        print("Success:", response.json())
except RetryRequestError as e:
    print(f"All retry attempts failed: {e}")
except requests.Timeout:
    print("The request timed out")
except requests.ConnectionError:
    print("A network error occurred")
except requests.RequestException as e:
    print(f"An error occurred while handling the request: {e}")
```

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
