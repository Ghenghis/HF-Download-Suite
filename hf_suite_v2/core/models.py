"""
Data models using Pydantic for validation and serialization.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class DownloadStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Platform(str, Enum):
    HUGGINGFACE = "huggingface"
    MODELSCOPE = "modelscope"
    CIVITAI = "civitai"


class RepoType(str, Enum):
    MODEL = "model"
    DATASET = "dataset"
    SPACE = "space"


class DownloadTask(BaseModel):
    """Represents a download task in the queue."""
    
    id: Optional[int] = None
    repo_id: str
    platform: Platform = Platform.HUGGINGFACE
    repo_type: RepoType = RepoType.MODEL
    status: DownloadStatus = DownloadStatus.PENDING
    save_path: str
    selected_files: Optional[List[str]] = None  # None = all files
    total_bytes: int = 0
    downloaded_bytes: int = 0
    speed_bps: float = 0.0
    eta_seconds: Optional[int] = None
    priority: int = Field(default=5, ge=1, le=10)
    retry_count: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    profile_id: Optional[int] = None
    
    @property
    def progress_percent(self) -> float:
        if self.total_bytes == 0:
            return 0.0
        return (self.downloaded_bytes / self.total_bytes) * 100
    
    @property
    def repo_name(self) -> str:
        return self.repo_id.split("/")[-1] if "/" in self.repo_id else self.repo_id
    
    @property
    def is_active(self) -> bool:
        return self.status in [DownloadStatus.DOWNLOADING, DownloadStatus.QUEUED]
    
    model_config = ConfigDict(use_enum_values=True)


class DownloadFile(BaseModel):
    """Individual file within a download task."""
    
    id: Optional[int] = None
    download_id: int
    file_path: str
    file_size: int = 0
    downloaded_bytes: int = 0
    status: DownloadStatus = DownloadStatus.PENDING
    checksum: Optional[str] = None
    verified: bool = False
    
    @property
    def progress_percent(self) -> float:
        if self.file_size == 0:
            return 0.0
        return (self.downloaded_bytes / self.file_size) * 100


class HistoryEntry(BaseModel):
    """Completed download history entry."""
    
    id: Optional[int] = None
    repo_id: str
    platform: Platform = Platform.HUGGINGFACE
    repo_type: RepoType = RepoType.MODEL
    save_path: str
    total_bytes: int = 0
    duration_seconds: int = 0
    completed_at: datetime = Field(default_factory=datetime.now)
    is_favorite: bool = False
    tags: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(use_enum_values=True)


class Profile(BaseModel):
    """Download profile with preset configurations."""
    
    id: Optional[int] = None
    name: str
    platform: Optional[Platform] = None
    endpoint: Optional[str] = None
    default_path: Optional[str] = None
    token_id: Optional[int] = None
    file_filters: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(use_enum_values=True)


class Token(BaseModel):
    """Stored authentication token (encrypted)."""
    
    id: Optional[int] = None
    name: str
    platform: Platform
    encrypted_value: str  # Encrypted token value
    scope: Optional[str] = None  # 'read', 'write', 'full'
    last_validated: Optional[datetime] = None
    is_valid: bool = True
    
    model_config = ConfigDict(use_enum_values=True)


class NamedLocation(BaseModel):
    """Saved path preset."""
    
    id: Optional[int] = None
    name: str
    path: str
    tool_type: Optional[str] = None  # 'comfyui', 'a1111', 'lmstudio', 'custom'
    model_type: Optional[str] = None  # 'checkpoints', 'loras', 'vae', etc.
    created_at: datetime = Field(default_factory=datetime.now)


class LocalModel(BaseModel):
    """Scanned local model file."""
    
    id: Optional[int] = None
    file_path: str
    file_name: str
    file_size: int = 0
    file_hash: Optional[str] = None
    model_type: Optional[str] = None
    source_repo: Optional[str] = None
    source_platform: Optional[Platform] = None
    scanned_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(use_enum_values=True)


class ProgressInfo(BaseModel):
    """Download progress information for UI updates."""
    
    task_id: int
    downloaded_bytes: int
    total_bytes: int
    speed_bps: float
    eta_seconds: Optional[int] = None
    current_file: Optional[str] = None
    files_completed: int = 0
    files_total: int = 0
    
    @property
    def progress_percent(self) -> float:
        if self.total_bytes == 0:
            return 0.0
        return (self.downloaded_bytes / self.total_bytes) * 100
    
    @property
    def speed_formatted(self) -> str:
        """Format speed as human-readable string."""
        speed = self.speed_bps
        for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
            if speed < 1024:
                return f"{speed:.1f} {unit}"
            speed /= 1024
        return f"{speed:.1f} TB/s"
    
    @property
    def eta_formatted(self) -> str:
        """Format ETA as human-readable string."""
        if self.eta_seconds is None:
            return "Unknown"
        
        seconds = self.eta_seconds
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"


class RepoInfo(BaseModel):
    """Repository information from API."""
    
    repo_id: str
    platform: Platform = Platform.HUGGINGFACE
    repo_type: RepoType = RepoType.MODEL
    author: str
    name: str
    description: Optional[str] = None
    downloads: int = 0
    likes: int = 0
    tags: List[str] = Field(default_factory=list)
    last_modified: Optional[datetime] = None
    private: bool = False
    gated: bool = False
    files: List[Dict[str, Any]] = Field(default_factory=list)
    
    @property
    def display_name(self) -> str:
        return self.name or self.repo_id.split("/")[-1]
    
    model_config = ConfigDict(use_enum_values=True)


class Notification(BaseModel):
    """UI notification."""
    
    message: str
    level: str = "info"  # 'info', 'success', 'warning', 'error'
    duration: int = 5000  # milliseconds
    action: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None
