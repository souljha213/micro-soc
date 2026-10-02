#!/usr/bin/env python3
import os
import json
import urllib.request
import urllib.parse

# Configuration: Set your webhook URL via environment variable or replace directly
WEBHOOK_URL = os.getenv("MICROSOC_WEBHOOK_URL", "YOUR_DISCORD_OR_TELEGRAM_WEBHOOK_URL")

def send_alert(title, description, severity="WARNING"):
    """
    Dispatches a structured security alert to a configured Discord/Telegram webhook.
    """
    if "YOUR_" in WEBHOOK_URL:
        print("[!] Webhook URL not configured. Skipping alert dispatch.")
        return False

    color = 0xFF0000 if severity == "CRITICAL" else 0xFFA500
    
    payload = {
        "username": "Micro-SOC Sentinel",
        "embeds": [{
            "title": f"🛡️ [{severity}] {title}",
            "description": description,
            "color": color,
            "footer": {"text": "Micro-SOC Autonomous Security Enclave"}
        }]
    }

    try:
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as response:
            return response.status == 204 or response.status == 200
    except Exception as e:
        print(f"[!] Failed to dispatch webhook alert: {e}")
        return False

if __name__ == "__main__":
    # Test dispatch
    send_alert("System Initialization", "Micro-SOC Webhook notification daemon online and monitoring.", "INFO")
