#!/usr/bin/env bash
# ==============================================================================
# NVIDIA Legacy Driver Recovery & Fallback Script
# Reverts DKMS installation and restores stock Nouveau graphics driver
# ==============================================================================

set -e

DRIVER_VER="${1:-470.256.02}"

echo "[*] NVIDIA Legacy Driver Recovery Script"
echo "[*] Target Driver Version: ${DRIVER_VER}"

if [ "$EUID" -ne 0 ]; then
  echo "[!] Please run as root (e.g. sudo bash scripts/recovery.sh)"
  exit 1
fi

echo "[*] 1. Removing Nouveau blacklist config..."
if [ -f "/etc/modprobe.d/blacklist-nvidia-nouveau.conf" ]; then
  rm -f /etc/modprobe.d/blacklist-nvidia-nouveau.conf
  echo "    [✓] /etc/modprobe.d/blacklist-nvidia-nouveau.conf removed."
else
  echo "    [i] Blacklist file not found, skipping."
fi

echo "[*] 2. Removing NVIDIA modules from DKMS..."
if dkms status nvidia | grep -q "${DRIVER_VER}"; then
  dkms remove -m nvidia -v "${DRIVER_VER}" --all || true
  echo "    [✓] DKMS module nvidia/${DRIVER_VER} removed."
else
  echo "    [i] DKMS module nvidia/${DRIVER_VER} is not registered, skipping."
fi

echo "[*] 3. Regenerating initramfs..."
update-initramfs -u

echo "=============================================================================="
echo "[+] RECOVERY COMPLETED SUCCESSFULLY!"
echo "[+] Nouveau open-source graphics driver restored."
echo "[+] You can now safely reboot your computer with: sudo reboot"
echo "=============================================================================="
