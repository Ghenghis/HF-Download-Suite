# HuggingFace Download Suite – Integrated Features & Roadmap

This merged project combines:

- **GUI HF / ModelScope Downloader** (`hf-model-downloader-main`)
- **ComfyUI HuggingFace Downloader nodes** (`ComfyUI_HuggingFace_Downloader-main`)
- **HF Login Helper batch script** (`hf_login_helper.bat` in `hf-model-downloader-main/scripts`)

---

## A. Implemented Integrated Features (15)

1. **Persistent settings file**
   - All UI preferences are stored in `~/.hf_model_suite/settings.json` (token, paths, options, etc.).
2. **Token persistence**
   - The Hugging Face token is saved to the settings file and restored automatically on start.
3. **“Use HF_TOKEN” button**
   - One-click load of the token from the `HF_TOKEN` environment variable into the UI.
4. **“Save” token button**
   - Explicit button to write the current token value into the persistent settings file.
5. **Configurable default save path**
   - The last used save directory is stored and re-applied automatically on the next launch.
6. **Path presets combo**
   - New **path preset dropdown** next to the save path field for quickly switching between favorite folders.
7. **“+ Add preset” path button**
   - One-click promotion of the current save path into a named preset (stored in settings).
8. **Named locations manager**
   - The **Settings dialog** lists all named locations and allows removing entries cleanly.
9. **ComfyUI root path setting**
   - A dedicated field in **Settings** to store the ComfyUI root directory for future deeper integration.
10. **“Open folder after download” option**
    - Checkbox in **Settings** that controls whether the target folder should open after a successful download.
11. **Automatic folder open after download**
    - When enabled, the app opens the final save directory (via the OS file browser) once a download finishes.
12. **Settings gear button in main UI**
    - New ⚙ button next to the Token field that opens a centralized **HF Suite Settings** dialog.
13. **Integrated HF Login Helper button**
    - A **“HF Login Helper”** button in the Quick Guide section runs `hf_login_helper.bat` (on Windows only) to configure CLI credentials.
14. **Robust, non‑blocking helper launching**
    - `hf_login_helper.bat` is started in a separate process, and any errors are caught and displayed in the log instead of crashing the GUI.
15. **Safe, non‑fatal settings handling**
    - All settings load/save operations are wrapped in try/except so a corrupt/missing config file never prevents the GUI from launching.

---

## B. Roadmap – Top 25 Missing / Future “Most Useful” Features

These are **not implemented yet**, but the code and layout are structured so they can be added in future versions.

1. **Multi‑download queue**
   - Allow users to queue multiple model/dataset IDs and download them sequentially or in parallel.
2. **Download profiles**
   - Named profiles combining token, endpoint, default path, and filters (e.g., “SDXL Models”, “GGUF Only”, “Datasets”).
3. **Per‑project presets**
   - Store separate settings per project folder (e.g. per ComfyUI install, per A1111 install, per LM Studio models dir).
4. **Model type filters**
   - Smart filters for common HF repos (checkpoints, LoRA, VAE, ControlNet, GGUF, etc.) with one‑click toggles.
5. **Dry‑run / size estimation**
   - Pre-download step that lists files and approximate total size before the actual download begins.
6. **Download resume UI**
   - Visual representation of partially downloaded repos and one‑click “resume” support.
7. **Per‑file selection**
   - Ability to see all files in a repo and selectively download only some of them (e.g., just `.gguf` or just `.safetensors`).
8. **Download history & favorites panel**
   - Side panel listing last N downloads, with quick re-download and “star”/favorite support.
9. **Bandwidth / rate limiting controls**
   - Per‑download bandwidth cap and global limit options to avoid saturating home networks.
10. **Concurrent download workers**
    - Configurable number of parallel downloads with a small dashboard showing each worker’s status.
11. **Error inspector**
    - Dedicated view that groups errors (auth, timeout, disk full, etc.) and suggests likely fixes.
12. **Disk space pre‑check**
    - Automatic free-space check against estimated download size with warnings and safeguards.
13. **Mirrors and endpoint presets**
    - Simple selector for common HF mirrors/endpoints (official + mirrors) with per-profile overrides.
14. **Token scope inspector**
    - UI helper to detect if the current token is scoped correctly (read / write / full) and warn if too weak.
15. **Security / privacy mode**
    - “Do not persist token” option and an easy “Forget token” button that wipes credentials from settings.
16. **ComfyUI targeted downloads**
    - Preset buttons for “download into ComfyUI checkpoints / loras / controlnet / clip / etc.” based on `comfy_root`.
17. **Cross‑tool sync**
    - Shared settings between this GUI and the ComfyUI custom nodes so preferred paths stay in sync.
18. **Script generator**
    - One‑click generation of a reusable Python or shell script that replicates the current download configuration.
19. **Model metadata viewer**
    - Embedded mini browser that shows HF model cards (tags, license, downloads, etc.) directly in the UI.
20. **Tag‑based smart suggestions**
    - Recommend target folders (e.g. “loras”, “vae”) based on model tags and file names.
21. **Automated backup & export**
    - Scheduled creation of JSON/YAML backups of settings, presets, and download history for easy migration.
22. **Profile import/export**
    - Export all presets/settings as a file and import them on another machine to clone the environment quickly.
23. **CLI companion**
    - Lightweight CLI interface using the same settings file so scripted workflows and the GUI stay perfectly aligned.
24. **Health diagnostics**
    - “Check environment” button to verify Python, `huggingface_hub` install, network reachability, and token validity.
25. **Plugin hook system**
    - Simple plugin API so advanced users can add custom post‑download hooks (e.g., auto‑convert, auto‑index, auto‑register model).

---

You now have a **single merged project** that:

- Keeps your Hugging Face token and favorite paths safe in one place  
- Lets you quickly change save locations with presets  
- Integrates a Windows HF login helper script  
- Is structured to grow into a full **HF + ComfyUI download control center** in future versions.

