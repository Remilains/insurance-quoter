from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import asyncio
import os
import json
import base64
from datetime import datetime
from quoter.engine import ClientInfo, run_all_quotes
from notifications import send_whatsapp_notification
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

# Load credentials from environment variables
def get_credentials():
    return {
        "good2go_user": os.environ.get("GOOD2GO_USER", ""),
        "good2go_pass": os.environ.get("GOOD2GO_PASS", ""),
        "natgen_user": os.environ.get("NATGEN_USER", ""),
        "natgen_pass": os.environ.get("NATGEN_PASS", ""),
        "bw_user": os.environ.get("BW_USER", ""),
        "bw_pass": os.environ.get("BW_PASS", ""),
    }

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/api/quote", methods=["POST"])
def submit_quote():
    data = request.json
    
    # Validate required fields
    required = ["first_name", "last_name", "dob", "gender", "address", "city", "state", "zip_code", "license_number", "date_licensed", "vin"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    client = ClientInfo(
        first_name=data["first_name"],
        last_name=data["last_name"],
        dob=data["dob"],
        gender=data["gender"],
        address=data["address"],
        city=data["city"],
        state=data["state"],
        zip_code=data["zip_code"],
        license_number=data["license_number"],
        date_licensed=data["date_licensed"],
        vin=data["vin"]
    )

    credentials = get_credentials()

    # Run quotes asynchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        results = loop.run_until_complete(run_all_quotes(client, credentials))
    finally:
        loop.close()

    # Format results
    formatted = []
    for r in results:
        result_data = {
            "carrier": r.carrier,
            "rate": r.rate,
            "bill_plan": r.bill_plan,
            "error": r.error,
            "screenshot": None
        }
        # Encode screenshot as base64 if available
        if r.screenshot_path and os.path.exists(r.screenshot_path):
            with open(r.screenshot_path, "rb") as f:
                result_data["screenshot"] = base64.b64encode(f.read()).decode("utf-8")
        formatted.append(result_data)

    # Send WhatsApp notification
    try:
        send_whatsapp_notification(client, formatted)
    except Exception as e:
        logger.error(f"WhatsApp notification failed: {e}")

    # Log the quote
    log_quote(client, formatted)

    return jsonify({
        "success": True,
        "client": f"{client.first_name} {client.last_name}",
        "timestamp": datetime.now().isoformat(),
        "results": formatted
    })

@app.route("/api/quotes/history", methods=["GET"])
def get_history():
    """Return recent quote history"""
    try:
        with open("quotes_log.json", "r") as f:
            history = json.load(f)
        return jsonify(history[-50:])  # Last 50 quotes
    except FileNotFoundError:
        return jsonify([])

def log_quote(client: ClientInfo, results: list):
    """Log quote to file"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "client": f"{client.first_name} {client.last_name}",
        "zip": client.zip_code,
        "vin": client.vin,
        "results": [{"carrier": r["carrier"], "rate": r["rate"], "error": r["error"]} for r in results]
    }
    
    history = []
    try:
        with open("quotes_log.json", "r") as f:
            history = json.load(f)
    except FileNotFoundError:
        pass
    
    history.append(entry)
    
    with open("quotes_log.json", "w") as f:
        json.dump(history, f, indent=2)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
