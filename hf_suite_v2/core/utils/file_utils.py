"""
File utility functions.
"""

import hashlib
import os
import re
from pathlib import Path
from typing import Optional


def format_bytes(bytes_val: int, precision: int = 1) -> str:
    """
    Format bytes as human-readable string.
    
    Args:
        bytes_val: Number of bytes
        precision: Decimal precision
        
    Returns:
        Formatted string (e.g., "1.5 GB")
    """
    if bytes_val < 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if bytes_val < 1024:
            return f"{bytes_val:.{precision}f} {unit}"
        bytes_val /= 1024
    
    return f"{bytes_val:.{precision}f} EB"


def format_duration(seconds: Optional[int]) -> str:
    """
    Format duration in seconds as human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "2h 15m 30s")
    """
    if seconds is None or seconds < 0:
        return "Unknown"
    
    if seconds < 60:
        return f"{seconds}s"
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if hours < 24:
        return f"{hours}h {remaining_minutes}m"
    
    days = hours // 24
    remaining_hours = hours % 24
    return f"{days}d {remaining_hours}h"


def safe_filename(filename: str, max_length: int = 200) -> str:
    """
    Sanitize filename to be safe for all platforms.
    
    Args:
        filename: Original filename
        max_length: Maximum length of result
        
    Returns:
        Sanitized filename
    """
    # Remove or replace dangerous characters
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    safe = safe.strip('. ')
    
    # Truncate if too long (preserve extension)
    if len(safe) > max_length:
        name, ext = os.path.splitext(safe)
        safe = name[:max_length - len(ext)] + ext
    
    # Fallback if empty
    if not safe:
        safe = "unnamed"
    
    return safe


def ensure_dir(path: str) -> Path:
    """
    Ensure directory exists, create if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        Path object of the directory
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_file_hash(
    filepath: str,
    algorithm: str = "sha256",
    chunk_size: int = 8192,
    max_bytes: Optional[int] = None
) -> str:
    """
    Calculate hash of a file.
    
    Args:
        filepath: Path to file
        algorithm: Hash algorithm (sha256, md5, etc.)
        chunk_size: Read chunk size
        max_bytes: Maximum bytes to hash (for large files)
        
    Returns:
        Hex digest of hash
    """
    hasher = hashlib.new(algorithm)
    bytes_read = 0
    
    with open(filepath, "rb") as f:
        while True:
            if max_bytes and bytes_read >= max_bytes:
                break
            
            read_size = chunk_size
            if max_bytes:
                read_size = min(chunk_size, max_bytes - bytes_read)
            
            data = f.read(read_size)
            if not data:
                break
            
            hasher.update(data)
            bytes_read += len(data)
    
    return hasher.hexdigest()


def get_file_size(filepath: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        filepath: Path to file
        
    Returns:
        File size in bytes, or 0 if file doesn't exist
    """
    try:
        return os.path.getsize(filepath)
    except OSError:
        return 0


def split_path(filepath: str) -> tuple:
    """
    Split file path into directory, filename, and extension.
    
    Args:
        filepath: Full file path
        
    Returns:
        Tuple of (directory, filename_without_ext, extension)
    """
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    name, ext = os.path.splitext(filename)
    return directory, name, ext
