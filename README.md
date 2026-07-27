# NVIDIA Legacy Driver Builder for Modern Ubuntu

Tools, DKMS patch collections, and automated scripts for compiling and installing legacy NVIDIA proprietary drivers (340.xx, 390.xx, 470.xx series) on modern Ubuntu Linux (Kernel 6.8+ and GCC 13/14+).

## Purpose

Older 2014-era NVIDIA GPUs (Fermi, Kepler, early Maxwell architectures) lack official kernel driver updates for modern Linux releases. This project automates downloading, patching, DKMS module compilation, and installation for modern kernels.

## Project Structure

```
nvidia-legacy-ubuntu/
├── docs/             # Technical documentation and troubleshooting guides
├── patches/          # DKMS kernel patches organized by driver and kernel version
├── scripts/          # Helper scripts (nouveau blacklisting, environment checks)
├── src/              # Python CLI orchestrator and build scripts
├── .gitignore        # Git ignore patterns for build artifacts and temporary files
└── README.md         # Overview and usage instructions
```

## Quick Start

*(Work in Progress)*

## License

MIT
