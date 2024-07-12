# Wrapped Requests "wreqs" module

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
