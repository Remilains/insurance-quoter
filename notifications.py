import os
import requests
import logging

logger = logging.getLogger(__name__)

def send_whatsapp_notification(client, results: list):
    """
    Send quote results to WhatsApp group via Twilio API.
    Requires TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM, WHATSAPP_GROUP_TO env vars.
    """
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_WHATSAPP_FROM")  # e.g. whatsapp:+14155238886
    to_number = os.environ.get("WHATSAPP_GROUP_TO")       # e.g. whatsapp:+1XXXXXXXXXX

    if not all([account_sid, auth_token, from_number, to_number]):
        logger.warning("WhatsApp credentials not configured. Skipping notification.")
        return

    # Build message
    lines = [
        f"🚗 *New Quote Ready*",
        f"👤 Client: {client.first_name} {client.last_name}",
        f"📍 ZIP: {client.zip_code}",
        f"🚙 VIN: {client.vin}",
        f"",
        f"📊 *Results:*"
    ]

    for r in results:
        carrier = r["carrier"]
        if r["error"]:
            lines.append(f"❌ {carrier}: Error - {r['error'][:60]}")
        elif r["rate"]:
            lines.append(f"✅ {carrier}: {r['rate']}")
        else:
            lines.append(f"⚠️ {carrier}: Rate not captured (see screenshot)")

    message = "\n".join(lines)

    # Send via Twilio
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    response = requests.post(
        url,
        auth=(account_sid, auth_token),
        data={
            "From": from_number,
            "To": to_number,
            "Body": message
        }
    )

    if response.status_code == 201:
        logger.info("WhatsApp notification sent successfully")
    else:
        logger.error(f"WhatsApp send failed: {response.status_code} {response.text}")
        raise Exception(f"Twilio error: {response.status_code}")
