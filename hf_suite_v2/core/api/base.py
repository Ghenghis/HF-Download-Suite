"""
Base API class and common exceptions.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""
    
    def __init__(self, message: str, status_code: int = None, response: Any = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response


class AuthenticationError(APIError):
    """Raised when authentication fails."""
    pass


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    pass


class NotFoundError(APIError):
    """Raised when resource is not found."""
    pass


@dataclass
class RepoFile:
    """Represents a file in a repository."""
    path: str
    size: int
    blob_id: Optional[str] = None
    lfs: bool = False
    sha256: Optional[str] = None


@dataclass
class RepoMetadata:
    """Repository metadata."""
    repo_id: str
    platform: str
    repo_type: str = "model"
    author: str = ""
    name: str = ""
    description: str = ""
    downloads: int = 0
    likes: int = 0
    tags: List[str] = None
    private: bool = False
    gated: bool = False
    last_modified: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class BaseAPI(ABC):
    """
    Abstract base class for platform APIs.
    
    Subclasses must implement:
    - get_repo_info()
    - list_files()
    - download_file()
    """
    
    def __init__(self, token: Optional[str] = None, endpoint: Optional[str] = None):
        """
        Initialize API client.
        
        Args:
            token: Authentication token
            endpoint: Custom API endpoint
        """
        self.token = token
        self.endpoint = endpoint
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return platform name."""
        pass
    
    @abstractmethod
    def get_repo_info(self, repo_id: str, repo_type: str = "model") -> RepoMetadata:
        """
        Get repository metadata.
        
        Args:
            repo_id: Repository ID (e.g., "user/model")
            repo_type: Repository type ("model" or "dataset")
            
        Returns:
            RepoMetadata object
            
        Raises:
            NotFoundError: If repository doesn't exist
            AuthenticationError: If authentication required/failed
        """
        pass
    
    @abstractmethod
    def list_files(self, repo_id: str, repo_type: str = "model") -> List[RepoFile]:
        """
        List files in a repository.
        
        Args:
            repo_id: Repository ID
            repo_type: Repository type
            
        Returns:
            List of RepoFile objects
        """
        pass
    
    @abstractmethod
    def download_file(
        self,
        repo_id: str,
        filename: str,
        local_path: str,
        repo_type: str = "model",
        progress_callback: callable = None,
    ) -> str:
        """
        Download a single file.
        
        Args:
            repo_id: Repository ID
            filename: File path within repository
            local_path: Local destination path
            repo_type: Repository type
            progress_callback: Optional callback for progress updates
            
        Returns:
            Path to downloaded file
        """
        pass
    
    def search(
        self,
        query: str,
        limit: int = 20,
        filters: Dict = None,
    ) -> List[RepoMetadata]:
        """
        Search for repositories.
        
        Args:
            query: Search query
            limit: Maximum results
            filters: Optional filter criteria
            
        Returns:
            List of matching repositories
        """
        raise NotImplementedError("Search not implemented for this platform")
    
    def validate_repo_id(self, repo_id: str) -> bool:
        """
        Validate repository ID format.
        
        Args:
            repo_id: Repository ID to validate
            
        Returns:
            True if valid format
        """
        if not repo_id:
            return False
        
        parts = repo_id.split("/")
        if len(parts) != 2:
            return False
        
        return all(part and not part.startswith(".") for part in parts)
