"""
Folder Icon Manager - Creates custom category-specific folder icons

Generates folder icons with visual indicators for different file categories:
- Documents: Blue folder with document icon
- Images: Green folder with image icon
- Videos: Red folder with video icon
- Audio: Orange folder with music icon
- Code: Purple folder with code brackets
- Archives: Yellow folder with zip icon
- Installers: Teal folder with setup icon
"""

import logging
from pathlib import Path
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtCore import Qt, QRect

logger = logging.getLogger(__name__)


class FolderIconManager:
    """Manages custom folder icons for different categories."""
    
    # Category colors and symbols
    CATEGORY_STYLES = {
        'Documents': {'color': '#3B82F6', 'symbol': '📄', 'text_color': '#1E3A8A'},
        'Images': {'color': '#22C55E', 'symbol': '🖼️', 'text_color': '#166534'},
        'Videos': {'color': '#EF4444', 'symbol': '🎬', 'text_color': '#991B1B'},
        'Audio': {'color': '#F97316', 'symbol': '🎵', 'text_color': '#9A3412'},
        'Code': {'color': '#8B5CF6', 'symbol': '💻', 'text_color': '#5B21B6'},
        'Archives': {'color': '#EAB308', 'symbol': '📦', 'text_color': '#854D0E'},
        'Installers': {'color': '#14B8A6', 'symbol': '⚙️', 'text_color': '#115E59'},
        'Other': {'color': '#6B7280', 'symbol': '📁', 'text_color': '#374151'},
    }
    
    _icon_cache = {}
    
    @classmethod
    def get_folder_icon(cls, category: str) -> QIcon:
        """
        Get a custom folder icon for the given category.
        
        Args:
            category: File category (Documents, Images, Videos, etc.)
        
        Returns:
            QIcon with custom category-specific design
        """
        # Check cache first
        if category in cls._icon_cache:
            return cls._icon_cache[category]
        
        # Get style for category (default to 'Other')
        style = cls.CATEGORY_STYLES.get(category, cls.CATEGORY_STYLES['Other'])
        
        # Create icon
        icon = cls._create_folder_icon(
            color=style['color'],
            symbol=style['symbol'],
            text_color=style['text_color']
        )
        
        # Cache it
        cls._icon_cache[category] = icon
        logger.debug(f"Created folder icon for category: {category}")
        
        return icon
    
    @classmethod
    def _create_folder_icon(cls, color: str, symbol: str, text_color: str) -> QIcon:
        """
        Create a custom folder icon with specified color and symbol.
        
        Args:
            color: Main folder color (hex)
            symbol: Emoji/text symbol to display
            text_color: Color for the symbol (hex)
        
        Returns:
            QIcon with custom design
        """
        # Create pixmap (48x48 for good quality)
        size = 48
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw folder shape
        folder_color = QColor(color)
        folder_color.setAlpha(230)  # Slight transparency
        
        # Folder tab (top)
        tab_rect = QRect(2, 8, 20, 8)
        painter.setBrush(QBrush(folder_color.darker(110)))
        painter.setPen(QPen(folder_color.darker(130), 1))
        painter.drawRoundedRect(tab_rect, 2, 2)
        
        # Main folder body
        body_rect = QRect(2, 14, size - 4, size - 16)
        painter.setBrush(QBrush(folder_color))
        painter.setPen(QPen(folder_color.darker(120), 2))
        painter.drawRoundedRect(body_rect, 4, 4)
        
        # Add symbol/emoji in center
        font = QFont("Segoe UI Emoji", 16)
        painter.setFont(font)
        painter.setPen(QColor(text_color))
        
        text_rect = QRect(0, 16, size, size - 16)
        painter.drawText(text_rect, Qt.AlignCenter, symbol)
        
        painter.end()
        
        return QIcon(pixmap)
    
    @classmethod
    def get_emoji_for_category(cls, category: str) -> str:
        """
        Get the emoji symbol for a category.
        
        Args:
            category: File category name
        
        Returns:
            Emoji string
        """
        style = cls.CATEGORY_STYLES.get(category, cls.CATEGORY_STYLES['Other'])
        return style['symbol']
    
    @classmethod
    def clear_cache(cls):
        """Clear the icon cache."""
        cls._icon_cache.clear()
        logger.info("Folder icon cache cleared")
