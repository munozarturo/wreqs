import requests
from wreqs import wrapped_request


req = requests.Request("GET", "https://finance.yahoo.com/gainers/")
with wrapped_request(req, check_retry=lambda r: r.status_code != 200) as resp:
    print(resp)
