from flask import Flask, jsonify

app = Flask(__name__)


def get_services_status():
    # Mock implementation for demonstration
    return {"service1": "running", "service2": "stopped", "database": "connected"}


@app.route("/status")
def status():
    status_data = get_services_status()
    return jsonify(status_data)


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(port=9998)
