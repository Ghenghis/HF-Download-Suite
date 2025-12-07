# HF Download Suite - Interactive TODO Tracker

> **Instructions**: Check off tasks as you complete them by changing `[ ]` to `[x]`

---

## Current Sprint: Critical Fixes & Core Features

### 🔴 Critical (Do First)

- [x] **BUG-001**: Fix `get_database` import error in `core/__init__.py`
  - Status: ✅ COMPLETED
  - Added `get_database = get_db` alias
  - Tests: 55/55 passing

- [x] **BUG-002**: Add disk space pre-check before downloads
  - File: `hf_suite_v2/core/download/worker.py`
  - Status: ✅ COMPLETED
  - Added `_check_disk_space()` and `_estimate_repo_size()` methods
  - Added 10% buffer for safety margin

- [x] **BUG-003**: Implement proper error messages with fixes
  - File: `hf_suite_v2/core/exceptions.py` (NEW)
  - Status: ✅ COMPLETED
  - Created 8 custom exception classes with actionable suggestions:
    - `InsufficientSpaceError`, `AuthenticationError`, `NetworkError`
    - `RepositoryNotFoundError`, `GatedModelError`, `DownloadInterruptedError`
    - `FileVerificationError`, `HFSuiteError` (base class)
  - Tests: 13/13 passing in `test_exceptions.py`

- [x] **FEAT-001**: Download size estimation (dry-run)
  - File: `hf_suite_v2/core/download/worker.py`
  - Status: ✅ COMPLETED (backend)
  - Added `_estimate_repo_size()` and `_estimate_hf_repo_size()` methods
  - Uses HuggingFace API to get file sizes before download
  - TODO: Add UI display in downloads_tab.py

### 🟡 High Priority (This Week)

- [x] **FEAT-002**: Bandwidth throttling controls
  - File: `hf_suite_v2/ui/tabs/settings_tab.py`
  - Status: ✅ COMPLETED
  - Added "Limit bandwidth" checkbox with MB/s spinbox
  - Saves to config.download.bandwidth_limit

- [x] **FEAT-003**: Token scope validation
  - File: `hf_suite_v2/ui/tabs/settings_tab.py`
  - Status: ✅ COMPLETED
  - Added "✓ Validate" button using HfApi().whoami()
  - Shows username, orgs, and token validity status

- [x] **FEAT-004**: Auto-retry with exponential backoff
  - File: `hf_suite_v2/core/download/worker.py`
  - Status: ✅ COMPLETED
  - Implements retry loop with exponential backoff (delay * 2^attempt)
  - Non-retryable errors (auth, space, gated) fail immediately
  - Respects cancel requests during retry wait

- [x] **FEAT-005**: API response caching
  - File: `hf_suite_v2/core/api/cache.py`
  - Status: ✅ COMPLETED
  - Created `APICache` singleton with TTL-based expiration
  - Added `@cached` decorator for easy function caching
  - Pre-defined TTLs for search, repo info, file listings

### 🟢 Medium Priority (Next Week)

- [x] **FEAT-006**: Export history to CSV/JSON
  - File: `hf_suite_v2/ui/tabs/history_tab.py`
  - Status: ✅ COMPLETED
  - Added "📤 Export" button with dropdown menu
  - Supports both CSV and JSON formats
  - JSON includes metadata (export date, count)

- [x] **FEAT-007**: Batch URL/ID import
  - File: `hf_suite_v2/ui/tabs/downloads_tab.py`
  - Status: ✅ COMPLETED
  - Added "📋 Batch" button with BatchImportDialog
  - Supports multiline input, comments (#), live count

- [x] **FEAT-008**: Keyboard shortcuts
  - File: `hf_suite_v2/ui/main_window.py`
  - Status: ✅ COMPLETED
  - Added shortcuts: Ctrl+1-7 (tabs), Ctrl+N (new), Ctrl+P (pause all)
  - Ctrl+Shift+P (resume), Ctrl+, (settings), F5 (refresh), Ctrl+Q (quit)
  - Also added pause_all/resume_all to download manager

- [x] **FEAT-009**: System tray support
  - File: `hf_suite_v2/ui/app.py`
  - Status: ✅ COMPLETED
  - Added `create_system_tray()` with context menu
  - Features: Show/Hide, Pause/Resume All, Quit
  - Added `minimize_to_tray` and `close_to_tray` to config

- [x] **FEAT-010**: ComfyUI auto-download missing
  - File: `hf_suite_v2/ui/tabs/comfyui_tab.py`
  - Status: ✅ COMPLETED
  - Fixed _download_selected() to use correct add() parameters
  - Removed unused DownloadTask import

---

## Code Quality Tasks

### Refactoring

- [x] **REFACTOR-001**: Extract PathSelector widget
  - File: `ui/widgets/path_selector.py`
  - Status: ✅ COMPLETED
  - Created PathSelector, SavePathSelector, FileSelector classes
  - Supports validation, mode selection, signals

- [x] **REFACTOR-002**: Create NotificationToast widget
  - File: `ui/widgets/notification_toast.py`
  - Status: ✅ COMPLETED
  - Created NotificationToast, NotificationManager
  - Features: fade animations, auto-dismiss, stacking, 4 severity levels

- [x] **REFACTOR-003**: Create custom exceptions
  - File: `hf_suite_v2/core/exceptions.py`
  - Status: ✅ COMPLETED
  - All exception classes created with `suggestion` property

### Testing

- [x] **TEST-001**: Add integration tests for download flow
  - File: `tests/integration/test_download_flow.py`
  - Status: ✅ COMPLETED
  - Tests: Models, paths, configuration, priorities, error handling

- [ ] **TEST-002**: Add UI tests with pytest-qt
  - File: `tests/ui/test_main_window.py`
  - Status: Deferred (requires display)

- [x] **TEST-003**: Add API tests
  - File: `tests/unit/test_api.py`
  - Status: ✅ COMPLETED
  - Tests: Base classes, caching, configuration, platform constants

### Documentation

- [x] **DOCS-001**: Update README with new architecture
  - File: `README.md`
  - Status: ✅ COMPLETED
  - Modern design with badges, screenshots, detailed docs

- [x] **DOCS-002**: Create user guide
  - File: `docs/USER_GUIDE.md`
  - Status: ✅ COMPLETED
  - Comprehensive guide with all features documented

- [x] **DOCS-003**: Add developer documentation
  - File: `docs/DEVELOPER_GUIDE.md`
  - Status: ✅ COMPLETED
  - Architecture, components, coding standards

---

## Progress Log

### December 6, 2025

| Time | Action | Result |
|------|--------|--------|
| 12:59 PM | Started comprehensive audit | Identified import error |
| 1:15 PM | Fixed `get_database` alias | Tests: 55/55 passing |
| 1:20 PM | Created MASTER_ACTION_PLAN.md | Full roadmap documented |
| 1:25 PM | Created TODO_TRACKER.md | Interactive tracking |
| 2:15 PM | Created `exceptions.py` | 8 exception classes with suggestions |
| 2:20 PM | Added disk space pre-check | `_check_disk_space()` in worker.py |
| 2:22 PM | Added size estimation | `_estimate_repo_size()` methods |
| 2:25 PM | Added exception tests | 13 new tests (68 total now) |
| 2:30 PM | Implemented auto-retry | Exponential backoff in worker.py |
| 2:35 PM | Added history export | CSV and JSON export in history_tab.py |
| 2:45 PM | Added keyboard shortcuts | 10+ shortcuts in main_window.py |
| 2:50 PM | Added batch import | BatchImportDialog in downloads_tab.py |
| 2:55 PM | Added system tray | QSystemTrayIcon with context menu |
| 3:00 PM | Added token validation | HfApi.whoami() in settings_tab.py |
| 3:05 PM | Added bandwidth throttling | UI controls in settings_tab.py |
| 3:10 PM | Created API cache | core/api/cache.py with TTL support |
| 3:15 PM | Fixed ComfyUI download | Correct manager.add() parameters |
| 3:20 PM | Created PathSelector | Reusable widget in widgets/ |
| 3:25 PM | Created NotificationToast | Toast notifications with animations |
| 3:30 PM | Added API cache tests | 13 new tests (81 total now) |
| 3:35 PM | Created USER_GUIDE.md | Comprehensive user documentation |
| 3:40 PM | Created DEVELOPER_GUIDE.md | Technical documentation |
| 3:50 PM | Added integration tests | 15 tests for download flow |
| 3:55 PM | Added API tests | 20 tests for API/caching |
| 4:00 PM | Fixed exceptions | Added is_retryable, DownloadError |
| 4:10 PM | Created README.md | Modern, interactive README |

---

## Notes & Decisions

### Architecture Decisions
1. Using `get_db` as primary function name, `get_database` as alias
2. Event bus pattern for decoupled communication
3. SQLite for local persistence (no server needed)
4. PyQt6-WebEngine optional (fallback search mode exists)

### Known Limitations
1. ModelScope requires separate token (not HF token)
2. CivitAI support planned but not implemented
3. Windows paths tested, Linux/macOS need verification

### Dependencies to Watch
- `huggingface_hub` API changes (check release notes)
- PyQt6 version compatibility with WebEngine
- SQLAlchemy 2.0 migration warnings (non-blocking)

---

## Quick Commands

```bash
# Run tests
cd g:\Github\Comfy-HF-Downloader\merged_hf_suite_project
python -m pytest hf_suite_v2/tests -v

# Run specific test file
python -m pytest hf_suite_v2/tests/unit/test_database.py -v

# Run GUI
python -m hf_suite_v2.main

# Run CLI
python -m hf_suite_v2.cli download TheBloke/Llama-2-7B-GGUF -o ./models
```

---

*Last updated: December 6, 2025*
