# Micro-SOC: Engineering Architecture & Threat Model

## 1. Threat Model & Security Objectives
Modern Linux workstations face persistent risks from local privilege escalation, unauthorized kernel injections, credential harvesting, and command-and-control (C2) beaconing. `Micro-SOC` assumes a **zero-trust host model**, operating under the premise that perimeter defenses can fail and that real-time runtime inspection and automated containment must happen locally at the kernel and user-space boundary.

### Primary Vectors Addressed:
* **Malicious Payloads & Droppers:** Ingested files via downloads or removable media.
* **Rootkits & Kernel Tampering:** Unauthorized `lsmod` modifications and driver insertions.
* **Credential Exposure & Canary Traps:** Unauthorized access to high-value configuration files or decoy traps.
* **Exfiltration & C2 Beacons:** Malicious outbound connections and unauthorized DNS resolutions.
