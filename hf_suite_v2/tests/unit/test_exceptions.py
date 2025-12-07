"""
Tests for custom exceptions.
"""

import pytest

from hf_suite_v2.core.exceptions import (
    HFSuiteError,
    InsufficientSpaceError,
    AuthenticationError,
    NetworkError,
    RepositoryNotFoundError,
    GatedModelError,
    DownloadInterruptedError,
    FileVerificationError,
)


class TestHFSuiteError:
    """Tests for base exception."""
    
    def test_message_only(self):
        """Test exception with message only."""
        error = HFSuiteError("Test error")
        assert str(error) == "Test error"
        assert error.suggestion is None
    
    def test_message_with_suggestion(self):
        """Test exception with message and suggestion."""
        error = HFSuiteError("Test error", "Try this fix")
        assert "Test error" in str(error)
        assert "Try this fix" in str(error)


class TestInsufficientSpaceError:
    """Tests for disk space error."""
    
    def test_basic(self):
        """Test insufficient space error."""
        error = InsufficientSpaceError(
            required_bytes=10 * 1024 ** 3,  # 10 GB
            available_bytes=5 * 1024 ** 3,   # 5 GB
            path="C:/downloads"
        )
        
        assert "10.00 GB" in str(error)
        assert "5.00 GB" in str(error)
        assert "C:/downloads" in str(error)
        assert error.suggestion is not None
    
    def test_suggestion_includes_free_amount(self):
        """Test that suggestion mentions how much to free."""
        error = InsufficientSpaceError(
            required_bytes=10 * 1024 ** 3,
            available_bytes=5 * 1024 ** 3,
            path="/tmp"
        )
        # Should suggest freeing ~5 GB
        assert "5.00 GB" in error.suggestion or "5" in error.suggestion


class TestAuthenticationError:
    """Tests for authentication error."""
    
    def test_huggingface(self):
        """Test HuggingFace auth error."""
        error = AuthenticationError("huggingface", "401 Unauthorized")
        
        assert "huggingface" in str(error).lower()
        assert "401" in str(error)
        assert "token" in error.suggestion.lower()
        assert "huggingface.co" in error.suggestion
    
    def test_modelscope(self):
        """Test ModelScope auth error."""
        error = AuthenticationError("modelscope")
        
        assert "modelscope" in str(error).lower()
        assert "MODELSCOPE_API_TOKEN" in error.suggestion


class TestNetworkError:
    """Tests for network error."""
    
    def test_with_url(self):
        """Test network error with URL."""
        error = NetworkError(url="https://huggingface.co/api", reason="Connection timeout")
        
        assert "huggingface.co" in str(error)
        assert "timeout" in str(error).lower()
        assert "mirror" in error.suggestion.lower()
    
    def test_without_url(self):
        """Test network error without URL."""
        error = NetworkError()
        
        assert "network error" in str(error).lower()
        assert error.suggestion is not None


class TestRepositoryNotFoundError:
    """Tests for repo not found error."""
    
    def test_basic(self):
        """Test repo not found error."""
        error = RepositoryNotFoundError("user/nonexistent", "huggingface")
        
        assert "user/nonexistent" in str(error)
        assert error.suggestion is not None


class TestGatedModelError:
    """Tests for gated model error."""
    
    def test_basic(self):
        """Test gated model error."""
        error = GatedModelError("meta-llama/Llama-2-7b")
        
        assert "meta-llama/Llama-2-7b" in str(error)
        assert "accept the license" in error.suggestion.lower()


class TestDownloadInterruptedError:
    """Tests for download interrupted error."""
    
    def test_basic(self):
        """Test download interrupted error."""
        error = DownloadInterruptedError(task_id=42, progress_percent=67.5)
        
        assert "67.5%" in str(error)
        assert "resume" in error.suggestion.lower()


class TestFileVerificationError:
    """Tests for file verification error."""
    
    def test_basic(self):
        """Test file verification error."""
        error = FileVerificationError(
            file_path="/downloads/model.safetensors",
            expected_hash="abc123def456",
            actual_hash="xyz789000111"
        )
        
        assert "model.safetensors" in str(error)
        assert "abc123" in str(error)
        assert "xyz789" in str(error)
        assert "re-download" in error.suggestion.lower()
    
    def test_without_hashes(self):
        """Test without hash details."""
        error = FileVerificationError(file_path="/downloads/model.safetensors")
        
        assert "model.safetensors" in str(error)
        assert error.suggestion is not None
