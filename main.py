import logging
import requests
from wreqs import wrapped_request, configure_logger

configure_logger(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

req = requests.Request("GET", "https://finance.yahoo.com/gainers/")
with wrapped_request(req, check_retry=lambda r: r.status_code != 200) as resp:
    print(resp)
