"""
ModelScope API wrapper.
"""

import logging
import os
from typing import Dict, List, Optional

from .base import (
    BaseAPI, RepoFile, RepoMetadata,
    APIError, AuthenticationError, NotFoundError
)

logger = logging.getLogger(__name__)

DEFAULT_ENDPOINT = "https://modelscope.cn"


class ModelScopeAPI(BaseAPI):
    """
    ModelScope API client.
    
    Wraps modelscope library for Chinese model hub access.
    """
    
    def __init__(
        self,
        token: Optional[str] = None,
        endpoint: Optional[str] = None,
    ):
        """
        Initialize ModelScope API client.
        
        Args:
            token: ModelScope token
            endpoint: Custom endpoint URL
        """
        if endpoint is None:
            endpoint = DEFAULT_ENDPOINT
        
        super().__init__(token=token, endpoint=endpoint)
        
        self._api = None
    
    @property
    def platform_name(self) -> str:
        return "modelscope"
    
    @property
    def api(self):
        """Lazy-load ModelScope HubApi."""
        if self._api is None:
            try:
                from modelscope.hub.api import HubApi
                self._api = HubApi()
                if self.token:
                    self._api.login(self.token)
            except ImportError:
                raise APIError("modelscope package not installed. Run: pip install modelscope")
        return self._api
    
    def get_repo_info(self, repo_id: str, repo_type: str = "model") -> RepoMetadata:
        """Get repository metadata from ModelScope."""
        try:
            model_info = self.api.get_model(repo_id)
            
            return RepoMetadata(
                repo_id=repo_id,
                platform="modelscope",
                repo_type=repo_type,
                author=repo_id.split("/")[0] if "/" in repo_id else "",
                name=repo_id.split("/")[-1],
                description=model_info.get("Description", ""),
                downloads=model_info.get("Downloads", 0),
                likes=model_info.get("Likes", 0),
                tags=model_info.get("Tags", []),
                private=model_info.get("Private", False),
            )
            
        except Exception as e:
            error_str = str(e).lower()
            
            if "401" in error_str or "unauthorized" in error_str:
                raise AuthenticationError(f"Authentication required for {repo_id}")
            elif "404" in error_str or "not found" in error_str:
                raise NotFoundError(f"Repository not found: {repo_id}")
            
            raise APIError(f"Failed to get repo info: {e}")
    
    def list_files(self, repo_id: str, repo_type: str = "model") -> List[RepoFile]:
        """List files in a ModelScope repository."""
        try:
            file_list = self.api.get_model_files(repo_id)
            
            files = []
            for file_info in file_list:
                # Handle different response formats
                if isinstance(file_info, dict):
                    path = file_info.get("Path") or file_info.get("name", "")
                    size = file_info.get("Size", 0)
                else:
                    path = str(file_info)
                    size = 0
                
                if path:
                    files.append(RepoFile(
                        path=path,
                        size=size,
                    ))
            
            return sorted(files, key=lambda f: f.path)
            
        except Exception as e:
            raise APIError(f"Failed to list files: {e}")
    
    def download_file(
        self,
        repo_id: str,
        filename: str,
        local_path: str,
        repo_type: str = "model",
        progress_callback: callable = None,
    ) -> str:
        """Download a file from ModelScope."""
        try:
            from modelscope.hub.file_download import model_file_download
            
            result = model_file_download(
                model_id=repo_id,
                file_path=filename,
                cache_dir=local_path,
            )
            
            return result
            
        except ImportError:
            raise APIError("modelscope package not installed")
        except Exception as e:
            raise APIError(f"Download failed: {e}")
    
    def download_model(
        self,
        repo_id: str,
        local_path: str,
        revision: str = None,
    ) -> str:
        """Download entire model from ModelScope."""
        try:
            from modelscope.hub.snapshot_download import snapshot_download
            
            result = snapshot_download(
                model_id=repo_id,
                cache_dir=local_path,
                revision=revision,
            )
            
            return result
            
        except ImportError:
            raise APIError("modelscope package not installed")
        except Exception as e:
            raise APIError(f"Download failed: {e}")
    
    def search(
        self,
        query: str,
        limit: int = 20,
        filters: Dict = None,
    ) -> List[RepoMetadata]:
        """Search ModelScope models."""
        try:
            # ModelScope search API
            results = self.api.list_models(
                query=query,
                page_size=limit,
            )
            
            models = []
            for model in results.get("Data", {}).get("Models", []):
                models.append(RepoMetadata(
                    repo_id=model.get("Name", ""),
                    platform="modelscope",
                    repo_type="model",
                    author=model.get("Name", "").split("/")[0] if "/" in model.get("Name", "") else "",
                    name=model.get("Name", "").split("/")[-1],
                    description=model.get("Description", ""),
                    downloads=model.get("Downloads", 0),
                    likes=model.get("Likes", 0),
                    tags=model.get("Tags", []),
                ))
            
            return models
            
        except Exception as e:
            logger.warning(f"ModelScope search failed: {e}")
            return []
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        try:
            # Try to access user info
            return self.token is not None
        except Exception:
            return False
