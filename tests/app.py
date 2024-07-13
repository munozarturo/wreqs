from flask import Flask, Response
import time

app = Flask(__name__)


@app.route("/success")
def success():
    return "Success", 200


@app.route("/retry")
def retry():
    return "Retry", 429


@app.route("/timeout")
def timeout():
    time.sleep(5)  # Simulate a long request
    return "Timeout", 200


@app.route("/custom_retry")
def custom_retry():
    return "Custom Retry", 418  # I'm a teapot


if __name__ == "__main__":
    app.run(port=5000)
