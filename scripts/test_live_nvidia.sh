#!/usr/bin/env bash
# ==============================================================================
# Safe Live Test for Patched NVIDIA Driver with Automatic 10s Self-Restoration
# ==============================================================================

LOG_FILE="/tmp/nvidia_smi_output.txt"
echo "=== Starting Safe NVIDIA Live Test ===" > "$LOG_FILE"
date >> "$LOG_FILE"

# Function to guarantee restoration of Nouveau and GDM3
restore_system() {
  echo "[*] Restoring system graphics..." >> "$LOG_FILE"
  modprobe -r nvidia_drm nvidia_modeset nvidia_uvm nvidia_peermem nvidia 2>> "$LOG_FILE" || true
  modprobe nouveau 2>> "$LOG_FILE" || true
  systemctl start gdm3 2>> "$LOG_FILE" || true
  echo "[+] Restoration complete!" >> "$LOG_FILE"
}

# Trap any unexpected exit to ensure restoration always runs
trap restore_system EXIT

echo "[*] 1. Stopping GDM3 display manager..." >> "$LOG_FILE"
systemctl stop gdm3 || true
sleep 2

echo "[*] 2. Unloading Nouveau driver..." >> "$LOG_FILE"
modprobe -r nouveau 2>> "$LOG_FILE" || true
sleep 1

echo "[*] 3. Loading Patched NVIDIA 470 driver..." >> "$LOG_FILE"
modprobe nvidia 2>> "$LOG_FILE" || true
modprobe nvidia-modeset 2>> "$LOG_FILE" || true
modprobe nvidia-drm 2>> "$LOG_FILE" || true

echo "[*] 4. Running nvidia-smi..." >> "$LOG_FILE"
echo "----------------------------------------------------------------------" >> "$LOG_FILE"
nvidia-smi >> "$LOG_FILE" 2>&1 || echo "[!] nvidia-smi returned non-zero code" >> "$LOG_FILE"
echo "----------------------------------------------------------------------" >> "$LOG_FILE"

echo "[*] 5. Holding state for 10 seconds (Safety Window)..." >> "$LOG_FILE"
sleep 10

echo "[*] 6. Initiating auto-restoration..." >> "$LOG_FILE"
restore_system

echo "=== Test Completed Successfully ===" >> "$LOG_FILE"
