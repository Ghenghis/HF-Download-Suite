# HF Download Suite - User Guide

A powerful desktop application for downloading models from HuggingFace and ModelScope with seamless integration for ComfyUI, Automatic1111, and LM Studio.

## Table of Contents

- [Getting Started](#getting-started)
- [Downloads Tab](#downloads-tab)
- [Search Tab](#search-tab)
- [History Tab](#history-tab)
- [ComfyUI Integration](#comfyui-integration)
- [Settings](#settings)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/hf-download-suite.git
cd hf-download-suite

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m hf_suite_v2
```

### First Run

1. On first launch, the application will create a configuration directory
2. Go to **Settings** tab to configure:
   - Your HuggingFace token (for gated models)
   - Default save directory
   - ComfyUI/A1111 paths (optional)

---

## Downloads Tab

The main hub for managing your model downloads.

### Adding a Download

1. Enter a repository ID in the format `username/model-name`
2. Select the save path or use the default
3. Click **Add to Queue** or press `Enter`

### Batch Import

Download multiple models at once:

1. Click the **📋 Batch** button
2. Enter repository IDs, one per line
3. Lines starting with `#` are treated as comments
4. Click **Import** to add all to queue

### Download Controls

| Button | Action |
|--------|--------|
| ⏸️ Pause | Pause the current download |
| ▶️ Resume | Resume a paused download |
| ❌ Cancel | Cancel and remove from queue |
| 📁 Open Folder | Open the download location |

### File Selection

Click **📋 Select Files** before adding to choose specific files from a repository instead of downloading everything.

---

## Search Tab

Browse and discover models from HuggingFace and ModelScope.

### Search Features

- **Text Search**: Enter keywords to find models
- **Platform Filter**: Choose HuggingFace or ModelScope
- **Type Filter**: Models, Datasets, or Spaces
- **Sort Options**: Downloads, Likes, Recent

### Model Cards

Each search result shows:
- Model name and author
- Download count and likes
- Tags and description
- Quick download button

---

## History Tab

View and manage your download history.

### Filtering

- Filter by status: All, Completed, Failed, Cancelled
- Search by repository name
- Sort by date or name

### Export History

1. Click **📤 Export**
2. Choose format:
   - **CSV**: Spreadsheet-compatible format
   - **JSON**: Structured data with metadata

### Re-download

Click any completed download to add it to the queue again with the same settings.

---

## ComfyUI Integration

Parse ComfyUI workflows and automatically download missing models.

### Setup

1. Go to **Settings** and set your ComfyUI root directory
2. Or use **Detect** to automatically find it

### Parsing a Workflow

1. Click **Browse** to select a workflow JSON file
2. Click **Parse** to analyze the workflow
3. The table shows all referenced models and their status:
   - ✅ **Found**: Model exists locally
   - ❌ **Missing**: Model needs to be downloaded
   - 🔍 **Unknown**: Could not determine status

### Downloading Missing Models

1. Check the models you want to download
2. Click **Resolve Selected** to find HuggingFace repos
3. Click **Download Selected** to add to queue

Models are automatically saved to the correct ComfyUI folder based on type (checkpoints, loras, embeddings, etc.).

---

## Settings

### Authentication

- **HuggingFace Token**: Required for gated models (Llama, SDXL, etc.)
  - Click **Get Token** to open the HuggingFace settings page
  - Click **✓ Validate** to verify your token
  - Click **Use HF_TOKEN** to load from environment variable

### Download Settings

| Setting | Description |
|---------|-------------|
| Concurrent downloads | Number of simultaneous downloads (1-8) |
| Auto retry | Automatically retry failed downloads |
| Maximum retries | Number of retry attempts |
| Verify checksums | Validate files after download |
| Open folder after | Open destination after completion |
| Limit bandwidth | Restrict download speed (MB/s) |

### Paths

| Path | Purpose |
|------|---------|
| Default save path | Where models are saved by default |
| ComfyUI root | For automatic model organization |
| A1111 root | For Automatic1111 integration |
| LM Studio models | For LM Studio integration |

### Network

- **Use HF Mirror**: Use mirror for faster downloads in some regions
- **Custom endpoint**: Override the default API endpoint
- **Timeout**: Connection timeout in seconds

### Appearance

- **Theme**: Dark, Light, or System
- **Remember window size**: Restore window position on restart
- **Show notifications**: Enable desktop notifications

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+1` to `Ctrl+7` | Switch between tabs |
| `Ctrl+N` | Focus new download input |
| `Ctrl+P` | Pause all downloads |
| `Ctrl+Shift+P` | Resume all downloads |
| `Ctrl+,` | Open Settings tab |
| `F5` | Refresh current tab |
| `Ctrl+Q` | Quit application |
| `Ctrl+F` | Focus search (when available) |

---

## System Tray

When enabled, the application shows an icon in the system tray:

- **Double-click**: Show/hide main window
- **Right-click menu**:
  - Show/Hide
  - Pause All
  - Resume All
  - Quit

Enable in Settings > Appearance > "Minimize to tray"

---

## Troubleshooting

### Common Issues

#### "Token validation failed"

- Ensure your token is correct
- Check if it has the required permissions
- For gated models, accept the model's terms on HuggingFace first

#### "Insufficient disk space"

- The app checks available space before downloading
- Free up space or choose a different save location

#### "Download failed - Connection error"

- Check your internet connection
- Try enabling HF Mirror in Settings
- Increase timeout value

#### "Model not found"

- Verify the repository ID is correct
- Check if the model is private (requires token)
- Ensure the model exists on HuggingFace

### Logs

Logs are saved to:
- Windows: `%APPDATA%\HF-Suite\logs\`
- macOS: `~/Library/Application Support/HF-Suite/logs/`
- Linux: `~/.local/share/HF-Suite/logs/`

### Reset Settings

To reset to defaults:
1. Go to Settings
2. Click **Reset to Defaults**
3. Click **Save Settings**

---

## Getting Help

- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Ask questions on GitHub Discussions
- **Wiki**: Check the project wiki for advanced topics

---

*HF Download Suite v2.0*
