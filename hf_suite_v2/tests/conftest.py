"""
Pytest configuration and fixtures.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory(prefix="hf_suite_test_") as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db_path(temp_dir: Path) -> Path:
    """Create a temporary database path."""
    return temp_dir / "test_suite.db"


@pytest.fixture
def sample_workflow() -> dict:
    """Sample ComfyUI workflow for testing."""
    return {
        "3": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "v1-5-pruned-emaonly.safetensors"
            }
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "a photo of a cat embedding:easynegative",
                "clip": ["4", 0]
            }
        },
        "10": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "vae-ft-mse-840000-ema-pruned.safetensors"
            }
        },
        "15": {
            "class_type": "LoraLoader",
            "inputs": {
                "lora_name": "my_custom_lora.safetensors",
                "strength_model": 1.0,
                "strength_clip": 1.0
            }
        }
    }


@pytest.fixture
def sample_repo_info() -> dict:
    """Sample repository info for testing."""
    return {
        "repo_id": "test-user/test-model",
        "platform": "huggingface",
        "repo_type": "model",
        "author": "test-user",
        "name": "test-model",
        "downloads": 1000,
        "likes": 50,
        "tags": ["diffusers", "stable-diffusion"],
    }


@pytest.fixture
def sample_download_task() -> dict:
    """Sample download task data."""
    return {
        "repo_id": "test-user/test-model",
        "platform": "huggingface",
        "repo_type": "model",
        "status": "pending",
        "save_path": "/tmp/models",
        "priority": 5,
    }
