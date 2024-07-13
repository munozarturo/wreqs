import random
import sys
from pathlib import Path
import time


# alternatively package and install `wreqs` module
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import requests
from wreqs import wrapped_request
from wreqs.error import RetryRequestError


BASE_URL = "http://localhost:5000"


def prepare_url(path: str) -> str:
    return f"{BASE_URL}/{path}"


@pytest.fixture(scope="session", autouse=True)
def start_server():
    import subprocess
    import time

    server = subprocess.Popen(["python", "tests/app.py"])
    time.sleep(1)
    yield
    server.terminate()


def test_simple():
    req = requests.Request("GET", prepare_url("/ping"))

    with wrapped_request(req) as response:
        assert response.status_code == 200


def test_with_session_pre_reqs():
    protected_req = requests.Request("GET", prepare_url("/protected/ping"))

    with wrapped_request(protected_req) as response:
        assert response.status_code == 401


def test_with_session():
    with requests.Session() as session:
        auth_req = requests.Request("POST", prepare_url("/auth"))

        with wrapped_request(auth_req, session=session) as response:
            assert response.status_code == 200

        protected_req = requests.Request("GET", prepare_url("/protected/ping"))

        with wrapped_request(protected_req, session=session) as response:
            assert response.status_code == 200


def test_timeout():
    timeout: float = 4
    req = requests.Request("POST", prepare_url("/timeout"), json={"timeout": timeout})

    with wrapped_request(req, timeout=timeout + 1) as response:
        assert response.status_code == 200

    with pytest.raises(requests.Timeout):
        with wrapped_request(req, timeout=timeout - 0.5) as _:
            pytest.fail()


def test_with_retry_pre_reqs():
    signature: str = random.randbytes(4).hex()
    req = requests.Request(
        "POST",
        prepare_url("/retry/number"),
        json={"signature": signature, "succeed_after_attempt": 3},
    )

    def retry_if_not_success(res: requests.Response) -> bool:
        return res.status_code != 200

    with pytest.raises(RetryRequestError):
        with wrapped_request(req, check_retry=retry_if_not_success) as _:
            pytest.fail()


def test_with_retry():
    signature: str = random.randbytes(4).hex()
    req = requests.Request(
        "POST",
        prepare_url("/retry/number"),
        json={"signature": signature, "succeed_after_attempt": 2},
    )

    def retry_if_not_success(res: requests.Response) -> bool:
        return res.status_code != 200

    with wrapped_request(req, check_retry=retry_if_not_success) as response:
        assert response.status_code == 200


def test_with_retry_modified_max():
    signature: str = random.randbytes(4).hex()
    req = requests.Request(
        "POST",
        prepare_url("/retry/number"),
        json={"signature": signature, "succeed_after_attempt": 3},
    )

    def retry_if_not_success(res: requests.Response) -> bool:
        return res.status_code != 200

    with wrapped_request(
        req, check_retry=retry_if_not_success, max_retries=4
    ) as response:
        assert response.status_code == 200


def test_with_retry_and_retry_callback_pre_reqs():
    signature: str = random.randbytes(4).hex()
    req = requests.Request(
        "POST",
        prepare_url("/retry/time"),
        json={"signature": signature, "succeed_after_s": 5},
    )

    def retry_if_not_success(res: requests.Response) -> bool:
        return res.status_code != 200

    def retry_callback(res: requests.Response) -> None:
        time.sleep(1)

    with pytest.raises(RetryRequestError):
        with wrapped_request(
            req, check_retry=retry_if_not_success, retry_callback=retry_callback
        ) as _:
            pytest.fail()


def test_with_retry_and_retry_callback():
    signature: str = random.randbytes(4).hex()
    req = requests.Request(
        "POST",
        prepare_url("/retry/time"),
        json={"signature": signature, "succeed_after_s": 2},
    )

    def retry_if_not_success(res: requests.Response) -> bool:
        return res.status_code != 200

    def retry_callback(res: requests.Response) -> None:
        time.sleep(1)

    with wrapped_request(
        req, check_retry=retry_if_not_success, retry_callback=retry_callback
    ) as response:
        assert response.status_code == 200
