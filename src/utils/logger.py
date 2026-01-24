"""
Logger Setup

Configures logging for the application.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logger(
    name: str = None,
    log_file: str = None,  # Will use Documents/AutoFolder_Logs/autofolder.log by default
    level: str = 'DEBUG',  # Changed to DEBUG for detailed output
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5  # Keep more log history
) -> logging.Logger:
    """
    Setup application logger.
    
    Args:
        name: Logger name
        log_file: Path to log file (defaults to Documents/AutoFolder_Logs)
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        max_bytes: Max log file size
        backup_count: Number of backup files
        
    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler - create logs in Documents/AutoFolder_Logs for easy access
    try:
        if log_file is None:
            # Default to Documents/AutoFolder_Logs
            documents_path = Path.home() / 'OneDrive' / 'Documents'
            if not documents_path.exists():
                documents_path = Path.home() / 'Documents'
            log_file = documents_path / 'AutoFolder_Logs' / 'autofolder.log'
        
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        
        # Log where logs are being saved
        logger.info(f"Log file: {log_file}")
    except Exception as e:
        logger.warning(f"Could not create log file: {e}")
    
    return logger
