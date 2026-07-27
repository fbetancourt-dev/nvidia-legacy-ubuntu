#!/usr/bin/env python3
"""
NVIDIA Legacy Driver Hardware & System Detector
Detects GPU PCI details, Linux kernel version, GCC version, and recommends the appropriate legacy driver branch.
"""

import json
import os
import re
import subprocess
import sys


def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        return e.stdout.strip() if e.stdout else ""


def get_kernel_info():
    uname = run_cmd("uname -r")
    return uname


def get_gcc_version():
    output = run_cmd("gcc --version")
    if output:
        first_line = output.splitlines()[0]
        match = re.search(r'(\d+\.\d+\.\d+)', first_line)
        if match:
            return match.group(1)
    return "Not installed"


def check_dkms_and_headers():
    dkms_installed = subprocess.run("which dkms", shell=True, capture_output=True).returncode == 0
    kernel_ver = get_kernel_info()
    headers_path = f"/usr/src/linux-headers-{kernel_ver}"
    headers_installed = os.path.exists(headers_path) or os.path.exists(f"/lib/modules/{kernel_ver}/build")
    return {
        "dkms_installed": dkms_installed,
        "headers_installed": headers_installed,
        "headers_path": headers_path if headers_installed else None
    }


def detect_gpus():
    pci_output = run_cmd("lspci -nn")
    gpus = []

    for line in pci_output.splitlines():
        if re.search(r'VGA|3D|Display', line, re.IGNORECASE) and 'NVIDIA' in line:
            # Extract PCI address, description, and ID [vendor:device]
            pci_addr = line.split()[0]
            match_id = re.search(r'\[([0-9a-fA-F]{4}:[0-9a-fA-F]{4})\]', line)
            device_id = match_id.group(1) if match_id else "Unknown"
            
            gpus.append({
                "pci_address": pci_addr,
                "description": line,
                "device_id": device_id
            })

    return gpus


def recommend_driver(gpu_info):
    desc = gpu_info.get("description", "").lower()
    dev_id = gpu_info.get("device_id", "").lower()

    # Fermi / Tesla architecture check (GeForce 400M, 500M, 610M, GT 630M Fermi, NVS) -> 340.xx
    if any(k in desc for k in ["fermi", "gf108", "gf119", "gf106", "gf100", "gt 610m", "gt 520m", "gt 420m", "nvs 5200m"]):
        return {
            "series": "340.xx",
            "recommended_version": "340.108",
            "notes": "Fermi architecture (Legacy 340.xx). Requires heavy kernel patches for Linux 6.x+."
        }

    # Kepler architecture (GK104, GK107, GK208, GT 750M, GT 740M, GTX 660M, Quadro K-series) -> 470.xx / 390.xx
    if any(k in desc for k in ["gk107", "gk104", "gk208", "gk110", "gt 750m", "gt 740m", "gtx 660m", "gtx 760m", "gtx 770m", "gtx 780m", "quadro k"]):
        return {
            "series": "470.xx",
            "recommended_version": "470.256.02",
            "alternative_series": "390.157",
            "notes": "Kepler architecture (Legacy 470.xx / 390.xx). Requires DKMS patches for Linux 6.8+."
        }

    # Maxwell architecture (GM107, GM204, GTX 750 Ti, GTX 860M Maxwell, GTX 960M, etc.) -> 470.xx / 535.xx
    if any(k in desc for k in ["maxwell", "gm107", "gm204", "gm206", "gtx 750 ti", "gtx 960m", "gtx 970m"]):
        return {
            "series": "470.xx / 535.xx",
            "recommended_version": "470.256.02",
            "notes": "Maxwell architecture. Supported by 470.xx or 535.xx legacy branches."
        }

    # General Fallback for 2014-era NVIDIA GPUs
    return {
        "series": "470.xx / 390.xx",
        "recommended_version": "470.256.02",
        "notes": "2014-era GPU detected. Check specific chip ID for exact driver branch."
    }


def main():
    kernel = get_kernel_info()
    gcc = get_gcc_version()
    dkms_headers = check_dkms_and_headers()
    gpus = detect_gpus()

    report = {
        "system": {
            "kernel_version": kernel,
            "gcc_version": gcc,
            "dkms_installed": dkms_headers["dkms_installed"],
            "headers_installed": dkms_headers["headers_installed"],
            "headers_path": dkms_headers["headers_path"]
        },
        "gpus": []
    }

    for gpu in gpus:
        rec = recommend_driver(gpu)
        report["gpus"].append({
            "gpu": gpu,
            "recommendation": rec
        })

    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))
        return

    print("=" * 60)
    print("      NVIDIA Legacy Driver Hardware & System Detector      ")
    print("=" * 60)
    print(f" Kernel Version:  {kernel}")
    print(f" GCC Version:    {gcc}")
    print(f" DKMS Installed: {'YES' if dkms_headers['dkms_installed'] else 'NO'}")
    print(f" Linux Headers:  {'YES (' + str(dkms_headers['headers_path']) + ')' if dkms_headers['headers_installed'] else 'NO'}")
    print("-" * 60)

    if not gpus:
        print(" [!] No NVIDIA GPUs detected via lspci.")
    else:
        for idx, item in enumerate(report["gpus"], 1):
            gpu = item["gpu"]
            rec = item["recommendation"]
            print(f" GPU #{idx}: {gpu['description']}")
            print(f"  ├─ Device ID:    [{gpu['device_id']}]")
            print(f"  ├─ Recommended:  Series {rec['series']} (Driver {rec['recommended_version']})")
            print(f"  └─ Notes:        {rec['notes']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
