import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from requests import Request, Timeout
from wreqs import wrapped_request
from wreqs.error import RetryRequestError


@pytest.fixture(scope="session", autouse=True)
def start_server():
    import subprocess
    import time

    server = subprocess.Popen(["python", "tests/app.py"])
    time.sleep(1)
    yield
    server.terminate()


def test_successful_request():
    req = Request("GET", "http://localhost:5000/success")

    with wrapped_request(req) as response:
        assert response.status_code == 200
        assert response.text == "Success"


def test_retry_request():
    req = Request("GET", "http://localhost:5000/retry")

    def check_retry(response):
        return response.status_code == 429

    with pytest.raises(RetryRequestError):
        with wrapped_request(
            req, max_retries=3, check_retry=check_retry, sleep_before_retry=0.1
        ) as response:
            pass


def test_timeout_request():
    req = Request("GET", "http://localhost:5000/timeout")
    with pytest.raises(Timeout):
        with wrapped_request(req, timeout=1) as response:
            pass


def test_custom_retry_logic():
    req = Request("GET", "http://localhost:5000/custom_retry")

    def check_retry(response):
        return response.status_code == 418

    with pytest.raises(RetryRequestError):
        with wrapped_request(req, max_retries=2, check_retry=check_retry) as response:
            pass
