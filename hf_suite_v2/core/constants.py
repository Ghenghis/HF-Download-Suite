"""
Application constants and default values.
"""

from pathlib import Path
import os

# Application info
APP_NAME = "HF Download Suite"
APP_VERSION = "2.0.0"
APP_AUTHOR = "HF Suite Team"

# Directories
USER_HOME = Path.home()
APP_DATA_DIR = USER_HOME / ".hf_download_suite"
DATABASE_PATH = APP_DATA_DIR / "suite.db"
LOGS_DIR = APP_DATA_DIR / "logs"
CACHE_DIR = APP_DATA_DIR / "cache"

# Ensure directories exist
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Platform configurations
PLATFORMS = {
    "huggingface": {
        "name": "Hugging Face",
        "icon": "huggingface_logo.png",
        "default_endpoint": "https://huggingface.co",
        "mirror_endpoint": "https://hf-mirror.com",
        "token_env": "HF_TOKEN",
        "models_url": "https://huggingface.co/models",
        "datasets_url": "https://huggingface.co/datasets",
        "token_url": "https://huggingface.co/settings/tokens",
    },
    "modelscope": {
        "name": "ModelScope",
        "icon": "modelscope_logo.png",
        "default_endpoint": "https://modelscope.cn",
        "mirror_endpoint": "https://modelscope.cn",
        "token_env": "MODELSCOPE_API_TOKEN",
        "models_url": "https://modelscope.cn/models",
        "datasets_url": "https://modelscope.cn/datasets",
        "token_url": "https://modelscope.cn/my/myaccesstoken",
    },
}

# Download settings
DEFAULT_MAX_WORKERS = 3
MAX_WORKERS_LIMIT = 8
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 5  # seconds
DEFAULT_CHUNK_SIZE = 8192  # bytes
DEFAULT_TIMEOUT = 300  # seconds

# File type categories for filtering
FILE_CATEGORIES = {
    "checkpoints": {
        "label": "Checkpoints",
        "extensions": [".safetensors", ".ckpt", ".pt", ".pth", ".bin"],
        "patterns": ["**/checkpoint*", "**/model*"],
    },
    "lora": {
        "label": "LoRA",
        "extensions": [".safetensors", ".pt"],
        "patterns": ["**/lora*", "**/adapter*"],
    },
    "vae": {
        "label": "VAE",
        "extensions": [".safetensors", ".pt", ".ckpt"],
        "patterns": ["**/vae*"],
    },
    "controlnet": {
        "label": "ControlNet",
        "extensions": [".safetensors", ".pth"],
        "patterns": ["**/controlnet*", "**/control*"],
    },
    "gguf": {
        "label": "GGUF (Quantized)",
        "extensions": [".gguf"],
        "patterns": ["**/*.gguf"],
    },
    "config": {
        "label": "Config Files",
        "extensions": [".json", ".yaml", ".yml", ".txt"],
        "patterns": ["**/config*", "**/tokenizer*"],
    },
}

# Ignore patterns (files to skip by default)
DEFAULT_IGNORE_PATTERNS = [
    "*.h5",
    "*.ot", 
    "*.msgpack",
    "*.pkl",
    "*.onnx",
    ".*",  # Hidden files
    "__pycache__/*",
    "*.pyc",
]

# UI Constants
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 700
SIDEBAR_WIDTH = 200
CARD_MIN_HEIGHT = 80

# Status values
class DownloadStatus:
    PENDING = "pending"
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Model types
class ModelType:
    CHECKPOINT = "checkpoint"
    LORA = "lora"
    VAE = "vae"
    CONTROLNET = "controlnet"
    EMBEDDING = "embedding"
    CLIP = "clip"
    UPSCALER = "upscaler"
    OTHER = "other"

# List of model types for iteration
MODEL_TYPES = [
    "checkpoint",
    "lora",
    "vae",
    "controlnet",
    "embedding",
    "clip",
    "upscaler",
    "gguf",
    "other",
]

# List of platform keys for iteration
PLATFORM_KEYS = list(PLATFORMS.keys())
