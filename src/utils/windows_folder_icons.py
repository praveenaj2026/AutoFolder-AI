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
import sys
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
        'Torrents': {'color': (5, 150, 105), 'emoji': '🌊'},  # Emerald
        'AutoFolder_Logs': {'color': (107, 114, 128), 'emoji': '📋'},  # Gray
        'Logs': {'color': (107, 114, 128), 'emoji': '📋'},  # Gray
        'Other': {'color': (156, 163, 175), 'emoji': '📂'},  # Light Gray
        'Fonts': {'color': (244, 63, 94), 'emoji': '🔤'},  # Rose
        'Data': {'color': (14, 165, 233), 'emoji': '💾'},  # Sky Blue
        'DATE_FOLDER': {'color': (209, 213, 219), 'emoji': '📅'},  # Subtle Gray
        
        # Work / Personal
        'Work': {'color': (37, 99, 235), 'emoji': '💼'},  # Blue
        'Personal': {'color': (236, 72, 153), 'emoji': '🏠'},  # Pink
        'Projects': {'color': (99, 102, 241), 'emoji': '📁'},  # Indigo
        'Temp': {'color': (156, 163, 175), 'emoji': '🧹'},  # Gray
        'Misc': {'color': (156, 163, 175), 'emoji': '📂'},  # Gray
        
        # Screens / Media capture
        'Screenshots': {'color': (59, 130, 246), 'emoji': '📸'},  # Blue
        'Recordings': {'color': (239, 68, 68), 'emoji': '⏺️'},  # Red
        'Clips': {'color': (239, 68, 68), 'emoji': '🎯'},  # Red
        
        # Backups / System
        'Backups': {'color': (156, 163, 175), 'emoji': '🛡️'},  # Gray
        'Drivers': {'color': (20, 184, 166), 'emoji': '🚗'},  # Teal
        'Firmware': {'color': (99, 102, 241), 'emoji': '🔌'},  # Indigo
        'Configs': {'color': (107, 114, 128), 'emoji': '⚙️'},  # Gray
        
        # Downloads / Cleanup
        'Downloads': {'color': (14, 165, 233), 'emoji': '⬇️'},  # Sky Blue
        'Archives_Old': {'color': (146, 64, 14), 'emoji': '🗃️'},  # Brown
        'Duplicates': {'color': (185, 28, 28), 'emoji': '♻️'},  # Dark Red
        
        # Cloud / Sync
        'Cloud': {'color': (59, 130, 246), 'emoji': '☁️'},  # Blue
        'Sync': {'color': (20, 184, 166), 'emoji': '🔄'},  # Teal
    }
    
    # File type-specific icons (for subfolders)
    FILE_TYPE_ICONS = {
        # Documents
        'PDF': {'color': (220, 38, 38), 'emoji': '📕'},  # Red
        'DOCX': {'color': (37, 99, 235), 'emoji': '📘'},  # Blue
        'DOC': {'color': (37, 99, 235), 'emoji': '📘'},  # Blue
        'TXT': {'color': (107, 114, 128), 'emoji': '📝'},  # Gray
        'RTF': {'color': (107, 114, 128), 'emoji': '📝'},  # Gray
        'ODT': {'color': (59, 130, 246), 'emoji': '📄'},  # Light Blue
        'XLSX': {'color': (21, 128, 61), 'emoji': '📊'},  # Green
        'XLS': {'color': (21, 128, 61), 'emoji': '📊'},  # Green
        'CSV': {'color': (5, 150, 105), 'emoji': '📈'},  # Emerald
        'PPTX': {'color': (234, 88, 12), 'emoji': '📽️'},  # Orange
        'PPT': {'color': (234, 88, 12), 'emoji': '📽️'},  # Orange
        
        # Archives
        'ZIP': {'color': (202, 138, 4), 'emoji': '🗜️'},  # Yellow
        'RAR': {'color': (202, 138, 4), 'emoji': '📦'},  # Yellow
        '7Z': {'color': (202, 138, 4), 'emoji': '🗜️'},  # Yellow
        'TAR': {'color': (146, 64, 14), 'emoji': '📦'},  # Brown
        'GZ': {'color': (146, 64, 14), 'emoji': '🗜️'},  # Brown
        
        # Images
        'JPG': {'color': (34, 197, 94), 'emoji': '🖼️'},  # Green
        'JPEG': {'color': (34, 197, 94), 'emoji': '🖼️'},  # Green
        'PNG': {'color': (59, 130, 246), 'emoji': '🖼️'},  # Blue
        'GIF': {'color': (236, 72, 153), 'emoji': '🎞️'},  # Pink
        'SVG': {'color': (249, 115, 22), 'emoji': '🎨'},  # Orange
        'BMP': {'color': (107, 114, 128), 'emoji': '🖼️'},  # Gray
        'WEBP': {'color': (59, 130, 246), 'emoji': '🖼️'},  # Blue
        
        # Video
        'MP4': {'color': (220, 38, 38), 'emoji': '🎬'},  # Red
        'AVI': {'color': (220, 38, 38), 'emoji': '🎬'},  # Red
        'MKV': {'color': (185, 28, 28), 'emoji': '🎬'},  # Dark Red
        'MOV': {'color': (239, 68, 68), 'emoji': '🎥'},  # Red
        'WMV': {'color': (220, 38, 38), 'emoji': '🎬'},  # Red
        
        # Audio
        'MP3': {'color': (249, 115, 22), 'emoji': '🎵'},  # Orange
        'WAV': {'color': (249, 115, 22), 'emoji': '🎵'},  # Orange
        'FLAC': {'color': (234, 88, 12), 'emoji': '🎶'},  # Dark Orange
        'AAC': {'color': (249, 115, 22), 'emoji': '🎵'},  # Orange
        'M4A': {'color': (249, 115, 22), 'emoji': '🎵'},  # Orange
        
        # Code
        'PY': {'color': (59, 130, 246), 'emoji': '🐍'},  # Blue (Python)
        'JS': {'color': (234, 179, 8), 'emoji': '📜'},  # Yellow (JavaScript)
        'HTML': {'color': (234, 88, 12), 'emoji': '🌐'},  # Orange
        'CSS': {'color': (59, 130, 246), 'emoji': '🎨'},  # Blue
        'JAVA': {'color': (220, 38, 38), 'emoji': '☕'},  # Red
        'CPP': {'color': (99, 102, 241), 'emoji': '⚙️'},  # Indigo
        'C': {'color': (107, 114, 128), 'emoji': '⚙️'},  # Gray
        
        # Executables
        'EXE': {'color': (20, 184, 166), 'emoji': '⚙️'},  # Teal
        'MSI': {'color': (20, 184, 166), 'emoji': '📀'},  # Teal
        'DMG': {'color': (99, 102, 241), 'emoji': '💿'},  # Indigo
        'APK': {'color': (34, 197, 94), 'emoji': '📱'},  # Green
        
        # Other
        'TORRENT': {'color': (34, 197, 94), 'emoji': '🌊'},  # Green
        'ISO': {'color': (99, 102, 241), 'emoji': '💿'},  # Indigo
        'URL': {'color': (59, 130, 246), 'emoji': '🔗'},  # Blue
        
        # Office / Business
        'XLSM': {'color': (21, 128, 61), 'emoji': '📊'},  # Green
        'PPTM': {'color': (234, 88, 12), 'emoji': '📽️'},  # Orange
        'ONE': {'color': (139, 92, 246), 'emoji': '📓'},  # Purple (OneNote)
        'EML': {'color': (59, 130, 246), 'emoji': '✉️'},  # Blue (Email)
        'MSG': {'color': (59, 130, 246), 'emoji': '✉️'},  # Blue (Outlook)
        'VCF': {'color': (20, 184, 166), 'emoji': '👤'},  # Teal (vCard)
        
        # Dev / Config / Logs
        'JSON': {'color': (234, 179, 8), 'emoji': '🧩'},  # Yellow
        'YAML': {'color': (234, 179, 8), 'emoji': '🧩'},  # Yellow
        'YML': {'color': (234, 179, 8), 'emoji': '🧩'},  # Yellow
        'XML': {'color': (99, 102, 241), 'emoji': '🧾'},  # Indigo
        'INI': {'color': (107, 114, 128), 'emoji': '⚙️'},  # Gray
        'CFG': {'color': (107, 114, 128), 'emoji': '⚙️'},  # Gray
        'LOG': {'color': (107, 114, 128), 'emoji': '📜'},  # Gray
        'ENV': {'color': (20, 184, 166), 'emoji': '🌱'},  # Teal
        
        # RAW Photos
        'CR2': {'color': (34, 197, 94), 'emoji': '📷'},  # Green (Canon)
        'NEF': {'color': (34, 197, 94), 'emoji': '📷'},  # Green (Nikon)
        'ARW': {'color': (34, 197, 94), 'emoji': '📷'},  # Green (Sony)
        'DNG': {'color': (34, 197, 94), 'emoji': '📷'},  # Green (Adobe)
        'HEIC': {'color': (59, 130, 246), 'emoji': '📱'},  # Blue (iPhone)
        
        # Media Production
        'SRT': {'color': (107, 114, 128), 'emoji': '💬'},  # Gray (Subtitles)
        'VTT': {'color': (107, 114, 128), 'emoji': '💬'},  # Gray (Subtitles)
        'PRPROJ': {'color': (185, 28, 28), 'emoji': '🎞️'},  # Dark Red (Premiere)
        'VEG': {'color': (239, 68, 68), 'emoji': '🎬'},  # Red (Vegas)
        'MID': {'color': (249, 115, 22), 'emoji': '🎹'},  # Orange (MIDI)
        'MIDI': {'color': (249, 115, 22), 'emoji': '🎹'},  # Orange
        
        # Design / 3D
        'PSD': {'color': (37, 99, 235), 'emoji': '🎨'},  # Blue (Photoshop)
        'AI': {'color': (234, 88, 12), 'emoji': '✒️'},  # Orange (Illustrator)
        'FIG': {'color': (139, 92, 246), 'emoji': '🖼️'},  # Purple (Figma)
        'BLEND': {'color': (249, 115, 22), 'emoji': '🧊'},  # Orange (Blender)
        'FBX': {'color': (99, 102, 241), 'emoji': '🧊'},  # Indigo (3D Model)
        'OBJ': {'color': (99, 102, 241), 'emoji': '🧊'},  # Indigo (3D Model)
        'STL': {'color': (14, 165, 233), 'emoji': '🖨️'},  # Sky Blue (3D Print)
        
        # Database / Data / AI
        'DB': {'color': (14, 165, 233), 'emoji': '🗄️'},  # Sky Blue
        'SQLITE': {'color': (14, 165, 233), 'emoji': '🗄️'},  # Sky Blue
        'IPYNB': {'color': (249, 115, 22), 'emoji': '📓'},  # Orange (Jupyter)
        'PKL': {'color': (99, 102, 241), 'emoji': '🧠'},  # Indigo (Pickle)
        'PARQUET': {'color': (5, 150, 105), 'emoji': '📊'},  # Emerald
        
        # Backup / System / VM
        'BAK': {'color': (156, 163, 175), 'emoji': '🛡️'},  # Gray (Backup)
        'OLD': {'color': (156, 163, 175), 'emoji': '🕰️'},  # Gray (Old)
        'LNK': {'color': (59, 130, 246), 'emoji': '🔗'},  # Blue (Shortcut)
        'DLL': {'color': (107, 114, 128), 'emoji': '🧩'},  # Gray (Library)
        'REG': {'color': (239, 68, 68), 'emoji': '🧬'},  # Red (Registry)
        'VHD': {'color': (99, 102, 241), 'emoji': '🖥️'},  # Indigo (Virtual Disk)
        'VHDX': {'color': (99, 102, 241), 'emoji': '🖥️'},  # Indigo (Virtual Disk)
        'QCOW2': {'color': (99, 102, 241), 'emoji': '🖥️'},  # Indigo (QEMU)
        'OVA': {'color': (99, 102, 241), 'emoji': '📦'},  # Indigo (VM Package)
    }
    
    def __init__(self, icon_folder: Path = None):
        """
        Initialize the folder icon customizer.
        
        Args:
            icon_folder: Where to store .ico files (default: resources/folder_icons/)
        """
        if icon_folder is None:
            if getattr(sys, 'frozen', False):
                base_dir = Path(getattr(sys, '_MEIPASS', Path(sys.executable).resolve().parent))
                icon_folder = base_dir / 'resources' / 'folder_icons'
            else:
                icon_folder = Path(__file__).parent.parent.parent / 'resources' / 'folder_icons'
        
        self.icon_folder = icon_folder
        # Do not create icon folder at init to avoid empty folders.
        # The folder will be created lazily when an icon is actually generated.
        logger.info(f"Folder icon customizer initialized (icon folder: {self.icon_folder})")
    
    def create_folder_icon(self, category: str) -> Optional[Path]:
        """
        Create a .ico file for the given category or file type.
        
        Args:
            category: Category name (Documents, Images, etc.) or file type (PDF, ZIP, etc.)
        
        Returns:
            Path to created .ico file or None if failed
        """
        try:
            # Check category icons first, then file type icons
            if category in self.CATEGORY_ICONS:
                icon_data = self.CATEGORY_ICONS[category]
            elif category in self.FILE_TYPE_ICONS:
                icon_data = self.FILE_TYPE_ICONS[category]
            else:
                logger.warning(f"Unknown category/type: {category}")
                return None
            
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
            
            # Ensure icon folder exists (lazy-create)
            try:
                self.icon_folder.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

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
            try:
                # Try to remove existing desktop.ini if it exists (might be read-only)
                if desktop_ini.exists():
                    try:
                        ctypes.windll.kernel32.SetFileAttributesW(str(desktop_ini), 0x80)  # Normal
                        desktop_ini.unlink()
                    except:
                        pass  # If we can't delete, we'll try to overwrite
                
                with open(desktop_ini, 'w', encoding='utf-8') as f:
                    f.write(ini_content)
            except PermissionError:
                logger.warning(f"Skipping {folder_path.name}: OneDrive sync or permissions prevent icon customization")
                return False
            except Exception as e:
                logger.error(f"Failed to write desktop.ini: {e}")
                return False
            
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
    
    def customize_organized_folders(self, base_folder: Path, category_folders: dict = None) -> int:
        """
        Set custom icons for all organized category folders.
        
        Args:
            base_folder: Root folder containing organized folders
            category_folders: Dict mapping category names to folder paths (optional)
        
        Returns:
            Number of folders successfully customized
        """
        count = 0
        
        # If no specific folders provided, scan all folders in base directory
        if not category_folders:
            category_folders = {}
        
        # Scan base folder for all category folders (Archives, Documents, Images, etc.)
        if base_folder.exists() and base_folder.is_dir():
            for folder in base_folder.iterdir():
                if folder.is_dir():
                    folder_name = folder.name
                    # Check if it's a known category
                    if folder_name in self.CATEGORY_ICONS:
                        if folder_name not in category_folders:
                            category_folders[folder_name] = folder
        
        for category, folder_path in category_folders.items():
            if folder_path.exists() and folder_path.is_dir():
                # Set category icon for main folder
                if self.set_folder_icon(folder_path, category):
                    count += 1
                
                # Recursively process ALL subfolders at any depth
                import os
                for root, dirs, files in os.walk(folder_path):
                    root_path = Path(root)
                    
                    # Skip the category folder itself (already processed)
                    if root_path == folder_path:
                        # Process only immediate subfolders for file type icons
                        for subfolder in folder_path.iterdir():
                            if subfolder.is_dir():
                                folder_name = subfolder.name.upper()
                                logger.debug(f"🔍 Processing 1st level subfolder: {subfolder.name} (uppercase: {folder_name})")
                                
                                # Check if it's a date folder
                                if self._is_date_folder(folder_name):
                                    logger.debug(f"  📅 Identified as date folder: {folder_name}")
                                    if self.set_folder_icon(subfolder, 'DATE_FOLDER'):
                                        count += 1
                                        logger.debug(f"  ✅ Date icon applied")
                                    continue
                                
                                # Try to match with file type icons
                                icon_type = None
                                logger.debug(f"  🔎 Checking file type match for: {folder_name}")
                                
                                # PRIORITY 1: Exact match (case-insensitive)
                                if folder_name in self.FILE_TYPE_ICONS:
                                    icon_type = folder_name
                                    logger.debug(f"  ✅ EXACT MATCH found: {icon_type}")
                                else:
                                    # PRIORITY 2: Substring match (but prefer longer matches)
                                    # Sort by length DESC to match longer strings first (e.g., "DOCX" before "DOC")
                                    matches = []
                                    for file_type in sorted(self.FILE_TYPE_ICONS.keys(), key=len, reverse=True):
                                        if file_type in folder_name:
                                            matches.append(file_type)
                                    
                                    # Use the longest match (most specific)
                                    if matches:
                                        icon_type = matches[0]
                                        logger.debug(f"  ✅ SUBSTRING MATCH found: {icon_type} (from {len(matches)} candidates)")
                                
                                # Use type-specific icon if found, otherwise use category icon
                                if icon_type:
                                    logger.debug(f"  🎨 Applying type-specific icon: {icon_type} to {subfolder.name}")
                                    if self.set_folder_icon(subfolder, icon_type):
                                        count += 1
                                        logger.debug(f"  ✅ Icon applied successfully")
                                    else:
                                        logger.warning(f"  ❌ Failed to apply icon: {icon_type}")
                                else:
                                    # For AI group folders (not file types), use category icon
                                    logger.debug(f"  🎨 Applying category icon: {category} to {subfolder.name}")
                                    if self.set_folder_icon(subfolder, category):
                                        count += 1
                                        logger.debug(f"  ✅ Category icon applied")
                                    else:
                                        logger.warning(f"  ❌ Failed to apply category icon")
                    else:
                        # For deeper levels, only process date folders
                        for dir_name in dirs:
                            subfolder = root_path / dir_name
                            folder_name = dir_name.upper()
                            
                            # Check if this is a date folder at any depth
                            if self._is_date_folder(folder_name):
                                if self.set_folder_icon(subfolder, 'DATE_FOLDER'):
                                    count += 1
        
        logger.info(f"Customized {count} folder icons")
        return count
    
    def _is_date_folder(self, folder_name: str) -> bool:
        """
        Check if folder name looks like a date folder.
        
        Args:
            folder_name: Folder name (uppercase)
        
        Returns:
            True if it's a date folder (Jan-26, Feb-25, 2025, etc.)
        """
        # Common date patterns
        date_patterns = [
            'JAN-', 'FEB-', 'MAR-', 'APR-', 'MAY-', 'JUN-',
            'JUL-', 'AUG-', 'SEP-', 'OCT-', 'NOV-', 'DEC-'
        ]
        
        # Check for month patterns
        for pattern in date_patterns:
            if pattern in folder_name:
                return True
        
        # Check if it's just a year (2024, 2025, etc.)
        if folder_name.isdigit() and len(folder_name) == 4:
            return True
        
        return False
