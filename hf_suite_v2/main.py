#!/usr/bin/env python3
"""
HF Download Suite v2 - Main Entry Point

A comprehensive HuggingFace model downloader with queue management,
multi-platform support, and ComfyUI integration.

Usage:
    python main.py

Requirements:
    - Python 3.10+
    - PyQt6
    - huggingface_hub
    - See requirements.txt for full list
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hf_suite_v2.ui.app import run_app


def main():
    """Main entry point."""
    return run_app()


if __name__ == "__main__":
    sys.exit(main())
