# Merged Hugging Face Download Suite

This archive combines:

- `hf-model-downloader-main` – PyQt6 GUI to download models/datasets from **Hugging Face** and **ModelScope**.
- `ComfyUI_HuggingFace_Downloader-main` – custom nodes for **ComfyUI** that download from Hugging Face.
- `hf-model-downloader-main/scripts/hf_login_helper.bat` – helper to log into Hugging Face from Windows cmd.

## Quick Start (GUI Downloader)

1. Install Python 3.10+ and dependencies:

   ```bash
   cd hf-model-downloader-main
   pip install -r requirements.txt
   ```

2. Run the GUI:

   ```bash
   python main.py
   ```

3. In the app you can now:
   - Choose **paths** and manage **path presets**.
   - Enter and **save your Hugging Face token**.
   - Open the HF **token page** and start the Windows **hf_login_helper.bat** script (from the UI) if desired.
   - Configure additional options from the ⚙ **Settings** dialog.

See `HF_SUITE_FEATURES.md` for a full breakdown of implemented features and the roadmap.
