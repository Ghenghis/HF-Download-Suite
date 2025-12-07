"""
Custom exceptions for HF Download Suite.

Provides meaningful error messages with actionable fixes.
"""


class HFSuiteError(Exception):
    """Base exception for HF Download Suite."""
    
    # Whether this error can be retried
    is_retryable: bool = False
    
    def __init__(self, message: str, suggestion: str = None):
        self.message = message
        self.suggestion = suggestion
        super().__init__(self.full_message)
    
    @property
    def full_message(self) -> str:
        if self.suggestion:
            return f"{self.message}\n\nSuggested fix: {self.suggestion}"
        return self.message


class DownloadError(HFSuiteError):
    """Base class for download-related errors."""
    pass


class InsufficientSpaceError(DownloadError):
    """Raised when there isn't enough disk space for download."""
    
    is_retryable = False
    
    def __init__(self, required_bytes: int, available_bytes: int, path: str):
        self.required_bytes = required_bytes
        self.available_bytes = available_bytes
        self.path = path
        
        required_gb = required_bytes / (1024 ** 3)
        available_gb = available_bytes / (1024 ** 3)
        
        message = (
            f"Insufficient disk space on '{path}'\n"
            f"Required: {required_gb:.2f} GB\n"
            f"Available: {available_gb:.2f} GB"
        )
        suggestion = (
            f"Free up at least {(required_bytes - available_bytes) / (1024 ** 3):.2f} GB "
            f"or choose a different download location."
        )
        super().__init__(message, suggestion)


class AuthenticationError(HFSuiteError):
    """Raised when authentication fails."""
    
    def __init__(self, platform: str, reason: str = None):
        self.platform = platform
        self.reason = reason
        
        message = f"Authentication failed for {platform}"
        if reason:
            message += f": {reason}"
        
        if platform == "huggingface":
            suggestion = (
                "1. Go to Settings tab and add your HuggingFace token\n"
                "2. Get a token from: https://huggingface.co/settings/tokens\n"
                "3. Make sure the token has 'read' access"
            )
        elif platform == "modelscope":
            suggestion = (
                "1. Set MODELSCOPE_API_TOKEN environment variable\n"
                "2. Get a token from: https://modelscope.cn/my/myaccesstoken"
            )
        else:
            suggestion = f"Please check your {platform} credentials"
        
        super().__init__(message, suggestion)


class NetworkError(DownloadError):
    """Raised for network-related failures."""
    
    is_retryable = True  # Network errors are usually transient
    
    def __init__(self, url: str = None, reason: str = None):
        self.url = url
        self.reason = reason
        
        if url:
            message = f"Network error accessing: {url}"
        else:
            message = "Network error occurred"
        
        if reason:
            message += f"\nReason: {reason}"
        
        suggestion = (
            "1. Check your internet connection\n"
            "2. Try using a mirror (Settings > Network > Use HF Mirror)\n"
            "3. Check if a proxy is needed (Settings > Network > Proxy)"
        )
        super().__init__(message, suggestion)


class RepositoryNotFoundError(HFSuiteError):
    """Raised when repository doesn't exist or is inaccessible."""
    
    def __init__(self, repo_id: str, platform: str):
        self.repo_id = repo_id
        self.platform = platform
        
        message = f"Repository not found: {repo_id} on {platform}"
        suggestion = (
            f"1. Verify the repository ID is correct\n"
            f"2. Check if the repository is private (requires authentication)\n"
            f"3. Verify the repository exists at: https://{platform}.co/{repo_id}"
        )
        super().__init__(message, suggestion)


class GatedModelError(HFSuiteError):
    """Raised when trying to access a gated model without permission."""
    
    def __init__(self, repo_id: str):
        self.repo_id = repo_id
        
        message = f"Access denied to gated model: {repo_id}"
        suggestion = (
            f"1. Go to https://huggingface.co/{repo_id} and accept the license\n"
            "2. Make sure you're authenticated with a token that has access\n"
            "3. Some models require organization membership"
        )
        super().__init__(message, suggestion)


class DownloadInterruptedError(HFSuiteError):
    """Raised when download is interrupted (can be resumed)."""
    
    def __init__(self, task_id: int, progress_percent: float):
        self.task_id = task_id
        self.progress_percent = progress_percent
        
        message = f"Download interrupted at {progress_percent:.1f}%"
        suggestion = "Click 'Resume' to continue downloading from where you left off."
        super().__init__(message, suggestion)


class FileVerificationError(HFSuiteError):
    """Raised when downloaded file fails verification."""
    
    def __init__(self, file_path: str, expected_hash: str = None, actual_hash: str = None):
        self.file_path = file_path
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
        
        message = f"File verification failed: {file_path}"
        if expected_hash and actual_hash:
            message += f"\nExpected: {expected_hash[:16]}...\nGot: {actual_hash[:16]}..."
        
        suggestion = (
            "1. Delete the corrupted file and re-download\n"
            "2. Check your disk for errors\n"
            "3. Try downloading from a mirror"
        )
        super().__init__(message, suggestion)
