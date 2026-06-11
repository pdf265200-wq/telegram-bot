"""
Helper utility functions
"""

import os
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Set

def format_file_size(size_in_bytes: int) -> str:
    """Convert file size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} TB"

def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return Path(filename).suffix.lower()

def is_allowed_file_type(filename: str, allowed_extensions: Set[str]) -> bool:
    """Check if file type is allowed"""
    return get_file_extension(filename) in allowed_extensions

def sanitize_filename(filename: str) -> str:
    """Remove potentially dangerous characters from filename"""
    # Remove path separators and other dangerous characters
    filename = os.path.basename(filename)
    # Replace spaces and special characters
    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-'))
    return filename

def create_temp_file(suffix: str = '', directory: str = 'temp') -> str:
    """Create a temporary file and return its path"""
    os.makedirs(directory, exist_ok=True)
    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
        dir=directory
    )
    return temp_file.name

def cleanup_temp_files(directory: str = 'temp', max_age_hours: int = 24):
    """Clean up temporary files older than specified hours"""
    try:
        now = datetime.now()
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            file_time = datetime.fromtimestamp(os.path.getctime(filepath))
            if (now - file_time).total_seconds() > max_age_hours * 3600:
                try:
                    if os.path.isfile(filepath):
                        os.unlink(filepath)
                except Exception:
                    pass
    except Exception:
        pass

def create_directories():
    """Create necessary directories for the bot"""
    directories = ['data', 'temp', 'logs']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def get_mime_type(file_path: str) -> str:
    """Get MIME type of a file"""
    import mimetypes
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'
