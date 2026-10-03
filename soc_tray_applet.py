import os
import json
import time
import threading
import subprocess
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item

STATUS_JSON = os.path.expanduser("~/host_audit_exchange/soc_status.json")
VAULT_DIR = os.path.expanduser("~/host_audit_exchange/malware_vault")

def create_icon_image(is_threat):
    # Generates a dynamic 64x64 shield icon (Green = Safe, Red = Threat)
    image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    color = (231, 76, 60, 255) if is_threat else (46, 204, 113, 255)
    
    # Draw a shield shape
    dc.polygon([(32, 4), (60, 14), (60, 36), (32, 60), (4, 36), (4, 14)], fill=color, outline=(255, 255, 255, 200), width=3)
    return image

def get_status():
    if os.path.exists(STATUS_JSON):
        try:
            with open(STATUS_JSON, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"status": "OFFLINE", "processed_files": 0, "quarantined_threats": 0, "latest_block_hash": "N/A"}

def open_vault(icon, item):
    subprocess.run(["xdg-open", VAULT_DIR])

def verify_ledger(icon, item):
    subprocess.run(["kitty", "python3", os.path.expanduser("~/host_audit_exchange/verify_ledger.py")])

def run_tray():
    def update_tooltip(icon):
        while icon.visible:
            data = get_status()
            q_count = data.get("quarantined_threats", 0)
            status_text = data.get("status", "ONLINE")
            block = data.get("latest_block_hash", "N/A")
            
            icon.title = f"Micro-SOC [{status_text}] | Vault: {q_count} | Hash: {block}"
            icon.icon = create_icon_image(q_count > 0)
            time.sleep(5)

    menu = (
        item('Open Malware Vault', open_vault),
        item('Verify Ledger Integrity', verify_ledger),
        item('Exit Applet', lambda icon, item: icon.stop())
    )

    initial_data = get_status()
    has_threats = initial_data.get("quarantined_threats", 0) > 0
    
    icon = pystray.Icon("micro_soc", create_icon_image(has_threats), "Micro-SOC Initializing...", menu)
    
    threading.Thread(target=update_tooltip, args=(icon,), daemon=True).s_start() if hasattr(threading.Thread(target=update_tooltip, args=(icon,), daemon=True), 's_start') else threading.Thread(target=update_tooltip, args=(icon,), daemon=True).start()
    
    icon.run()

if __name__ == "__main__":
    run_tray()
