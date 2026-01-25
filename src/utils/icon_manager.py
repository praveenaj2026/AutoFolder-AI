"""
Icon Manager - Provides custom icons for AutoFolder AI
"""

import os
from pathlib import Path
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QMessageBox

class IconManager:
    """Manages custom icons for the application."""
    
    _icons = {}
    _icon_dir = None
    
    @classmethod
    def initialize(cls):
        """Initialize icon directory path."""
        if cls._icon_dir is None:
            # Get the project root directory
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            cls._icon_dir = project_root / 'resources' / 'icons'
    
    @classmethod
    def get_icon(cls, name: str) -> QIcon:
        """
        Get a QIcon by name.
        
        Args:
            name: Icon name (without extension): 'info', 'warning', 'error', 'question', 'success', 'app_icon'
            
        Returns:
            QIcon object
        """
        cls.initialize()
        
        if name not in cls._icons:
            icon_path = cls._icon_dir / f'{name}.png'
            if icon_path.exists():
                cls._icons[name] = QIcon(str(icon_path))
            else:
                # Fallback to default icon
                cls._icons[name] = QIcon()
        
        return cls._icons[name]
    
    @classmethod
    def get_pixmap(cls, name: str, size: int = 64) -> QPixmap:
        """
        Get a QPixmap by name with specified size.
        
        Args:
            name: Icon name (without extension)
            size: Desired size in pixels
            
        Returns:
            QPixmap object
        """
        icon = cls.get_icon(name)
        return icon.pixmap(size, size)
    
    @classmethod
    def get_app_icon(cls) -> QIcon:
        """Get the main application icon."""
        return cls.get_icon('app_icon')
    
    @classmethod
    def set_message_box_icon(cls, msg_box: QMessageBox, icon_type: str):
        """
        Set custom icon for QMessageBox.
        
        Args:
            msg_box: QMessageBox instance
            icon_type: One of 'info', 'warning', 'error', 'question', 'success'
        """
        pixmap = cls.get_pixmap(icon_type, 64)
        msg_box.setIconPixmap(pixmap)
