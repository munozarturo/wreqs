# Wrapped Requests "wreqs" module

## Logging Configuration

The `wreqs` module provides flexible logging capabilities to help you track and debug your HTTP requests. By default, the module uses a built-in logger, but you have several options to customize the logging behavior to suit your needs.

### Default Logging

Out of the box, `wreqs` uses a default logger with minimal configuration. If you don't need any special logging setup, you can use the module as is:

```python
import wreqs

context = wreqs.wrapped_request(some_request)
```

This will use the default logger, which outputs to the console at the INFO level.

### Configuring the Default Logger

If you want to adjust the default logger's behavior, you can use the `configure_logger` function:

```python
import logging
import wreqs

wreqs.configure_logger(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='wreqs.log'
)

context = wreqs.wrapped_request(some_request)
```

### Using a Custom Logger

For more advanced logging needs, you can create and configure your own logger and pass it to `wrapped_request`:

```python
import logging
import wreqs

# Create and configure a custom logger
custom_logger = logging.getLogger('my_app.wreqs')
custom_logger.setLevel(logging.INFO)

# Create a file handler
file_handler = logging.FileHandler('my_app_wreqs.log')
file_handler.setLevel(logging.INFO)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create a formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
custom_logger.addHandler(file_handler)
custom_logger.addHandler(console_handler)

# Use the custom logger with wreqs
context = wreqs.wrapped_request(some_request, custom_logger=custom_logger)
```
