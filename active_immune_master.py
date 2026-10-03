import os
import json
import hashlib
import subprocess
import time
import shutil
from datetime import datetime

try:
    import yara
    YARA_AVAILABLE = True
except ImportError:
    YARA_AVAILABLE = False

EXCHANGE_DIR = os.path.expanduser("~/host_audit_exchange")
WATCH_DIR = os.path.expanduser("~/Downloads")
LEDGER_PATH = os.path.join(EXCHANGE_DIR, "crypto_audit_ledger.json")
BACKUP_LEDGER_PATH = os.path.join(EXCHANGE_DIR, "crypto_audit_ledger_backup.json")
SEEN_FILE = os.path.join(EXCHANGE_DIR, "seen_files.json")
VAULT_DIR = os.path.join(EXCHANGE_DIR, "malware_vault")
RULES_DIR = os.path.join(EXCHANGE_DIR, "yara_rules")
IOC_BLOCKLIST = os.path.join(EXCHANGE_DIR, "ioc_blocklist.json")
STATUS_JSON = os.path.join(EXCHANGE_DIR, "soc_status.json")
CANARY_DIR = os.path.expanduser("~/Documents")

os.makedirs(VAULT_DIR, exist_ok=True)
os.makedirs(RULES_DIR, exist_ok=True)

CRITICAL_FILES_TO_WATCH = ["/etc/passwd", "/etc/shadow"]

CANARY_FILE = os.path.join(CANARY_DIR, ".financial_passwords_backup.txt")
if not os.path.exists(CANARY_FILE):
    try:
        with open(CANARY_FILE, "w") as f:
            f.write("CONFIDENTIAL: MASTER PASSWORDS AND CRYPTO KEYS. DO NOT ACCESS.")
        os.chmod(CANARY_FILE, 0o400)
    except Exception:
        pass

DEFAULT_RULE = os.path.join(RULES_DIR, "threat_signatures.yar")
if not os.path.exists(DEFAULT_RULE):
    with open(DEFAULT_RULE, "w") as f:
        f.write('''
rule AdvancedThreatSignatures {
    strings:
        $s1 = "EXPLOIT" nocase
        $s2 = "payload" nocase
        $s3 = "eicar" nocase
        $s4 = "ransomware" nocase
    condition:
        any of them
}
''')

compiled_rules = None
if YARA_AVAILABLE:
    try:
        compiled_rules = yara.compile(filepaths={"threats": DEFAULT_RULE})
    except Exception:
        pass

def load_ioc_blocklist():
    if os.path.exists(IOC_BLOCKLIST):
        try:
            with open(IOC_BLOCKLIST, "r") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set(["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"])

def trigger_desktop_alert(title, message, is_critical=False):
    urgency = "critical" if is_critical else "normal"
    try:
        subprocess.run(["notify-send", "-u", urgency, f"SOC: {title}", message], capture_output=True)
        subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"], capture_output=True)
    except Exception:
        pass

def firewall_interdiction(ip_address=None):
    try:
        subprocess.run(["sudo", "nft", "add", "table", "inet", "micro_soc_defense"], capture_output=True)
        subprocess.run(["sudo", "nft", "add", "chain", "inet", "micro_soc_defense", "input", "{ type filter hook input priority 0; policy accept; }"], capture_output=True)
        if ip_address:
            subprocess.run(["sudo", "nft", "add", "rule", "inet", "micro_soc_defense", "input", "ip", "saddr", ip_address, "drop"], capture_output=True)
            print(f"[!] Firewall Interdiction: Dropped traffic from malicious IP {ip_address}")
    except Exception:
        pass

def dns_sinkhole_block(domain):
    # Null-route domain via local hosts or sinkhole interface simulation
    try:
        hosts_entry = f"0.0.0.0 {domain}\n"
        with open("/etc/hosts", "r") as f:
            content = f.read()
        if domain not in content:
            with open("/etc/hosts", "a") as f:
                f.write(hosts_entry)
            print(f"[!] DNS Sinkhole Active: Null-routed {domain}")
    except Exception:
        pass

def snapshot_kernel_modules():
    try:
        result = subprocess.run(["lsmod"], capture_output=True, text=True)
        hasher = hashlib.sha256()
        hasher.update(result.stdout.encode('utf-8'))
        return hasher.hexdigest()
    except Exception:
        return "unknown"

def snapshot_fim_files():
    fim_state = {}
    for filepath in CRITICAL_FILES_TO_WATCH:
        if os.path.exists(filepath):
            try:
                hasher = hashlib.sha256()
                with open(filepath, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        hasher.update(byte_block)
                fim_state[filepath] = hasher.hexdigest()
            except Exception:
                fim_state[filepath] = "unreadable"
    return fim_state

def scan_proc_memory():
    # Scrapes /proc processes for suspicious command line indicators
    anomalies = []
    try:
        for pid in os.listdir("/proc"):
            if pid.isdigit():
                cmdline_path = os.path.join("/proc", pid, "cmdline")
                if os.path.exists(cmdline_path):
                    try:
                        with open(cmdline_path, "r") as f:
                            cmdline = f.read().replace("\x00", " ").strip()
                            if any(term in cmdline.lower() for term in ["nc -e", "bash -i", "python -c 'import socket", "perl -e"]):
                                anomalies.append({"pid": pid, "cmd": cmdline})
                    except Exception:
                        pass
    except Exception:
        pass
    return anomalies

def calculate_chain_hash(previous_hash, data_string):
    hasher = hashlib.sha256()
    hasher.update((previous_hash + data_string).encode('utf-8'))
    return hasher.hexdigest()

def update_status_file(state, processed_count, quarantine_count, last_hash):
    status_data = {
        "status": state,
        "processed_files": processed_count,
        "quarantined_threats": quarantine_count,
        "latest_block_hash": last_hash[:16] if last_hash else "None",
        "updated_at": datetime.utcnow().isoformat()
    }
    try:
        with open(STATUS_JSON, "w") as f:
            json.dump(status_data, f, indent=4)
    except Exception:
        pass

def write_cryptographic_ledger(event_data):
    ledger = []
    previous_hash = "0" * 64
    
    if os.path.exists(LEDGER_PATH):
        try:
            with open(LEDGER_PATH, "r") as f:
                ledger = json.load(f)
                if ledger:
                    previous_hash = ledger[-1].get("current_block_hash", previous_hash)
        except Exception:
            pass

    data_string = json.dumps(event_data, sort_keys=True)
    current_block_hash = calculate_chain_hash(previous_hash, data_string)
    
    event_block = {
        "timestamp": datetime.utcnow().isoformat(),
        "previous_block_hash": previous_hash,
        "current_block_hash": current_block_hash,
        "payload": event_data
    }
    
    ledger.append(event_block)
    with open(LEDGER_PATH, "w") as f:
        json.dump(ledger, f, indent=4)
        
    try:
        shutil.copy(LEDGER_PATH, BACKUP_LEDGER_PATH)
    except Exception:
        pass
    
    syslog_msg = f"MICRO_SOC_GRID: BlockHash={current_block_hash[:16]} Action={event_data.get('action', 'ingest')}"
    subprocess.run(["logger", "-p", "auth.warn", syslog_msg], capture_output=True)
    return current_block_hash

def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()

def save_seen(seen_set):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_set), f)

def quarantine_and_triage(filepath, filename, reason):
    dest_path = os.path.join(VAULT_DIR, filename)
    try:
        shutil.move(filepath, dest_path)
        os.chmod(dest_path, 0o000)
        print(f"[!] QUARANTINED: {filename} -> Vault ({reason})")
        trigger_desktop_alert("Threat Neutralized!", f"File {filename} isolated to malware vault.", is_critical=True)
        firewall_interdiction()
        dns_sinkhole_block("malicious-c2-beacon.local")
    except Exception as e:
        print(f"[!] Quarantine failed for {filename}: {e}")

if __name__ == "__main__":
    print("[*] Fully Loaded Enterprise Micro-SOC Master Engine Initialized (Maximum Paranoia Mode + FIM/Proc/Sinkhole).")
    latest_hash = "0" * 64
    initial_kernel_sig = snapshot_kernel_modules()
    initial_fim_state = snapshot_fim_files()
    
    if not os.path.exists(LEDGER_PATH):
        latest_hash = write_cryptographic_ledger({
            "action": "system_init", 
            "status": "maximum_hardening_active",
            "kernel_baseline": initial_kernel_sig,
            "fim_baseline": initial_fim_state
        })
    else:
        try:
            with open(LEDGER_PATH, "r") as f:
                ledger = json.load(f)
                if ledger:
                    latest_hash = ledger[-1].get("current_block_hash", latest_hash)
        except Exception:
            pass
    
    seen_files = load_seen()
    blocklist = load_ioc_blocklist()
    processed_count = len(seen_files)
    quarantine_count = len(os.listdir(VAULT_DIR)) if os.path.exists(VAULT_DIR) else 0
    
    update_status_file("ONLINE", processed_count, quarantine_count, latest_hash)
    
    while True:
        # 1. Runtime Kernel Integrity Verification
        current_kernel_sig = snapshot_kernel_modules()
        if current_kernel_sig != initial_kernel_sig:
            write_cryptographic_ledger({
                "action": "kernel_integrity_alert",
                "status": "warning",
                "details": "Kernel module state changed unexpectedly."
            })
            trigger_desktop_alert("Kernel Integrity Alert!", "Active kernel modules modified.", is_critical=True)
            initial_kernel_sig = current_kernel_sig

        # 2. File Integrity Monitor (FIM) Verification
        current_fim_state = snapshot_fim_files()
        if current_fim_state != initial_fim_state:
            write_cryptographic_ledger({
                "action": "fim_integrity_alert",
                "status": "critical",
                "details": "Critical system file modified."
            })
            trigger_desktop_alert("FIM Alert!", "Critical system files tampered with!", is_critical=True)
            initial_fim_state = current_fim_state

        # 3. Memory / Process Payload Scraper
        proc_anomalies = scan_proc_memory()
        for anomaly in proc_anomalies:
            write_cryptographic_ledger({
                "action": "memory_payload_alert",
                "status": "critical",
                "payload_details": anomaly
            })
            trigger_desktop_alert("Memory Payload Detected!", f"Suspicious process PID {anomaly['pid']} flagged.", is_critical=True)

        # 4. Folder Watch Ingestion Pipeline
        if os.path.exists(WATCH_DIR):
            for filename in os.listdir(WATCH_DIR):
                filepath = os.path.join(WATCH_DIR, filename)
                if os.path.isfile(filepath) and filename not in seen_files:
                    sha256_hash = hashlib.sha256()
                    try:
                        with open(filepath, "rb") as f:
                            for byte_block in iter(lambda: f.read(4096), b""):
                                sha256_hash.update(byte_block)
                        file_hash = sha256_hash.hexdigest()
                    except Exception:
                        file_hash = "unreadable"

                    matches = []
                    if compiled_rules:
                        try:
                            matches = compiled_rules.match(filepath)
                        except Exception:
                            pass

                    is_yara_threat = len(matches) > 0
                    is_hash_threat = file_hash in blocklist
                    is_threat = is_yara_threat or is_hash_threat
                    threat_reason = "Yara Signature Match" if is_yara_threat else ("Known IOC Hash Match" if is_hash_threat else "Clean")
                    triage_status = "quarantined_vault" if is_threat else "passed_host"

                    event = {
                        "action": "enterprise_intercept",
                        "filename": filename,
                        "sha256": file_hash,
                        "yara_matches": [str(m) for m in matches],
                        "triage_status": triage_status,
                        "reason": threat_reason
                    }
                    latest_hash = write_cryptographic_ledger(event)
                    processed_count += 1

                    if is_threat:
                        quarantine_and_triage(filepath, filename, threat_reason)
                        quarantine_count += 1

                    seen_files.add(filename)
                    save_seen(seen_files)
                    update_status_file("ONLINE", processed_count, quarantine_count, latest_hash)
                    
        time.sleep(2)
