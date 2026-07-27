#!/usr/bin/env bash
# Fetch and extract official NVIDIA driver .run installer
set -e

DRIVER_VERSION="${1:-470.256.02}"
ARCH="x86_64"
FILENAME="NVIDIA-Linux-${ARCH}-${DRIVER_VERSION}.run"
DOWNLOAD_URL="https://us.download.nvidia.com/XFree86/Linux-${ARCH}/${DRIVER_VERSION}/${FILENAME}"
WORK_DIR="$(pwd)/build"

echo "[*] Target Driver Version: ${DRIVER_VERSION}"
mkdir -p "${WORK_DIR}"
cd "${WORK_DIR}"

if [ ! -f "${FILENAME}" ]; then
    echo "[*] Downloading ${FILENAME}..."
    curl -fSL -O "${DOWNLOAD_URL}"
else
    echo "[*] Driver installer ${FILENAME} already present in cache."
fi

chmod +x "${FILENAME}"

EXTRACT_DIR="${WORK_DIR}/NVIDIA-Linux-${ARCH}-${DRIVER_VERSION}"
if [ -d "${EXTRACT_DIR}" ]; then
    echo "[*] Removing previous extraction dir ${EXTRACT_DIR}..."
    rm -rf "${EXTRACT_DIR}"
fi

echo "[*] Extracting ${FILENAME}..."
./"${FILENAME}" --extract-only --target "${EXTRACT_DIR}"

echo "[+] Driver extracted to: ${EXTRACT_DIR}"
