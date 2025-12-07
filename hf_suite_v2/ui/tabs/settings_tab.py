"""
Settings tab - Application configuration.
"""

import logging
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QFrame, QLabel, QLineEdit, QPushButton, QComboBox,
    QCheckBox, QSpinBox, QScrollArea, QFileDialog,
    QGroupBox, QSizePolicy
)
from PyQt6.QtCore import Qt

from ...core import get_config, EventBus, Events
from ...core.constants import PLATFORMS
from ..widgets.embedded_browser import BrowserDialog, is_webengine_available

logger = logging.getLogger(__name__)


class SettingsTab(QWidget):
    """
    Settings tab with categorized configuration options.
    
    Sections:
    - Authentication (Tokens)
    - Download Settings
    - Paths & Locations
    - Network
    - Appearance
    """
    
    def __init__(self):
        super().__init__()
        
        self.config = get_config()
        self.event_bus = EventBus()
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self) -> None:
        """Set up the UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Authentication section
        layout.addWidget(self._create_auth_section())
        
        # Download settings section
        layout.addWidget(self._create_download_section())
        
        # Paths section
        layout.addWidget(self._create_paths_section())
        
        # Network section
        layout.addWidget(self._create_network_section())
        
        # Appearance section
        layout.addWidget(self._create_appearance_section())
        
        # Stretch
        layout.addStretch()
        
        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_settings)
        save_layout.addWidget(reset_btn)
        
        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save_settings)
        save_layout.addWidget(save_btn)
        
        layout.addLayout(save_layout)
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
    
    def _create_section(self, title: str, icon: str = "") -> QGroupBox:
        """Create a settings section group box."""
        group = QGroupBox(f"{icon} {title}" if icon else title)
        # Use theme styling - no inline styles needed
        return group
    
    def _create_auth_section(self) -> QGroupBox:
        """Create authentication settings section."""
        group = self._create_section("Authentication", "🔑")
        layout = QFormLayout(group)
        layout.setSpacing(12)
        
        # HuggingFace token
        hf_layout = QHBoxLayout()
        self.hf_token_input = QLineEdit()
        self.hf_token_input.setPlaceholderText("Enter your HuggingFace token")
        self.hf_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        hf_layout.addWidget(self.hf_token_input)
        
        hf_env_btn = QPushButton("Use HF_TOKEN")
        hf_env_btn.setFixedWidth(100)
        hf_env_btn.clicked.connect(self._load_hf_token_from_env)
        hf_layout.addWidget(hf_env_btn)
        
        hf_validate_btn = QPushButton("✓ Validate")
        hf_validate_btn.setFixedWidth(80)
        hf_validate_btn.clicked.connect(self._validate_hf_token)
        hf_layout.addWidget(hf_validate_btn)
        
        hf_get_btn = QPushButton("Get Token")
        hf_get_btn.setFixedWidth(80)
        hf_get_btn.clicked.connect(lambda: self._open_url(PLATFORMS["huggingface"]["token_url"]))
        hf_layout.addWidget(hf_get_btn)
        
        # Token status label
        self.hf_token_status = QLabel("")
        self.hf_token_status.setStyleSheet("font-size: 11px;")
        
        layout.addRow("HuggingFace:", hf_layout)
        layout.addRow("", self.hf_token_status)
        
        # ModelScope token
        ms_layout = QHBoxLayout()
        self.ms_token_input = QLineEdit()
        self.ms_token_input.setPlaceholderText("Enter your ModelScope token")
        self.ms_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        ms_layout.addWidget(self.ms_token_input)
        
        ms_get_btn = QPushButton("Get Token")
        ms_get_btn.setFixedWidth(80)
        ms_get_btn.clicked.connect(lambda: self._open_url(PLATFORMS["modelscope"]["token_url"]))
        ms_layout.addWidget(ms_get_btn)
        
        layout.addRow("ModelScope:", ms_layout)
        
        return group
    
    def _create_download_section(self) -> QGroupBox:
        """Create download settings section."""
        group = self._create_section("Download Settings", "📥")
        layout = QFormLayout(group)
        layout.setSpacing(12)
        
        # Max workers
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 8)
        self.workers_spin.setValue(self.config.download.max_workers)
        layout.addRow("Concurrent downloads:", self.workers_spin)
        
        # Auto retry
        self.auto_retry_check = QCheckBox("Automatically retry failed downloads")
        self.auto_retry_check.setChecked(self.config.download.auto_retry)
        layout.addRow(self.auto_retry_check)
        
        # Max retries
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setRange(0, 10)
        self.max_retries_spin.setValue(self.config.download.max_retries)
        layout.addRow("Maximum retries:", self.max_retries_spin)
        
        # Verify checksums
        self.verify_check = QCheckBox("Verify file checksums after download")
        self.verify_check.setChecked(self.config.download.verify_checksums)
        layout.addRow(self.verify_check)
        
        # Open folder after
        self.open_folder_check = QCheckBox("Open folder after download completes")
        self.open_folder_check.setChecked(self.config.download.open_folder_after)
        layout.addRow(self.open_folder_check)
        
        # Bandwidth throttling
        bandwidth_layout = QHBoxLayout()
        self.bandwidth_check = QCheckBox("Limit bandwidth")
        self.bandwidth_check.stateChanged.connect(self._on_bandwidth_toggle)
        bandwidth_layout.addWidget(self.bandwidth_check)
        
        self.bandwidth_spin = QSpinBox()
        self.bandwidth_spin.setRange(1, 1000)
        self.bandwidth_spin.setValue(10)
        self.bandwidth_spin.setSuffix(" MB/s")
        self.bandwidth_spin.setFixedWidth(100)
        self.bandwidth_spin.setEnabled(False)
        bandwidth_layout.addWidget(self.bandwidth_spin)
        
        bandwidth_layout.addStretch()
        layout.addRow(bandwidth_layout)
        
        # Load current bandwidth setting
        if self.config.download.bandwidth_limit:
            self.bandwidth_check.setChecked(True)
            self.bandwidth_spin.setEnabled(True)
            # Convert bytes/sec to MB/s
            self.bandwidth_spin.setValue(self.config.download.bandwidth_limit // (1024 * 1024))
        
        return group
    
    def _create_paths_section(self) -> QGroupBox:
        """Create paths settings section."""
        group = self._create_section("Paths & Locations", "📁")
        layout = QFormLayout(group)
        layout.setSpacing(12)
        
        # Default save path
        default_layout = QHBoxLayout()
        self.default_path_input = QLineEdit()
        self.default_path_input.setText(self.config.paths.default_save_path)
        default_layout.addWidget(self.default_path_input)
        
        default_browse = QPushButton("Browse")
        default_browse.setFixedWidth(80)
        default_browse.clicked.connect(lambda: self._browse_path(self.default_path_input))
        default_layout.addWidget(default_browse)
        
        layout.addRow("Default save path:", default_layout)
        
        # ComfyUI root
        comfy_layout = QHBoxLayout()
        self.comfy_path_input = QLineEdit()
        self.comfy_path_input.setText(self.config.paths.comfy_root)
        self.comfy_path_input.setPlaceholderText("Auto-detect or set manually")
        comfy_layout.addWidget(self.comfy_path_input)
        
        comfy_browse = QPushButton("Browse")
        comfy_browse.setFixedWidth(80)
        comfy_browse.clicked.connect(lambda: self._browse_path(self.comfy_path_input))
        comfy_layout.addWidget(comfy_browse)
        
        layout.addRow("ComfyUI root:", comfy_layout)
        
        return group
    
    def _create_network_section(self) -> QGroupBox:
        """Create network settings section."""
        group = self._create_section("Network", "🌐")
        layout = QFormLayout(group)
        layout.setSpacing(12)
        
        # Use HF mirror
        self.hf_mirror_check = QCheckBox("Use HuggingFace mirror (hf-mirror.com)")
        self.hf_mirror_check.setChecked(self.config.network.use_hf_mirror)
        layout.addRow(self.hf_mirror_check)
        
        # Custom endpoint
        self.endpoint_input = QLineEdit()
        self.endpoint_input.setText(self.config.network.hf_endpoint)
        self.endpoint_input.setPlaceholderText("https://huggingface.co")
        layout.addRow("Custom HF endpoint:", self.endpoint_input)
        
        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(30, 600)
        self.timeout_spin.setValue(self.config.network.timeout)
        self.timeout_spin.setSuffix(" seconds")
        layout.addRow("Connection timeout:", self.timeout_spin)
        
        return group
    
    def _create_appearance_section(self) -> QGroupBox:
        """Create appearance settings section."""
        from ..theme import THEME_NAMES, apply_theme
        
        group = self._create_section("Appearance", "🎨")
        layout = QFormLayout(group)
        layout.setSpacing(12)
        
        # Theme selector with all 15 themes
        theme_layout = QHBoxLayout()
        self.theme_combo = QComboBox()
        for key, name in THEME_NAMES.items():
            self.theme_combo.addItem(name, key)
        
        # Set current theme
        current_theme = self.config.ui.theme
        idx = self.theme_combo.findData(current_theme)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        
        # Preview button
        preview_btn = QPushButton("Apply Now")
        preview_btn.setFixedWidth(100)
        preview_btn.clicked.connect(self._apply_theme_now)
        theme_layout.addWidget(preview_btn)
        
        layout.addRow("Theme:", theme_layout)
        
        # Remember window size
        self.remember_size_check = QCheckBox("Remember window size and position")
        self.remember_size_check.setChecked(self.config.ui.remember_window_size)
        layout.addRow(self.remember_size_check)
        
        # Show notifications
        self.notifications_check = QCheckBox("Show notifications")
        self.notifications_check.setChecked(self.config.ui.show_notifications)
        layout.addRow(self.notifications_check)
        
        return group
    
    def _on_theme_changed(self, index: int) -> None:
        """Handle theme selection change."""
        pass  # Theme applied on button click or save
    
    def _apply_theme_now(self) -> None:
        """Apply the selected theme immediately."""
        from ..theme import apply_theme
        from PyQt6.QtWidgets import QApplication
        
        theme_key = self.theme_combo.currentData()
        if theme_key:
            app = QApplication.instance()
            if app:
                apply_theme(app, theme_key)
                self.event_bus.emit(Events.NOTIFICATION, f"Applied theme: {self.theme_combo.currentText()}", "success")
    
    def _load_settings(self) -> None:
        """Load current settings into UI."""
        # Already done in _setup_ui for most fields
        pass
    
    def _save_settings(self) -> None:
        """Save settings from UI."""
        try:
            # Auth
            # Note: In production, tokens should be encrypted before storage
            
            # Download
            self.config.download.max_workers = self.workers_spin.value()
            self.config.download.auto_retry = self.auto_retry_check.isChecked()
            self.config.download.max_retries = self.max_retries_spin.value()
            self.config.download.verify_checksums = self.verify_check.isChecked()
            self.config.download.open_folder_after = self.open_folder_check.isChecked()
            
            # Bandwidth limit (convert MB/s to bytes/sec)
            if self.bandwidth_check.isChecked():
                self.config.download.bandwidth_limit = self.bandwidth_spin.value() * 1024 * 1024
            else:
                self.config.download.bandwidth_limit = None
            
            # Paths
            self.config.paths.default_save_path = self.default_path_input.text()
            self.config.paths.comfy_root = self.comfy_path_input.text()
            
            # Network
            self.config.network.use_hf_mirror = self.hf_mirror_check.isChecked()
            self.config.network.hf_endpoint = self.endpoint_input.text() or PLATFORMS["huggingface"]["default_endpoint"]
            self.config.network.timeout = self.timeout_spin.value()
            
            # Appearance
            self.config.ui.theme = self.theme_combo.currentData() or "dark"
            self.config.ui.remember_window_size = self.remember_size_check.isChecked()
            self.config.ui.show_notifications = self.notifications_check.isChecked()
            
            # Apply theme
            self._apply_theme_now()
            
            # Save
            self.config.save()
            
            self.event_bus.emit(Events.SETTINGS_CHANGED)
            self.event_bus.emit(Events.NOTIFICATION, "Settings saved", "success")
            
            logger.info("Settings saved successfully")
            
        except Exception as e:
            self.event_bus.emit(Events.NOTIFICATION, f"Failed to save settings: {e}", "error")
            logger.error(f"Failed to save settings: {e}")
    
    def _reset_settings(self) -> None:
        """Reset settings to defaults."""
        from ...core.config import reset_config
        self.config = reset_config()
        self._load_settings()
        self.event_bus.emit(Events.NOTIFICATION, "Settings reset to defaults", "info")
    
    def _browse_path(self, input_field: QLineEdit) -> None:
        """Browse for a directory."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            input_field.text() or os.path.expanduser("~")
        )
        if path:
            input_field.setText(path)
    
    def _load_hf_token_from_env(self) -> None:
        """Load HuggingFace token from environment."""
        token = os.environ.get("HF_TOKEN", "")
        if token:
            self.hf_token_input.setText(token)
            self.event_bus.emit(Events.NOTIFICATION, "Token loaded from environment", "success")
        else:
            self.event_bus.emit(Events.NOTIFICATION, "HF_TOKEN not found in environment", "warning")
    
    def _open_url(self, url: str) -> None:
        """Open URL in internal browser dialog (no external redirects)."""
        if is_webengine_available():
            # Use internal embedded browser
            dialog = BrowserDialog(url=url, title="Get Token", parent=self)
            dialog.browser.token_detected.connect(self._on_token_detected)
            dialog.show()
        else:
            # Fallback to external only if WebEngine not installed
            from PyQt6.QtGui import QDesktopServices
            from PyQt6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl(url))
            self.event_bus.emit(
                Events.NOTIFICATION,
                "Install PyQt6-WebEngine for in-app browsing",
                "info"
            )
    
    def _on_token_detected(self, token: str) -> None:
        """Handle token detected from browser."""
        self.hf_token_input.setText(token)
        self.event_bus.emit(Events.NOTIFICATION, "Token auto-filled!", "success")
    
    def _on_bandwidth_toggle(self, state: int) -> None:
        """Handle bandwidth limit checkbox toggle."""
        self.bandwidth_spin.setEnabled(state == Qt.CheckState.Checked.value)
    
    def _validate_hf_token(self) -> None:
        """Validate HuggingFace token and show scope info."""
        token = self.hf_token_input.text().strip()
        
        if not token:
            self.hf_token_status.setText("⚠️ No token entered")
            self.hf_token_status.setStyleSheet("color: #fab387; font-size: 11px;")
            return
        
        self.hf_token_status.setText("🔄 Validating...")
        self.hf_token_status.setStyleSheet("color: #89b4fa; font-size: 11px;")
        
        # Force UI update
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        
        try:
            from huggingface_hub import HfApi
            api = HfApi(token=token)
            user_info = api.whoami()
            
            # Extract useful info
            username = user_info.get("name", "Unknown")
            auth_type = user_info.get("auth", {}).get("type", "unknown")
            
            # Check for write access (needed for gated models)
            can_write = "write" in str(user_info.get("auth", {}).get("accessToken", {}).get("fineGrained", {}).get("scoped", []))
            
            # Build status message
            status_parts = [f"✅ Valid ({username})"]
            
            if auth_type == "access_token":
                status_parts.append("Token")
            
            # Check for orgs
            orgs = user_info.get("orgs", [])
            if orgs:
                org_names = [o.get("name", "?") for o in orgs[:2]]
                status_parts.append(f"Orgs: {', '.join(org_names)}")
            
            self.hf_token_status.setText(" | ".join(status_parts))
            self.hf_token_status.setStyleSheet("color: #a6e3a1; font-size: 11px;")
            
            self.event_bus.emit(Events.NOTIFICATION, f"Token valid for user: {username}", "success")
            
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Invalid" in error_msg.lower():
                self.hf_token_status.setText("❌ Invalid token")
            else:
                self.hf_token_status.setText(f"❌ Error: {error_msg[:50]}")
            
            self.hf_token_status.setStyleSheet("color: #f38ba8; font-size: 11px;")
            self.event_bus.emit(Events.NOTIFICATION, "Token validation failed", "error")
