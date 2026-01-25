"""
Windows Folder Icon Customizer

Sets custom icons for folders based on their category (Documents, Images, Videos, etc.)
This is a Windows-specific feature using desktop.ini files.

Works by:
1. Creating .ico files for each category
2. Creating desktop.ini in each folder
3. Setting folder attributes to use custom icon
"""

import logging
import os
import ctypes
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class WindowsFolderIconCustomizer:
    """Customizes folder icons on Windows using desktop.ini files."""
    
    # Category icon colors and symbols
    CATEGORY_ICONS = {
        'Documents': {'color': (59, 130, 246), 'emoji': '📄'},  # Blue
        'Images': {'color': (34, 197, 94), 'emoji': '🖼️'},  # Green
        'Videos': {'color': (239, 68, 68), 'emoji': '🎬'},  # Red
        'Audio': {'color': (249, 115, 22), 'emoji': '🎵'},  # Orange
        'Code': {'color': (139, 92, 246), 'emoji': '💻'},  # Purple
        'Archives': {'color': (234, 179, 8), 'emoji': '📦'},  # Yellow
        'Installers': {'color': (20, 184, 166), 'emoji': '⚙️'},  # Teal
        'Games': {'color': (236, 72, 153), 'emoji': '🎮'},  # Pink
        'Movies': {'color': (220, 38, 38), 'emoji': '🎞️'},  # Dark Red
        'Software': {'color': (99, 102, 241), 'emoji': '💿'},  # Indigo
        'Books': {'color': (168, 85, 247), 'emoji': '📚'},  # Purple
        'Music': {'color': (234, 88, 12), 'emoji': '🎸'},  # Orange
    }
    
    def __init__(self, icon_folder: Path = None):
        """
        Initialize the folder icon customizer.
        
        Args:
            icon_folder: Where to store .ico files (default: resources/folder_icons/)
        """
        if icon_folder is None:
            icon_folder = Path(__file__).parent.parent.parent / 'resources' / 'folder_icons'
        
        self.icon_folder = icon_folder
        self.icon_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Folder icon customizer initialized: {self.icon_folder}")
    
    def create_folder_icon(self, category: str) -> Optional[Path]:
        """
        Create a .ico file for the given category.
        
        Args:
            category: Category name (Documents, Images, etc.)
        
        Returns:
            Path to created .ico file or None if failed
        """
        try:
            if category not in self.CATEGORY_ICONS:
                logger.warning(f"Unknown category: {category}")
                return None
            
            icon_data = self.CATEGORY_ICONS[category]
            color = icon_data['color']
            
            # Create icon image (256x256 for high quality)
            size = 256
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw folder shape
            folder_color = color + (230,)  # Add alpha
            
            # Folder tab (top)
            tab_width = 100
            tab_height = 30
            tab_y = 50
            draw.rounded_rectangle(
                [20, tab_y, 20 + tab_width, tab_y + tab_height],
                radius=10,
                fill=tuple(max(0, c - 30) for c in color) + (230,)
            )
            
            # Main folder body
            body_y = tab_y + tab_height - 5
            body_height = 150
            draw.rounded_rectangle(
                [20, body_y, size - 20, body_y + body_height],
                radius=15,
                fill=folder_color
            )
            
            # Add emoji/text (simplified - just text)
            try:
                font = ImageFont.truetype("seguiemj.ttf", 80)  # Segoe UI Emoji
            except:
                font = ImageFont.load_default()
            
            # Draw text in center
            text = icon_data['emoji']
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = (size - text_width) // 2
            text_y = body_y + (body_height - text_height) // 2
            draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)
            
            # Save as .ico (multiple sizes for compatibility)
            ico_path = self.icon_folder / f"{category.lower()}_folder.ico"
            img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
            
            logger.info(f"Created icon: {ico_path}")
            return ico_path
            
        except Exception as e:
            logger.error(f"Failed to create icon for {category}: {e}", exc_info=True)
            return None
    
    def set_folder_icon(self, folder_path: Path, category: str) -> bool:
        """
        Set custom icon for a Windows folder.
        
        Args:
            folder_path: Path to folder
            category: Category name
        
        Returns:
            True if successful, False otherwise
        """
        if os.name != 'nt':
            logger.warning("Folder icon customization only works on Windows")
            return False
        
        try:
            # Create icon file if it doesn't exist
            ico_path = self.icon_folder / f"{category.lower()}_folder.ico"
            if not ico_path.exists():
                ico_path = self.create_folder_icon(category)
                if not ico_path:
                    return False
            
            # Create desktop.ini content
            desktop_ini = folder_path / 'desktop.ini'
            ini_content = f"""[.ShellClassInfo]
IconResource={str(ico_path)},0
[ViewState]
Mode=
Vid=
FolderType=Generic
"""
            
            # Write desktop.ini
            with open(desktop_ini, 'w', encoding='utf-8') as f:
                f.write(ini_content)
            
            # Set file attributes: hidden + system
            ctypes.windll.kernel32.SetFileAttributesW(str(desktop_ini), 0x02 | 0x04)
            
            # Set folder as system folder (required for icon to show)
            ctypes.windll.kernel32.SetFileAttributesW(str(folder_path), 0x04)
            
            # Refresh icon cache (optional - requires SHChangeNotify)
            try:
                SHCNE_ASSOCCHANGED = 0x08000000
                SHCNF_IDLIST = 0x0000
                ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)
            except:
                pass
            
            logger.info(f"Set custom icon for folder: {folder_path.name} ({category})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set folder icon: {e}", exc_info=True)
            return False
    
    def customize_organized_folders(self, base_folder: Path, category_folders: dict) -> int:
        """
        Set custom icons for all organized category folders.
        
        Args:
            base_folder: Root folder containing organized folders
            category_folders: Dict mapping category names to folder paths
        
        Returns:
            Number of folders successfully customized
        """
        count = 0
        
        for category, folder_path in category_folders.items():
            if folder_path.exists() and folder_path.is_dir():
                if self.set_folder_icon(folder_path, category):
                    count += 1
                    
                    # Also customize subfolders (AI groups)
                    for subfolder in folder_path.iterdir():
                        if subfolder.is_dir():
                            # Use same category icon for subfolders
                            if self.set_folder_icon(subfolder, category):
                                count += 1
        
        logger.info(f"Customized {count} folder icons")
        return count
