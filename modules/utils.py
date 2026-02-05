"""
Studio Pack Generator Online - Utility Functions

Provides helper functions for SHA1 hashing, file naming, and path manipulation.
"""

import hashlib
import os
import re
from pathlib import Path
from typing import Optional


def compute_sha1(file_path: str) -> str:
    """
    Compute SHA1 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        SHA1 hash as hexadecimal string
    """
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha1.update(chunk)
    return sha1.hexdigest()


def compute_sha1_from_bytes(data: bytes) -> str:
    """
    Compute SHA1 hash from bytes.
    
    Args:
        data: Bytes to hash
        
    Returns:
        SHA1 hash as hexadecimal string
    """
    return hashlib.sha1(data).hexdigest()


def clean_name(name: str) -> str:
    """
    Clean a file or folder name for display.
    
    - Removes leading numbers and separators (e.g., "01 - " or "12_")
    - Replaces underscores with spaces
    - Removes file extension
    
    Args:
        name: Original filename or folder name
        
    Returns:
        Cleaned name suitable for display and TTS
    """
    # Remove file extension
    name_without_ext = Path(name).stem
    
    # Remove leading numbers followed by separator
    # Matches: "01 - ", "12_", "1-", "01.", etc.
    cleaned = re.sub(r'^\d+[\s\-_.]+', '', name_without_ext)
    
    # Replace underscores with spaces
    cleaned = cleaned.replace('_', ' ')
    
    # Trim whitespace
    cleaned = cleaned.strip()
    
    # If cleaning removed everything, use original
    return cleaned if cleaned else name_without_ext


def get_asset_filename(file_path: str, extension: Optional[str] = None) -> str:
    """
    Generate asset filename using SHA1 hash.
    
    Args:
        file_path: Path to the source file
        extension: Optional extension override (without dot)
        
    Returns:
        Filename in format: {sha1}.{extension}
    """
    sha1 = compute_sha1(file_path)
    if extension is None:
        extension = Path(file_path).suffix.lstrip('.')
    return f"{sha1}.{extension}"


def ensure_dir(path: str) -> str:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        The path that was created/verified
    """
    os.makedirs(path, exist_ok=True)
    return path


def is_audio_file(filename: str) -> bool:
    """
    Check if a file is a supported audio format.
    
    Args:
        filename: Filename to check
        
    Returns:
        True if audio file, False otherwise
    """
    audio_extensions = {'.mp3', '.ogg', '.opus', '.wav', '.m4a', '.flac'}
    return Path(filename).suffix.lower() in audio_extensions


def is_image_file(filename: str) -> bool:
    """
    Check if a file is a supported image format.
    
    Args:
        filename: Filename to check
        
    Returns:
        True if image file, False otherwise
    """
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'}
    return Path(filename).suffix.lower() in image_extensions


def is_special_file(filename: str) -> bool:
    """
    Check if a file is a special control file (0-item, thumbnail, etc.).
    
    Args:
        filename: Filename to check
        
    Returns:
        True if special file, False otherwise
    """
    special_patterns = [
        '0-item.mp3', '0-item.png', '0-item.jpg',
        'thumbnail.png', 'thumbnail.jpg',
        'metadata.json', '0-config.json',
        '0-night-mode.mp3'
    ]
    return Path(filename).name.lower() in [p.lower() for p in special_patterns]


def sanitize_filename(filename: str) -> str:
    """
    Remove or replace characters that are invalid in filenames.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Replace problematic characters
    invalid_chars = '<>:"/\\|?*'
    result = filename
    for char in invalid_chars:
        result = result.replace(char, '_')
    return result


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string like "3:45" or "1:23:45"
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def generate_uuid() -> str:
    """
    Generate a unique identifier for story nodes.
    
    Returns:
        UUID string
    """
    import uuid
    return str(uuid.uuid4())
