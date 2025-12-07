import os
import platform

from PyQt6.QtCore import QSize, Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .resource_utils import get_asset_path
from .unified_downloader import UnifiedDownloadWorker
from .settings_manager import load_settings, save_settings

GITHUB_REPO_URL = "https://github.com/samzong/hf-model-downloader"
AUTHOR_NAME = "samzong"
AUTHOR_GITHUB_URL = "https://github.com/samzong"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HF Model Downloader")

        # Set window icon based on platform
        system = platform.system().lower()
        if system == "darwin":
            icon_path = get_asset_path("icon.icns")
        elif system == "windows":
            icon_path = get_asset_path("icon.ico")
        else:
            icon_path = get_asset_path("icon.png")

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        main_widget = QWidget()
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        standard_button_height = 32

        icon_layout = QHBoxLayout()
        icon_layout.setContentsMargins(10, 10, 10, 0)

        self.platform_button_group = QButtonGroup()
        self.platform_button_group.setExclusive(True)

        self.hf_button = QPushButton()
        hf_icon_path = get_asset_path("huggingface_logo.png")
        if os.path.exists(hf_icon_path):
            self.hf_button.setIcon(QIcon(hf_icon_path))
            self.hf_button.setIconSize(QSize(32, 32))
        self.hf_button.setCheckable(True)
        self.hf_button.setChecked(True)
        self.hf_button.setStyleSheet("""
            QPushButton {
                border: 2px solid #ddd;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
            }
            QPushButton:hover {
                border-color: #FFD21E;
                background-color: #fffbf0;
            }
            QPushButton:checked {
                border-color: #FFD21E;
                background-color: #fff8e1;
            }
        """)
        self.platform_button_group.addButton(self.hf_button, 0)

        self.ms_button = QPushButton()
        ms_icon_path = get_asset_path("modelscope_logo.png")
        if os.path.exists(ms_icon_path):
            self.ms_button.setIcon(QIcon(ms_icon_path))
            self.ms_button.setIconSize(QSize(32, 32))
        self.ms_button.setCheckable(True)
        self.ms_button.setStyleSheet("""
            QPushButton {
                border: 2px solid #ddd;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
            }
            QPushButton:hover {
                border-color: #1677FF;
                background-color: #f0f8ff;
            }
            QPushButton:checked {
                border-color: #1677FF;
                background-color: #e6f3ff;
            }
        """)
        self.platform_button_group.addButton(self.ms_button, 1)

        self.platform_button_group.idClicked.connect(self.on_platform_icon_changed)

        icon_layout.addWidget(self.hf_button)
        icon_layout.addWidget(self.ms_button)
        icon_layout.addStretch()

        layout.addLayout(icon_layout)

        help_frame = QFrame()
        help_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        help_layout = QVBoxLayout(help_frame)

        help_title = QLabel("📖 Quick Guide")
        help_title.setStyleSheet("font-weight: bold; font-size: 12px;")
        help_layout.addWidget(help_title)

        guide_content_layout = QHBoxLayout()

        help_text = QLabel(
            "1. Select platform\n"
            "2. Enter model ID (e.g., 'bert-base-uncased')\n"
            "3. Choose save location\n"
            "4. Click Download (add token for private repos)\n"
        )
        help_text.setWordWrap(True)
        help_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        guide_content_layout.addWidget(help_text)

        links_layout = QVBoxLayout()
        links_layout.addStretch()
        self.browse_models_btn = QPushButton("🔍 Browse Models")
        self.browse_models_btn.setMaximumWidth(150)
        self.browse_models_btn.setFixedHeight(standard_button_height)
        self.browse_models_btn.clicked.connect(self.open_models_page)
        self.browse_datasets_btn = QPushButton("📊 Browse Datasets")
        self.browse_datasets_btn.setMaximumWidth(150)
        self.browse_datasets_btn.setFixedHeight(standard_button_height)
        self.browse_datasets_btn.clicked.connect(self.open_datasets_page)
        self.get_token_btn = QPushButton("🔑 Get Token")
        self.get_token_btn.setMaximumWidth(150)
        self.get_token_btn.setFixedHeight(standard_button_height)
        self.get_token_btn.clicked.connect(self.open_token_page)

        # Optional Windows-only helper to run hf_login_helper.bat
        self.login_helper_btn = QPushButton("HF Login Helper")
        self.login_helper_btn.setMaximumWidth(150)
        self.login_helper_btn.setFixedHeight(standard_button_height)
        self.login_helper_btn.clicked.connect(self.run_login_helper)

        links_layout.addWidget(self.browse_models_btn)
        links_layout.addWidget(self.browse_datasets_btn)
        links_layout.addWidget(self.get_token_btn)
        links_layout.addWidget(self.login_helper_btn)
        links_layout.addStretch()

        guide_content_layout.addLayout(links_layout)
        help_layout.addLayout(guide_content_layout)

        layout.addWidget(help_frame)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["Hugging Face", "ModelScope"])
        self.platform_combo.setCurrentText("Hugging Face")
        self.platform_combo.currentTextChanged.connect(self.on_platform_changed)
        self.platform_combo.hide()

        type_layout = QHBoxLayout()
        type_label = QLabel("Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Model", "Dataset"])
        self.type_combo.setCurrentText("Model")
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        repo_layout = QHBoxLayout()
        self.repo_label = QLabel("Model ID:")
        self.repo_input = QLineEdit()
        self.repo_input.setPlaceholderText("e.g., qwen/Qwen2.5-Coder-1.5B-Instruct")
        repo_layout.addWidget(self.repo_label)
        repo_layout.addWidget(self.repo_input)
        layout.addLayout(repo_layout)

        path_layout = QHBoxLayout()
        path_label = QLabel("Save Path:")
        self.path_input = QLineEdit()

        # Preset locations combo (from settings)
        self.path_preset_combo = QComboBox()
        self.path_preset_combo.setMinimumWidth(140)
        self.path_preset_combo.currentIndexChanged.connect(self.on_path_preset_changed)

        # Button to add current path as a preset
        self.add_preset_button = QPushButton("+")
        self.add_preset_button.setFixedWidth(28)
        self.add_preset_button.setToolTip("Add current path as a preset")
        self.add_preset_button.clicked.connect(self.add_current_path_as_preset)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_path)

        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.path_preset_combo)
        path_layout.addWidget(self.add_preset_button)
        path_layout.addWidget(browse_button)
        layout.addLayout(path_layout)

        token_layout = QHBoxLayout()
        token_label = QLabel("Token:")
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText(
            "Optional: For private models or higher rate limits"
        )

        # Load token from HF_TOKEN env
        self.load_env_token_button = QPushButton("Use HF_TOKEN")
        self.load_env_token_button.setToolTip("Load token from HF_TOKEN environment variable")
        self.load_env_token_button.clicked.connect(self.load_token_from_env)

        # Save token into settings
        self.save_token_button = QPushButton("Save")
        self.save_token_button.setToolTip("Save token into local settings file")
        self.save_token_button.clicked.connect(self.save_token_clicked)

        # Settings dialog (gear)
        self.settings_button = QPushButton("\u2699")
        self.settings_button.setFixedWidth(28)
        self.settings_button.setToolTip("Open advanced settings")
        self.settings_button.clicked.connect(self.open_settings_dialog)

        token_layout.addWidget(token_label)
        token_layout.addWidget(self.token_input)
        token_layout.addWidget(self.load_env_token_button)
        token_layout.addWidget(self.save_token_button)
        token_layout.addWidget(self.settings_button)
        layout.addLayout(token_layout)

        endpoint_layout = QHBoxLayout()
        endpoint_label = QLabel("Endpoint:")
        self.endpoint_input = QLineEdit()
        self.endpoint_input.setText("https://hf-mirror.com")
        self.endpoint_input.setPlaceholderText("default: https://hf-mirror.com")
        endpoint_layout.addWidget(endpoint_label)
        endpoint_layout.addWidget(self.endpoint_input)
        layout.addLayout(endpoint_layout)

        button_layout = QHBoxLayout()
        self.download_button = QPushButton("Download")
        self.download_button.setFixedHeight(standard_button_height)
        self.download_button.clicked.connect(self.start_download)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setFixedHeight(standard_button_height)
        self.stop_button.clicked.connect(self.stop_download)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(100)
        layout.addWidget(self.log_text)

        footer_frame = QFrame()
        footer_layout = QHBoxLayout(footer_frame)

        footer_layout.addStretch()

        github_btn = QPushButton("View on GitHub")
        github_btn.setFlat(True)
        github_btn.setStyleSheet(
            "QPushButton { "
            "font-size: 12px; color: #666; border: none; text-decoration: underline; "
            "}"
        )
        github_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(GITHUB_REPO_URL))
        )
        footer_layout.addWidget(github_btn)

        author_btn = QPushButton(f"Created by {AUTHOR_NAME}")
        author_btn.setFlat(True)
        author_btn.setStyleSheet(
            "QPushButton { "
            "font-size: 12px; color: #666; border: none; text-decoration: underline; "
            "}"
        )
        author_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(AUTHOR_GITHUB_URL))
        )
        footer_layout.addWidget(author_btn)

        footer_layout.addStretch()

        layout.addWidget(footer_frame)

        # Load persisted settings (token, paths, options)
        self._init_settings()

        self._set_dynamic_minimum_height()

        self.download_worker = None
        self.last_save_path = ""

    def _set_dynamic_minimum_height(self):
        platform_icons_height = 40
        help_section_height = 200
        form_fields_height = 200
        buttons_height = 40
        log_minimum_height = 100
        footer_height = 40
        margins_spacing = 40

        total_height = (
            platform_icons_height
            + help_section_height
            + form_fields_height
            + buttons_height
            + log_minimum_height
            + footer_height
            + margins_spacing
        )

        self.setMinimumHeight(total_height)
        self.setMinimumWidth(800)

    def closeEvent(self, event):
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.finished.disconnect()
            self.download_worker.error.disconnect()
            self.download_worker.status.disconnect()
            self.download_worker.log.disconnect()

            self.download_worker.cancel_download()
            if not self.download_worker.wait(5000):
                self.download_worker.terminate()
                self.download_worker.wait()
        event.accept()

    def on_platform_icon_changed(self, button_id):
        if button_id == 0:
            platform_text = "Hugging Face"
        else:
            platform_text = "ModelScope"

        self.platform_combo.setCurrentText(platform_text)

    def on_platform_changed(self, platform_text):
        if platform_text == "ModelScope":
            self.endpoint_input.setText("https://modelscope.cn")
        else:
            self.endpoint_input.setText("https://hf-mirror.com")

    def open_models_page(self):
        """Open the models page for the current platform"""
        platform = self.platform_combo.currentText()
        if platform == "ModelScope":
            QDesktopServices.openUrl(QUrl("https://modelscope.cn/models"))
        else:
            QDesktopServices.openUrl(QUrl("https://huggingface.co/models"))

    def open_datasets_page(self):
        platform = self.platform_combo.currentText()
        if platform == "ModelScope":
            QDesktopServices.openUrl(QUrl("https://modelscope.cn/datasets"))
        else:
            QDesktopServices.openUrl(QUrl("https://huggingface.co/datasets"))

    def open_token_page(self):
        platform = self.platform_combo.currentText()
        if platform == "ModelScope":
            QDesktopServices.openUrl(QUrl("https://modelscope.cn/my/myaccesstoken"))
        else:
            QDesktopServices.openUrl(QUrl("https://huggingface.co/settings/tokens"))

    def on_type_changed(self, type_text):
        # platform = self.platform_combo.currentText()
        if type_text == "Dataset":
            self.repo_label.setText("Dataset ID:")
            self.repo_input.setPlaceholderText("e.g., baicai003/Llama3-Chinese-dataset")
        else:
            self.repo_label.setText("Model ID:")
            self.repo_input.setPlaceholderText("e.g., deepseek-ai/DeepSeek-R1")

    def browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if path:
            self.path_input.setText(path)

    def start_download(self):
        repo_id = self.repo_input.text().strip()
        save_path = self.path_input.text().strip()
        self.last_save_path = save_path
        token = self.token_input.text().strip() or None
        repo_type = self.type_combo.currentText().lower()
        platform = self.platform_combo.currentText()

        endpoint = self.endpoint_input.text().strip()
        if not endpoint:
            if platform == "ModelScope":
                endpoint = "https://modelscope.cn"
            else:
                endpoint = "https://hf-mirror.com"

        if not repo_id:
            repo_type_text = "model ID" if repo_type == "model" else "dataset ID"
            self.update_status(f"Error: Please enter a {repo_type_text}", error=True)
            return

        if not save_path:
            self.update_status("Error: Please select a save path", error=True)
            return

        self.download_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.stop_button.setStyleSheet(
            "QPushButton { background-color: #ff4444; color: white; }"
        )
        self.update_status("Initializing download...")
        self.log_text.clear()

        if platform == "ModelScope":
            self.download_worker = UnifiedDownloadWorker(
                "modelscope", repo_id, save_path, token, endpoint, repo_type
            )
        else:
            self.download_worker = UnifiedDownloadWorker(
                "huggingface", repo_id, save_path, token, endpoint, repo_type
            )

        self.download_worker.finished.connect(
            self.download_finished, Qt.ConnectionType.QueuedConnection
        )
        self.download_worker.error.connect(
            self.download_error, Qt.ConnectionType.QueuedConnection
        )
        self.download_worker.status.connect(
            self.update_status, Qt.ConnectionType.QueuedConnection
        )
        self.download_worker.log.connect(
            self.update_log, Qt.ConnectionType.QueuedConnection
        )

        self.download_worker.finished.connect(
            self._on_worker_finished, Qt.ConnectionType.QueuedConnection
        )
        self.download_worker.start()

    def stop_download(self):
        if self.download_worker and self.download_worker.isRunning():
            self.stop_button.setEnabled(False)
            self.stop_button.setStyleSheet("")
            self.update_status("Stopping download...")
            self.download_worker.cancel_download()
            self.download_button.setEnabled(True)

    def update_status(self, message, error=False):
        if error:
            self.log_text.append(f"❌ {message}")
        else:
            self.log_text.append(f"ℹ️ {message}")
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def update_log(self, message):
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def download_finished(self):
        self.download_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("")
        self.update_status("✅ Download completed successfully!")
        self.log_text.append("✅ Download completed successfully!")

    def download_error(self, error_msg):
        self.download_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("")
        if "cancelled by user" in error_msg.lower():
            self.update_status("⏹️ Download stopped by user")
            self.log_text.append("⏹️ Download stopped by user")
        else:
            self.update_status(f"❌ Error: {error_msg}", error=True)
            self.log_text.append(f"❌ Error: {error_msg}")


    # === Settings & presets helpers ===

    def _init_settings(self):
        """Load settings from disk and apply them to the UI."""
        self.settings = load_settings()

        # Token
        token = self.settings.get("token") or ""
        if token:
            self.token_input.setText(token)

        # Save path
        default_path = self.settings.get("default_save_path") or ""
        if default_path:
            self.path_input.setText(default_path)

        # Platform / type
        last_platform = self.settings.get("last_platform") or "Hugging Face"
        for i in range(self.platform_combo.count()):
            if self.platform_combo.itemText(i) == last_platform:
                self.platform_combo.setCurrentIndex(i)
                break

        last_repo_type = self.settings.get("last_repo_type") or "Model"
        for i in range(self.type_combo.count()):
            if self.type_combo.itemText(i) == last_repo_type:
                self.type_combo.setCurrentIndex(i)
                break

        # Named locations
        self._refresh_path_presets()

    def _refresh_path_presets(self):
        self.path_preset_combo.blockSignals(True)
        self.path_preset_combo.clear()
        self.path_preset_combo.addItem("Presets...")
        for loc in self.settings.get("named_locations", []):
            label = f"{loc.get('name','')}"
            self.path_preset_combo.addItem(label, loc.get("path", ""))
        self.path_preset_combo.blockSignals(False)

    def on_path_preset_changed(self, index: int):
        if index <= 0:
            return
        path = self.path_preset_combo.itemData(index)
        if path:
            self.path_input.setText(path)

    def add_current_path_as_preset(self):
        path = self.path_input.text().strip()
        if not path:
            return
        name = os.path.basename(path) or path
        locations = list(self.settings.get("named_locations", []))
        if any(loc.get("path") == path for loc in locations):
            return
        locations.append({"name": name, "path": path})
        self.settings["named_locations"] = locations
        self.settings["default_save_path"] = path
        save_settings(self.settings)
        self._refresh_path_presets()

    def load_token_from_env(self):
        token = os.environ.get("HF_TOKEN", "").strip()
        if token:
            self.token_input.setText(token)

    def save_token_clicked(self):
        token = self.token_input.text().strip()
        self.settings["token"] = token
        save_settings(self.settings)

    def open_settings_dialog(self):
        from PyQt6.QtWidgets import QDialog, QFormLayout, QCheckBox, QListWidget, QDialogButtonBox

        dlg = QDialog(self)
        dlg.setWindowTitle("HF Suite Settings")
        layout = QVBoxLayout(dlg)

        form = QFormLayout()
        comfy_edit = QLineEdit(self.settings.get("comfy_root", ""))
        form.addRow("ComfyUI root:", comfy_edit)

        default_path_edit = QLineEdit(self.settings.get("default_save_path", ""))
        form.addRow("Default save path:", default_path_edit)

        open_after_cb = QCheckBox("Open folder after successful download")
        open_after_cb.setChecked(bool(self.settings.get("open_folder_after_download", True)))
        form.addRow(open_after_cb)

        layout.addLayout(form)

        layout.addWidget(QLabel("Named locations:"))
        list_widget = QListWidget()
        locations = list(self.settings.get("named_locations", []))
        for loc in locations:
            list_widget.addItem(f"{loc.get('name','')} -> {loc.get('path','')}")
        layout.addWidget(list_widget)

        btn_row = QHBoxLayout()
        btn_remove = QPushButton("Remove selected")
        btn_row.addWidget(btn_remove)
        layout.addLayout(btn_row)

        def remove_selected():
            row = list_widget.currentRow()
            if row < 0:
                return
            del locations[row]
            list_widget.takeItem(row)

        btn_remove.clicked.connect(remove_selected)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttons)

        def on_accept():
            self.settings["comfy_root"] = comfy_edit.text().strip()
            self.settings["default_save_path"] = default_path_edit.text().strip()
            self.settings["open_folder_after_download"] = open_after_cb.isChecked()
            self.settings["named_locations"] = locations
            save_settings(self.settings)
            if self.settings["default_save_path"]:
                self.path_input.setText(self.settings["default_save_path"])
            self._refresh_path_presets()
            dlg.accept()

        buttons.accepted.connect(on_accept)
        buttons.rejected.connect(dlg.reject)

        dlg.exec()


    def run_login_helper(self):
        """Run the bundled hf_login_helper.bat on Windows to configure HF credentials."""
        import subprocess
        if platform.system().lower() != "windows":
            self.update_status("HF Login Helper is only available on Windows.", error=True)
            return
        # Batch script is located in scripts folder next to this file's parent directory
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "hf_login_helper.bat")
        if not os.path.exists(script_path):
            self.update_status("hf_login_helper.bat not found in scripts folder.", error=True)
            return
        try:
            subprocess.Popen(["cmd.exe", "/c", script_path])
            self.update_status("Started hf_login_helper.bat in a separate window.")
        except Exception as exc:
            self.update_status(f"Failed to start hf_login_helper.bat: {exc}", error=True)

    def _on_worker_finished(self):
        if hasattr(self, "download_worker") and self.download_worker:
            # Wait for thread to fully stop before cleanup
            if self.download_worker.isRunning():
                self.download_worker.wait(5000)  # Wait up to 3 seconds

            # Clear the worker reference
            self.download_worker = None

        # Optionally open the save folder after successful download
        try:
            if getattr(self, "settings", None) and self.settings.get("open_folder_after_download", True):
                if getattr(self, "last_save_path", "") and os.path.isdir(self.last_save_path):
                    QDesktopServices.openUrl(QUrl.fromLocalFile(self.last_save_path))
        except Exception:
            # Never crash the app because of this helper
            pass

