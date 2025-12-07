"""
HuggingFace Hub API wrapper.
"""

import logging
import os
from typing import Dict, List, Optional

from .base import (
    BaseAPI, RepoFile, RepoMetadata,
    APIError, AuthenticationError, NotFoundError, RateLimitError
)

logger = logging.getLogger(__name__)

# Default HuggingFace endpoint
DEFAULT_ENDPOINT = "https://huggingface.co"
MIRROR_ENDPOINT = "https://hf-mirror.com"


class HuggingFaceAPI(BaseAPI):
    """
    HuggingFace Hub API client.
    
    Wraps huggingface_hub library with additional error handling
    and progress support.
    """
    
    def __init__(
        self,
        token: Optional[str] = None,
        endpoint: Optional[str] = None,
        use_mirror: bool = False,
    ):
        """
        Initialize HuggingFace API client.
        
        Args:
            token: HuggingFace token (or uses HF_TOKEN env var)
            endpoint: Custom endpoint URL
            use_mirror: Use hf-mirror.com instead of huggingface.co
        """
        # Check environment for token
        if token is None:
            token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        
        # Determine endpoint
        if endpoint is None:
            endpoint = MIRROR_ENDPOINT if use_mirror else DEFAULT_ENDPOINT
        
        super().__init__(token=token, endpoint=endpoint)
        
        self._api = None
    
    @property
    def platform_name(self) -> str:
        return "huggingface"
    
    @property
    def api(self):
        """Lazy-load HfApi."""
        if self._api is None:
            from huggingface_hub import HfApi
            self._api = HfApi(endpoint=self.endpoint, token=self.token)
        return self._api
    
    def get_repo_info(self, repo_id: str, repo_type: str = "model") -> RepoMetadata:
        """Get repository metadata from HuggingFace."""
        try:
            if repo_type == "model":
                info = self.api.model_info(repo_id)
            else:
                info = self.api.dataset_info(repo_id)
            
            return RepoMetadata(
                repo_id=info.id,
                platform="huggingface",
                repo_type=repo_type,
                author=info.author or info.id.split("/")[0],
                name=info.id.split("/")[-1],
                description=getattr(info, "description", ""),
                downloads=info.downloads or 0,
                likes=info.likes or 0,
                tags=list(info.tags) if info.tags else [],
                private=info.private if hasattr(info, "private") else False,
                gated=info.gated if hasattr(info, "gated") else False,
                last_modified=str(info.lastModified) if hasattr(info, "lastModified") else None,
            )
            
        except Exception as e:
            error_str = str(e).lower()
            
            if "401" in error_str or "unauthorized" in error_str:
                raise AuthenticationError(f"Authentication required for {repo_id}")
            elif "404" in error_str or "not found" in error_str:
                raise NotFoundError(f"Repository not found: {repo_id}")
            elif "429" in error_str or "rate limit" in error_str:
                raise RateLimitError("Rate limit exceeded")
            
            raise APIError(f"Failed to get repo info: {e}")
    
    def list_files(self, repo_id: str, repo_type: str = "model") -> List[RepoFile]:
        """List files in a HuggingFace repository."""
        try:
            if repo_type == "model":
                info = self.api.model_info(repo_id, files_metadata=True)
            else:
                info = self.api.dataset_info(repo_id, files_metadata=True)
            
            files = []
            if info.siblings:
                for sibling in info.siblings:
                    files.append(RepoFile(
                        path=sibling.rfilename,
                        size=sibling.size or 0,
                        blob_id=sibling.blob_id,
                        lfs=sibling.lfs is not None if hasattr(sibling, "lfs") else False,
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
        """Download a file from HuggingFace."""
        from huggingface_hub import hf_hub_download
        
        try:
            # Set environment for custom endpoint
            if self.endpoint and self.endpoint != DEFAULT_ENDPOINT:
                os.environ["HF_ENDPOINT"] = self.endpoint
            
            result = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                repo_type=repo_type,
                local_dir=local_path,
                token=self.token,
            )
            
            return result
            
        except Exception as e:
            raise APIError(f"Download failed: {e}")
        finally:
            # Restore endpoint
            if "HF_ENDPOINT" in os.environ:
                del os.environ["HF_ENDPOINT"]
    
    def search(
        self,
        query: str,
        limit: int = 20,
        filters: Dict = None,
    ) -> List[RepoMetadata]:
        """Search HuggingFace models."""
        from huggingface_hub import ModelFilter
        
        try:
            model_filter = ModelFilter()
            
            if filters:
                if filters.get("task"):
                    model_filter.task = filters["task"]
                if filters.get("library"):
                    model_filter.library = filters["library"]
            
            results = self.api.list_models(
                search=query,
                filter=model_filter,
                limit=limit,
                sort="downloads",
                direction=-1,
            )
            
            models = []
            for model in results:
                models.append(RepoMetadata(
                    repo_id=model.id,
                    platform="huggingface",
                    repo_type="model",
                    author=model.id.split("/")[0] if "/" in model.id else "",
                    name=model.id.split("/")[-1],
                    downloads=model.downloads or 0,
                    likes=model.likes or 0,
                    tags=list(model.tags) if model.tags else [],
                    private=model.private if hasattr(model, "private") else False,
                    gated=model.gated if hasattr(model, "gated") else False,
                ))
            
            return models
            
        except Exception as e:
            raise APIError(f"Search failed: {e}")
    
    def whoami(self) -> Optional[Dict]:
        """Get current user info (if authenticated)."""
        try:
            return self.api.whoami()
        except Exception:
            return None
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        info = self.whoami()
        return info is not None
