import sys
from pathlib import Path

# alternatively package and install `wreqs` module
sys.path.insert(0, str(Path(__file__).parent.parent))

import random
import time
import pytest
import requests
from wreqs import wreq, wreqs_session
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

    with wreq(req) as response:
        assert response.status_code == 200


def test_with_session_pre_reqs():
    protected_req = requests.Request("GET", prepare_url("/protected/ping"))

    with wreq(protected_req) as response:
        assert response.status_code == 401


def test_with_session():
    with requests.Session() as session:
        auth_req = requests.Request("POST", prepare_url("/auth"))

        with wreq(auth_req, session=session) as response:
            assert response.status_code == 200

        protected_req = requests.Request("GET", prepare_url("/protected/ping"))

        with wreq(protected_req, session=session) as response:
            assert response.status_code == 200


def test_timeout():
    timeout: float = 4
    req = requests.Request("POST", prepare_url("/timeout"), json={"timeout": timeout})

    with wreq(req, timeout=timeout + 1) as response:
        assert response.status_code == 200

    with pytest.raises(requests.Timeout):
        with wreq(req, timeout=timeout - 0.5) as _:
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
        with wreq(req, check_retry=retry_if_not_success) as _:
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

    with wreq(req, check_retry=retry_if_not_success) as response:
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

    with wreq(req, check_retry=retry_if_not_success, max_retries=4) as response:
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
        with wreq(
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

    with wreq(
        req, check_retry=retry_if_not_success, retry_callback=retry_callback
    ) as response:
        assert response.status_code == 200


def test_wreqs_session_basic():
    with wreqs_session():
        req = requests.Request("GET", prepare_url("/ping"))
        with wreq(req) as response:
            assert response.status_code == 200


def test_wreqs_session_multiple_requests():
    with wreqs_session():
        req1 = requests.Request("GET", prepare_url("/ping"))
        req2 = requests.Request("GET", prepare_url("/protected/ping"))

        with wreq(req1) as response1:
            assert response1.status_code == 200

        with wreq(req2) as response2:
            assert response2.status_code == 401


def test_wreqs_session_auth_flow():
    with wreqs_session():
        auth_req = requests.Request("POST", prepare_url("/auth"))
        protected_req = requests.Request("GET", prepare_url("/protected/ping"))

        with wreq(auth_req) as auth_response:
            assert auth_response.status_code == 200

        with wreq(protected_req) as protected_response:
            assert protected_response.status_code == 200


def test_wreqs_session_exception_handling():
    with pytest.raises(requests.Timeout):
        with wreqs_session():
            req = requests.Request("POST", prepare_url("/timeout"), json={"timeout": 2})
            with wreq(req, timeout=1):
                pytest.fail("Should have timed out")


def test_wreqs_session_retry_error():
    def always_retry(res: requests.Response) -> bool:
        return True

    with pytest.raises(RetryRequestError):
        with wreqs_session():
            req = requests.Request("GET", prepare_url("/ping"))
            with wreq(req, check_retry=always_retry, max_retries=3):
                pytest.fail("Should have raised RetryRequestError")


def test_wreqs_session_nested():
    with wreqs_session() as outer_session:
        req1 = requests.Request("GET", prepare_url("/ping"))
        with wreq(req1) as response1:
            assert response1.status_code == 200

        with wreqs_session() as inner_session:
            req2 = requests.Request("GET", prepare_url("/ping"))
            with wreq(req2) as response2:
                assert response2.status_code == 200

        assert outer_session != inner_session


def test_wreqs_session_explicit_vs_implicit():
    with wreqs_session() as session:
        req1 = requests.Request("GET", prepare_url("/ping"))
        req2 = requests.Request("GET", prepare_url("/ping"))

        with wreq(req1, session=session) as response1:
            assert response1.status_code == 200

        with wreq(req2) as response2:
            assert response2.status_code == 200
