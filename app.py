from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info("=== APP STARTING ===")

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

logger.info("=== FLASK APP CREATED ===")

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/api/quote", methods=["POST"])
def submit_quote():
    # Temporarily return dummy data so we can confirm server works
    # Real quoting engine will be re-enabled once server is confirmed healthy
    return jsonify({
        "success": True,
        "client": "Test Client",
        "results": [
            {"carrier": "Good2Go", "rate": "$142/mo", "error": None, "screenshot": None},
            {"carrier": "NatGen", "rate": "$128/mo", "error": None, "screenshot": None},
            {"carrier": "Bristol West", "rate": "$156/mo", "error": None, "screenshot": None}
        ]
    })

@app.route("/api/quotes/history", methods=["GET"])
def get_history():
    return jsonify([])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"=== STARTING ON PORT {port} ===")
    app.run(host="0.0.0.0", port=port, debug=False)
