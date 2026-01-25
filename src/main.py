"""
AutoFolder AI - Main Entry Point

This is the main application launcher that initializes the UI and core systems.
"""

import sys
import logging
from pathlib import Path

# Fix Windows taskbar icon (must be BEFORE QApplication import)
import os
if os.name == 'nt':  # Windows only
    import ctypes
    # Tell Windows this is a unique app (not Python)
    myappid = 'autofolder.ai.organizer.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from ui.main_window import MainWindow
from utils.config_manager import ConfigManager
from utils.logger import setup_logger
from utils.icon_manager import IconManager


def main():
    """Initialize and run the AutoFolder AI application."""
    
    # Setup logging
    logger = setup_logger()
    logger.info("=" * 60)
    logger.info("AutoFolder AI Starting...")
    logger.info("=" * 60)
    
    # Load configuration
    config = ConfigManager()
    app_config = config.get('app', {})
    
    logger.info(f"Version: {app_config.get('version', '1.0.0')}")
    logger.info(f"Mode: {app_config.get('mode', 'base').upper()}")
    
    # Create Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("AutoFolder AI")
    app.setOrganizationName("AutoFolder")
    
    # Set application icon globally
    app.setWindowIcon(IconManager.get_app_icon())
    
    # Set high DPI scaling (suppress Qt6 deprecation warnings)
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        try:
            if hasattr(Qt, 'AA_EnableHighDpiScaling'):
                QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        except:
            pass
        try:
            if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
                QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        except:
            pass
    
    # Create and show main window
    try:
        window = MainWindow(config)
        window.show()
        
        logger.info("Application window opened successfully")
        
        # Run event loop
        exit_code = app.exec()
        
        logger.info(f"Application closing with code: {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
