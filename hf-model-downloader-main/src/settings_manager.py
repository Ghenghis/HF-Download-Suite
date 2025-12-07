
import json
import os
from typing import Any, Dict

CONFIG_DIR_NAME = ".hf_model_suite"
CONFIG_FILE_NAME = "settings.json"


def get_config_dir() -> str:
    home = os.path.expanduser("~")
    return os.path.join(home, CONFIG_DIR_NAME)


def get_config_path() -> str:
    return os.path.join(get_config_dir(), CONFIG_FILE_NAME)


def get_default_settings() -> Dict[str, Any]:
    return {
        "token": "",
        "default_save_path": "",
        "named_locations": [],
        "open_folder_after_download": True,
        "comfy_root": "",
        "recent_repos": [],
        "last_platform": "Hugging Face",
        "last_repo_type": "Model",
    }


def load_settings() -> Dict[str, Any]:
    cfg_path = get_config_path()
    data = get_default_settings()
    try:
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data.update(loaded)
    except Exception:
        pass
    return data


def save_settings(settings: Dict[str, Any]) -> None:
    cfg_dir = get_config_dir()
    os.makedirs(cfg_dir, exist_ok=True)
    cfg_path = get_config_path()
    safe = dict(get_default_settings())
    safe.update(settings or {})
    try:
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(safe, f, indent=2)
    except Exception:
        pass
