"""
CLI module for HF Download Suite.

Provides command-line interface for:
- Downloading models from HuggingFace/ModelScope
- Managing download queue
- Scanning local models
- Configuration management
"""

from .main import cli, main

__all__ = ["cli", "main"]
