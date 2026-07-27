#!/usr/bin/env python3
"""
NVIDIA Legacy Driver Patch Manager
Applies compatibility patches for legacy NVIDIA drivers to compile on modern Linux kernels (6.8+ / 7.x).
"""

import argparse
import os
import subprocess
import sys


def find_patches_for_driver(patches_dir, driver_version):
    driver_patch_dir = os.path.join(patches_dir, driver_version)
    if not os.path.isdir(driver_patch_dir):
        return []
    
    patches = []
    for f in sorted(os.listdir(driver_patch_dir)):
        if f.endswith(".patch") or f.endswith(".diff"):
            patches.append(os.path.join(driver_patch_dir, f))
    return patches


def apply_patch(patch_file, target_dir, dry_run=False):
    # -f / --forward prevents interactive prompts on reversed/already applied patches
    cmd = ["patch", "-p1", "-f", "--no-backup-if-mismatch"]
    if dry_run:
        cmd.append("--dry-run")

    with open(patch_file, "r") as f:
        try:
            res = subprocess.run(
                cmd,
                cwd=target_dir,
                stdin=f,
                capture_output=True,
                text=True,
                check=True
            )
            return True, res.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr or e.stdout


def main():
    parser = argparse.ArgumentParser(description="NVIDIA Legacy Driver Patch Manager")
    parser.add_argument("--driver", required=True, help="Target driver version (e.g. 470.256.02, 390.157, 340.108)")
    parser.add_argument("--target", required=True, help="Path to extracted driver source directory")
    parser.add_argument("--apply", action="store_true", help="Apply patches (default is dry-run)")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    patches_dir = os.path.join(project_root, "patches")

    patches = find_patches_for_driver(patches_dir, args.driver)

    print(f"[*] Patch Manager targeting Driver {args.driver}")
    print(f"[*] Driver Directory: {args.target}")

    if not os.path.isdir(args.target):
        print(f"[!] Error: Target directory '{args.target}' does not exist.")
        sys.exit(1)

    if not patches:
        print(f"[!] No local patch files found in patches/{args.driver}/")
        sys.exit(0)

    print(f"[*] Found {len(patches)} patch file(s):")
    for p in patches:
        print(f"    - {os.path.basename(p)}")

    dry_run = not args.apply
    if dry_run:
        print("\n[*] Running in DRY-RUN mode (use --apply to apply changes):")

    all_success = True
    for patch_file in patches:
        patch_name = os.path.basename(patch_file)
        success, output = apply_patch(patch_file, args.target, dry_run=dry_run)
        if success:
            print(f"  [✓] {patch_name}: OK")
        else:
            print(f"  [!] {patch_name}: Output:\n{output}")

    if not all_success:
        sys.exit(1)
    else:
        print("\n[+] Patch operation completed successfully.")


if __name__ == "__main__":
    main()
