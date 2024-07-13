import requests
from wreqs import wrapped_request


req = requests.Request("GET", "https://finance.yahoo.com/gainers/")
with wrapped_request(req) as resp:
    print(resp)
