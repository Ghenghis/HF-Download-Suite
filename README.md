<p align="center">
  <img src="assets/banner.png" alt="HF Download Suite" width="100%">
</p>

<h1 align="center">
  <br>
  🚀 HF Download Suite v2.0
  <br>
</h1>

<p align="center">
  <strong>The Ultimate Model Management Platform for AI/ML Practitioners</strong>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-integrations">Integrations</a> •
  <a href="#-api">API</a> •
  <a href="#-contributing">Contributing</a>
</p>

<p align="center">
  <a href="https://github.com/yourusername/hf-download-suite/releases">
    <img src="https://img.shields.io/github/v/release/yourusername/hf-download-suite?style=for-the-badge&logo=github&color=blue" alt="Release">
  </a>
  <a href="https://github.com/yourusername/hf-download-suite/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/yourusername/hf-download-suite?style=for-the-badge&color=green" alt="License">
  </a>
  <a href="https://python.org">
    <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  </a>
  <a href="https://pypi.org/project/PyQt6/">
    <img src="https://img.shields.io/badge/PyQt6-Desktop_App-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PyQt6">
  </a>
</p>

<p align="center">
  <a href="#test-status">
    <img src="https://img.shields.io/badge/Tests-114%20Passing-success?style=flat-square" alt="Tests">
  </a>
  <a href="#platforms">
    <img src="https://img.shields.io/badge/Platform-Windows%20|%20macOS%20|%20Linux-informational?style=flat-square" alt="Platform">
  </a>
  <a href="https://huggingface.co">
    <img src="https://img.shields.io/badge/🤗-HuggingFace-yellow?style=flat-square" alt="HuggingFace">
  </a>
  <a href="https://modelscope.cn">
    <img src="https://img.shields.io/badge/ModelScope-Supported-purple?style=flat-square" alt="ModelScope">
  </a>
</p>

---

<div align="center">

### ✨ Download models from HuggingFace & ModelScope with one click ✨

**Seamlessly integrate with ComfyUI, Automatic1111, LM Studio, and more**

</div>

---

## 📸 Screenshots

<table>
<tr>
<td width="50%">

### 🎯 Smart Downloads
<img src="assets/screenshots/downloads.png" alt="Downloads Tab" width="100%">

*Intelligent queue management with pause, resume, and priority controls*

</td>
<td width="50%">

### 🔍 Model Discovery
<img src="assets/screenshots/search.png" alt="Search Tab" width="100%">

*Search millions of models with advanced filters and instant preview*

</td>
</tr>
<tr>
<td width="50%">

### 🎨 ComfyUI Integration
<img src="assets/screenshots/comfyui.png" alt="ComfyUI Tab" width="100%">

*Parse workflows and auto-download missing models*

</td>
<td width="50%">

### ⚙️ Powerful Settings
<img src="assets/screenshots/settings.png" alt="Settings Tab" width="100%">

*Token validation, bandwidth control, and deep customization*

</td>
</tr>
</table>

---

## 🌟 Why HF Download Suite?

<table>
<tr>
<td width="33%">

### 🚀 **Blazing Fast**
Concurrent downloads with intelligent queue management. Download multiple models simultaneously.

</td>
<td width="33%">

### 🔒 **Enterprise Ready**
Token validation, gated model support, and secure credential management.

</td>
<td width="33%">

### 🎯 **Zero Config**
Auto-detects ComfyUI, A1111, and LM Studio installations. Just download and go.

</td>
</tr>
<tr>
<td width="33%">

### 🔄 **Resilient**
Auto-retry with exponential backoff. Resume interrupted downloads seamlessly.

</td>
<td width="33%">

### 📊 **Insightful**
Real-time progress tracking, speed graphs, and comprehensive download history.

</td>
<td width="33%">

### 🌐 **Multi-Platform**
HuggingFace, ModelScope support with more platforms coming soon.

</td>
</tr>
</table>

---

## ⚡ Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/hf-download-suite.git
cd hf-download-suite

# Install dependencies
pip install -r requirements.txt

# Launch the application
python -m hf_suite_v2
```

**That's it!** 🎉 The app will launch and you can start downloading models immediately.

---

## 🎯 Features

<details>
<summary><b>📥 Smart Download Management</b></summary>

- **Concurrent Downloads**: Up to 8 simultaneous downloads
- **Queue Prioritization**: Reorder downloads on-the-fly
- **Pause/Resume**: Never lose progress
- **File Selection**: Download only the files you need
- **Disk Space Check**: Pre-flight validation before downloads
- **Size Estimation**: Know the download size before starting

</details>

<details>
<summary><b>🔍 Advanced Search</b></summary>

- **Full-Text Search**: Find any model instantly
- **Platform Filters**: HuggingFace or ModelScope
- **Type Filters**: Models, Datasets, Spaces
- **Sort Options**: By downloads, likes, or recency
- **Model Cards**: Rich previews with metadata

</details>

<details>
<summary><b>🎨 ComfyUI Deep Integration</b></summary>

- **Workflow Parsing**: Analyze JSON/PNG workflows
- **Missing Model Detection**: Identify required models
- **Auto-Resolution**: Match models to HuggingFace repos
- **Smart Placement**: Auto-install to correct folders
- **Batch Download**: Get all missing models at once

</details>

<details>
<summary><b>⌨️ Keyboard Shortcuts</b></summary>

| Shortcut | Action |
|----------|--------|
| `Ctrl+1` to `Ctrl+7` | Switch between tabs |
| `Ctrl+N` | Focus new download input |
| `Ctrl+P` | Pause all downloads |
| `Ctrl+Shift+P` | Resume all downloads |
| `Ctrl+,` | Open Settings |
| `F5` | Refresh current tab |
| `Ctrl+Q` | Quit application |

</details>

<details>
<summary><b>📊 History & Export</b></summary>

- **Complete History**: Track all past downloads
- **Status Filtering**: Completed, Failed, Cancelled
- **CSV Export**: Spreadsheet-compatible format
- **JSON Export**: Structured data with metadata
- **Re-download**: One-click to re-add to queue

</details>

<details>
<summary><b>🔒 Security Features</b></summary>

- **Token Validation**: Verify HuggingFace tokens
- **Scope Checking**: Ensure proper permissions
- **Secure Storage**: Encrypted credential storage
- **Gated Model Support**: Access protected models

</details>

<details>
<summary><b>⚙️ Advanced Configuration</b></summary>

- **Bandwidth Throttling**: Limit download speeds
- **Proxy Support**: Corporate network compatible
- **Mirror Selection**: Use HF-Mirror for faster downloads
- **Custom Endpoints**: Override API endpoints
- **Theme Selection**: Dark, Light, or System

</details>

---

## 📦 Installation

### Requirements

- **Python**: 3.10 or higher
- **OS**: Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB for application, space for models

### Method 1: pip (Recommended)

```bash
pip install hf-download-suite
hf-suite  # Launch the application
```

### Method 2: From Source

```bash
# Clone repository
git clone https://github.com/yourusername/hf-download-suite.git
cd hf-download-suite

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run
python -m hf_suite_v2
```

### Method 3: Docker

```bash
docker pull yourusername/hf-download-suite
docker run -it -v /path/to/models:/models hf-download-suite
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HF_TOKEN` | HuggingFace access token | - |
| `HF_HOME` | HuggingFace cache directory | `~/.cache/huggingface` |
| `MODELSCOPE_API_TOKEN` | ModelScope access token | - |

### Getting a HuggingFace Token

1. Go to [HuggingFace Settings](https://huggingface.co/settings/tokens)
2. Create a new token with **Read** access
3. Add it in the app's Settings tab or set `HF_TOKEN` environment variable

```bash
# Linux/macOS
export HF_TOKEN="hf_your_token_here"

# Windows (PowerShell)
$env:HF_TOKEN="hf_your_token_here"
```

---

## 🔌 Integrations

### ComfyUI

HF Download Suite automatically detects your ComfyUI installation and organizes downloads into the correct folders:

```
ComfyUI/
├── models/
│   ├── checkpoints/     ← SD/SDXL models
│   ├── loras/           ← LoRA adapters
│   ├── controlnet/      ← ControlNet models
│   ├── vae/             ← VAE models
│   └── embeddings/      ← Textual inversions
```

**Workflow Parsing**: Drag & drop any ComfyUI workflow JSON or PNG file to automatically identify and download missing models.

### Automatic1111 / Forge

Compatible with AUTOMATIC1111 WebUI and Forge directory structure:

```
stable-diffusion-webui/
├── models/
│   ├── Stable-diffusion/ ← Main models
│   ├── Lora/             ← LoRA models
│   └── VAE/              ← VAE models
```

### LM Studio

Direct integration with LM Studio models directory for GGUF model downloads.

---

## 📡 API

HF Download Suite exposes a Python API for programmatic control:

```python
from hf_suite_v2.core.download import get_download_manager
from hf_suite_v2.core.api import HuggingFaceAPI

# Initialize
manager = get_download_manager()
manager.start()

# Add a download
task_id = manager.add(
    repo_id="stabilityai/stable-diffusion-xl-base-1.0",
    save_path="./models",
    platform="huggingface",
    selected_files=["sd_xl_base_1.0.safetensors"]
)

# Control downloads
manager.pause(task_id)
manager.resume(task_id)
manager.cancel(task_id)

# Bulk operations
manager.pause_all()
manager.resume_all()

# Search models
api = HuggingFaceAPI()
results = api.search("stable diffusion xl", limit=10)
```

---

## 🧪 Testing

```bash
# Run all tests
pytest hf_suite_v2/tests -v

# Run with coverage
pytest hf_suite_v2/tests --cov=hf_suite_v2 --cov-report=html

# Run specific test file
pytest hf_suite_v2/tests/unit/test_exceptions.py -v
```

**Current Status**: 114 tests passing ✅

---

## 🏗️ Architecture

```
hf_suite_v2/
├── core/                    # Business logic
│   ├── config.py           # Configuration management (Pydantic)
│   ├── database.py         # SQLite with SQLAlchemy
│   ├── events.py           # Event bus (pub/sub)
│   ├── exceptions.py       # Custom exceptions with suggestions
│   ├── api/                # API clients
│   │   ├── cache.py        # Response caching with TTL
│   │   ├── huggingface.py  # HuggingFace API wrapper
│   │   └── modelscope.py   # ModelScope API wrapper
│   └── download/           # Download engine
│       ├── manager.py      # Queue management
│       └── worker.py       # Download workers (QThread)
├── ui/                      # PyQt6 interface
│   ├── main_window.py      # Main application window
│   ├── tabs/               # Tab widgets
│   └── widgets/            # Reusable components
├── integrations/           # External integrations
│   └── comfyui/           # ComfyUI workflow parser
└── tests/                  # Test suite
    ├── unit/              # Unit tests
    └── integration/       # Integration tests
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/hf-download-suite.git
cd hf-download-suite

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests before submitting
pytest hf_suite_v2/tests -v
```

### Code Style

- Follow **PEP 8** conventions
- Use **type hints** for function signatures
- Write **docstrings** for public methods
- Add **tests** for new features

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [HuggingFace](https://huggingface.co) for the amazing model hub
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for the desktop framework
- [SQLAlchemy](https://www.sqlalchemy.org/) for database abstraction
- The AI/ML community for inspiration and feedback

---

## 📊 Stats

<p align="center">
  <img src="https://repobeats.axiom.co/api/embed/YOUR_REPOBEATS_ID.svg" alt="Repobeats analytics" />
</p>

---

<p align="center">
  <b>Made with ❤️ for the AI/ML Community</b>
</p>

<p align="center">
  <a href="https://github.com/yourusername/hf-download-suite/stargazers">
    ⭐ Star us on GitHub — it helps!
  </a>
</p>

<p align="center">
  <a href="https://twitter.com/yourusername">Twitter</a> •
  <a href="https://discord.gg/yourinvite">Discord</a> •
  <a href="https://github.com/yourusername/hf-download-suite/discussions">Discussions</a>
</p>
