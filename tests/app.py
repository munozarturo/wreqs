from collections import defaultdict
import time
from typing import Any
from flask import Flask, Response, json, request

app = Flask(__name__)

SECRET_KEY: str = "some-big-secret"


@app.get("/ping")
def success():
    data: dict[str, Any] = {"message": "success"}
    resp: Response = app.response_class(
        response=json.dumps(data), status=200, mimetype="application/json"
    )
    return resp


@app.post("/auth")
def authenticate():
    data: dict[str, Any] = {"message": "success"}
    resp: Response = app.response_class(
        response=json.dumps(data), status=200, mimetype="application/json"
    )
    resp.set_cookie("auth-token", SECRET_KEY)
    return resp


@app.get("/protected/ping")
def authenticated_only_ping():
    resp: Response = app.response_class(mimetype="application/json")
    if request.cookies.get("auth-token") == SECRET_KEY:
        resp.status = 200
        resp.data = json.dumps({"message": "success"})
    else:
        resp.status = 401
        resp.data = json.dumps({"message": "unauthorized"})
    return resp


@app.post("/timeout")
def timeout():
    req_data: dict[str, Any] = request.json
    timeout: float = req_data["timeout"]

    time.sleep(timeout)

    data: dict[str, Any] = {"message": "success"}
    resp: Response = app.response_class(
        response=json.dumps(data), status=200, mimetype="application/json"
    )
    return resp


num_reqs_by_signature: defaultdict[str, int] = defaultdict(lambda: 0)


@app.post("/retry/number")
def retry_number():
    req_data: dict[str, Any] = request.json
    signature: str = req_data["signature"]
    succeed_after_attempt: int = int(req_data["succeed_after_attempt"])
    num_reqs_by_signature[signature] += 1

    resp: Response = app.response_class(
        response=json.dumps(
            {
                "message": (
                    "success"
                    if num_reqs_by_signature[signature] > succeed_after_attempt
                    else "error"
                )
            }
        ),
        status=200 if num_reqs_by_signature[signature] > succeed_after_attempt else 500,
        mimetype="application/json",
    )
    return resp


signature_first_seen: defaultdict[str, float] = defaultdict(time.time)


@app.post("/retry/time")
def retry_time():
    req_data: dict[str, Any] = request.json
    signature: str = req_data["signature"]
    succeed_after_s: float = float(req_data["succeed_after_s"])

    succeed_time: float = signature_first_seen[signature] + succeed_after_s
    resp: Response = app.response_class(
        response=json.dumps(
            {"message": ("success" if time.time() > succeed_time else "error")}
        ),
        status=200 if time.time() > succeed_time else 500,
        mimetype="application/json",
    )

    print(
        signature,
        signature_first_seen[signature],
        succeed_after_s,
        succeed_time,
        time.time(),
    )

    return resp


if __name__ == "__main__":
    app.run(port=5000)
