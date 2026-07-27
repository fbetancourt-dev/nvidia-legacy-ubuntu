#!/usr/bin/env python3
"""
NVIDIA Legacy Driver Builder & DKMS Installer Orchestrator
Automates detecting GPU, fetching driver sources, applying modern kernel patches,
compiling modules, and setting up DKMS on modern Ubuntu Linux.
"""

import argparse
import os
import subprocess
import sys

# Import detector and patch_manager components
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import detector
import patch_manager


def run_command(cmd, cwd=None):
    print(f"[*] Executing: {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd)
    if res.returncode != 0:
        print(f"[!] Command failed with exit code {res.returncode}")
        return False
    return True


def setup_dkms(driver_version, source_dir):
    dkms_target_dir = f"/usr/src/nvidia-{driver_version}"
    print(f"[*] Setting up DKMS source tree at {dkms_target_dir}...")
    
    if not os.path.exists(source_dir):
        print(f"[!] Source directory '{source_dir}' does not exist.")
        return False

    kernel_src = os.path.join(source_dir, "kernel")
    if not os.path.exists(kernel_src):
        print(f"[!] Kernel source subdirectory '{kernel_src}' not found.")
        return False

    # Sync kernel module sources to /usr/src/nvidia-<version>
    cmd_copy = f"sudo mkdir -p {dkms_target_dir} && sudo cp -r {kernel_src}/* {dkms_target_dir}/"
    if not run_command(cmd_copy):
        return False

    # Register and build via dkms
    cmd_dkms_add = f"sudo dkms add -m nvidia -v {driver_version} --force"
    cmd_dkms_build = f"sudo dkms build -m nvidia -v {driver_version}"
    cmd_dkms_install = f"sudo dkms install -m nvidia -v {driver_version} --force"

    print("[*] Adding module to DKMS...")
    run_command(cmd_dkms_add)

    print("[*] Building DKMS module...")
    if not run_command(cmd_dkms_build):
        print("[!] DKMS build failed. Check /var/lib/dkms/nvidia/*/build/make.log")
        return False

    print("[*] Installing DKMS module...")
    if not run_command(cmd_dkms_install):
        print("[!] DKMS install failed.")
        return False

    print("[+] DKMS installation completed successfully.")
    return True


def main():
    parser = argparse.ArgumentParser(description="NVIDIA Legacy Driver Builder & Installer")
    parser.add_argument("--detect", action="store_true", help="Detect system GPU and recommend driver version")
    parser.add_argument("--driver", help="Specify driver version (e.g. 470.256.02, 390.157, 340.108)")
    parser.add_argument("--fetch", action="store_true", help="Fetch and extract driver installer")
    parser.add_argument("--patch", action="store_true", help="Apply kernel compatibility patches")
    parser.add_argument("--build", action="store_true", help="Compile kernel modules locally")
    parser.add_argument("--install-dkms", action="store_true", help="Install patched driver via DKMS (requires sudo)")
    parser.add_argument("--all", action="store_true", help="Run complete pipeline (Detect -> Fetch -> Patch -> Build)")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    build_dir = os.path.join(project_root, "build")

    if args.detect or len(sys.argv) == 1:
        detector.main()
        if len(sys.argv) == 1:
            return

    # Determine target driver version
    driver_ver = args.driver
    if not driver_ver:
        gpus = detector.detect_gpus()
        if gpus:
            rec = detector.recommend_driver(gpus[0])
            driver_ver = rec["recommended_version"]
        else:
            driver_ver = "470.256.02"

    print(f"\n[*] Target Driver Version: {driver_ver}")
    driver_extracted_dir = os.path.join(build_dir, f"NVIDIA-Linux-x86_64-{driver_ver}")

    if args.fetch or args.all:
        fetch_script = os.path.join(project_root, "scripts", "fetch_driver.sh")
        if not run_command(f"{fetch_script} {driver_ver}", cwd=project_root):
            sys.exit(1)

    if args.patch or args.all:
        patches_dir = os.path.join(project_root, "patches")
        patches = patch_manager.find_patches_for_driver(patches_dir, driver_ver)
        if not patches:
            print(f"[!] No patches found for driver {driver_ver}")
        else:
            for p in patches:
                print(f"[*] Applying patch: {os.path.basename(p)}")
                ok, output = patch_manager.apply_patch(p, driver_extracted_dir, dry_run=False)
                if ok:
                    print(f"  [✓] Applied successfully.")
                else:
                    print(f"  [!] Patch application failed or already applied:\n{output}")

    if args.build or args.all:
        kernel_dir = os.path.join(driver_extracted_dir, "kernel")
        if not os.path.exists(kernel_dir):
            print(f"[!] Kernel source dir {kernel_dir} not found.")
            sys.exit(1)

        print("[*] Compiling kernel modules locally...")
        kernel_ver = detector.get_kernel_info()
        make_cmd = f"make -C {kernel_dir} -f Makefile NV_KERNEL_SOURCES=/lib/modules/{kernel_ver}/build NV_KERNEL_OUTPUT=/lib/modules/{kernel_ver}/build modules"
        if run_command(make_cmd, cwd=kernel_dir):
            print("[+] Kernel modules compiled successfully!")
        else:
            print("[!] Local compilation failed. Inspect build logs.")

    if args.install_dkms:
        if not setup_dkms(driver_ver, driver_extracted_dir):
            sys.exit(1)


if __name__ == "__main__":
    main()
