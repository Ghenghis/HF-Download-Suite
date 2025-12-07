"""
Tab views for the main window.
"""

from .downloads_tab import DownloadsTab
from .browser_tab import BrowserTab
from .history_tab import HistoryTab
from .local_models_tab import LocalModelsTab
from .settings_tab import SettingsTab
from .profiles_tab import ProfilesTab
from .comfyui_tab import ComfyUITab

__all__ = [
    "DownloadsTab",
    "BrowserTab", 
    "HistoryTab",
    "LocalModelsTab",
    "SettingsTab",
    "ProfilesTab",
    "ComfyUITab",
]
