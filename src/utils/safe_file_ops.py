"""
Safe File Operations

Provides wrapper functions to safely access file stats, handling all edge cases:
- FileNotFoundError (deleted files, symlinks)
- PermissionError (system files, protected files)
- OSError (network files, corrupted files)
- Any other filesystem errors

Use these instead of direct Path.stat() calls to prevent crashes.
"""

import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def safe_stat(file_path: Path):
    """
    Safely get file stats, handling all access errors.
    
    Args:
        file_path: Path to file
        
    Returns:
        os.stat_result or None if inaccessible
    """
    try:
        return file_path.stat()
    except (FileNotFoundError, PermissionError, OSError) as e:
        logger.debug(f"Cannot access file stats: {file_path} - {type(e).__name__}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error accessing file stats: {file_path} - {type(e).__name__}: {e}")
        return None


def safe_get_size(file_path: Path, default: int = 0) -> int:
    """
    Safely get file size, handling all access errors.
    
    Args:
        file_path: Path to file
        default: Default size if stat fails (default: 0)
        
    Returns:
        File size in bytes or default
    """
    try:
        return file_path.stat().st_size
    except (FileNotFoundError, PermissionError, OSError) as e:
        logger.debug(f"Cannot get file size: {file_path} - {type(e).__name__}")
        return default
    except Exception as e:
        logger.warning(f"Unexpected error getting file size: {file_path} - {type(e).__name__}: {e}")
        return default


def safe_get_mtime(file_path: Path, default: Optional[float] = None) -> float:
    """
    Safely get file modification time, handling all access errors.
    
    Args:
        file_path: Path to file
        default: Default mtime if stat fails (default: current time)
        
    Returns:
        Modification timestamp or default
    """
    try:
        return file_path.stat().st_mtime
    except (FileNotFoundError, PermissionError, OSError) as e:
        logger.debug(f"Cannot get file mtime: {file_path} - {type(e).__name__}")
        return default if default is not None else datetime.now().timestamp()
    except Exception as e:
        logger.warning(f"Unexpected error getting file mtime: {file_path} - {type(e).__name__}: {e}")
        return default if default is not None else datetime.now().timestamp()


def safe_exists(file_path: Path) -> bool:
    """
    Safely check if file exists, handling all access errors.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if file exists and is accessible, False otherwise
    """
    try:
        return file_path.exists()
    except (PermissionError, OSError) as e:
        logger.debug(f"Cannot check if file exists: {file_path} - {type(e).__name__}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error checking file exists: {file_path} - {type(e).__name__}: {e}")
        return False


def safe_is_file(file_path: Path) -> bool:
    """
    Safely check if path is a file, handling all access errors.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if path is a file and accessible, False otherwise
    """
    try:
        return file_path.is_file()
    except (PermissionError, OSError) as e:
        logger.debug(f"Cannot check if is file: {file_path} - {type(e).__name__}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error checking is_file: {file_path} - {type(e).__name__}: {e}")
        return False


def safe_is_dir(file_path: Path) -> bool:
    """
    Safely check if path is a directory, handling all access errors.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if path is a directory and accessible, False otherwise
    """
    try:
        return file_path.is_dir()
    except (PermissionError, OSError) as e:
        logger.debug(f"Cannot check if is directory: {file_path} - {type(e).__name__}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error checking is_dir: {file_path} - {type(e).__name__}: {e}")
        return False


def safe_iterdir(dir_path: Path):
    """
    Safely iterate directory contents, handling all access errors.
    
    Args:
        dir_path: Path to directory
        
    Yields:
        Path objects for accessible items only
    """
    try:
        for item in dir_path.iterdir():
            yield item
    except (PermissionError, OSError) as e:
        logger.debug(f"Cannot iterate directory: {dir_path} - {type(e).__name__}")
    except Exception as e:
        logger.warning(f"Unexpected error iterating directory: {dir_path} - {type(e).__name__}: {e}")


def safe_glob(dir_path: Path, pattern: str):
    """
    Safely glob directory with pattern, handling all access errors.
    
    Args:
        dir_path: Path to directory
        pattern: Glob pattern (e.g., '*.txt', '**/*.py')
        
    Yields:
        Path objects for matching accessible items only
    """
    try:
        for item in dir_path.glob(pattern):
            yield item
    except (PermissionError, OSError) as e:
        logger.debug(f"Cannot glob directory: {dir_path} with pattern '{pattern}' - {type(e).__name__}")
    except Exception as e:
        logger.warning(f"Unexpected error globbing directory: {dir_path} - {type(e).__name__}: {e}")
