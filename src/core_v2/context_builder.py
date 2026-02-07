"""
AutoFolder AI v2.0 - Context Builder

Analyzes folder context to inform better placement decisions.
Prevents redundant nesting like "Documents/Text/TXT/" or "Audio/MP3/MP3/".
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import Counter

from .models import FileNode, RuleResult

logger = logging.getLogger(__name__)


class FolderContext:
    """
    Context information about a folder.
    
    Helps prevent redundant nesting by understanding what's already there.
    """
    
    def __init__(self, path: Path):
        """
        Initialize folder context.
        
        Args:
            path: Folder path to analyze
        """
        self.path = path
        self.name = path.name
        self.name_lower = path.name.lower()
        
        # Context extracted from folder name
        self.implies_category: Optional[str] = None
        self.implies_subcategory: Optional[str] = None
        self.implies_extension: Optional[str] = None
        
        # Statistics
        self.file_count = 0
        self.extension_counts: Dict[str, int] = {}
        self.dominant_extension: Optional[str] = None
    
    def __repr__(self):
        """String representation."""
        parts = [f"FolderContext({self.path})"]
        if self.implies_category:
            parts.append(f"category={self.implies_category}")
        if self.implies_subcategory:
            parts.append(f"subcategory={self.implies_subcategory}")
        if self.dominant_extension:
            parts.append(f"dominant={self.dominant_extension}")
        return f"<{' '.join(parts)}>"


class ContextBuilder:
    """
    Builds context information for folders.
    
    Analyzes folder names and contents to prevent redundant nesting.
    """
    
    def __init__(self):
        """Initialize context builder."""
        # Folder name → Category mapping
        self._category_hints = {
            "documents": "Documents",
            "docs": "Documents",
            "images": "Images",
            "pictures": "Images",
            "photos": "Images",
            "pics": "Images",
            "videos": "Videos",
            "movies": "Videos",
            "audio": "Audio",
            "music": "Audio",
            "songs": "Audio",
            "archives": "Archives",
            "compressed": "Archives",
            "code": "Code",
            "src": "Code",
            "source": "Code",
            "installers": "Installers",
            "setup": "Installers",
            "fonts": "Fonts",
            "ebooks": "eBooks",
            "books": "eBooks",
            "3d": "3D Models",
            "models": "3D Models",
            "databases": "Databases",
            "db": "Databases",
            "backups": "Backups",
            "backup": "Backups",
            "shortcuts": "Shortcuts",
            "torrents": "Torrents",
        }
        
        # Folder name → Subcategory mapping
        self._subcategory_hints = {
            "pdf": "PDF",
            "word": "Word",
            "excel": "Excel",
            "powerpoint": "PowerPoint",
            "text": "Text",
            "txt": "Text",
            "markdown": "Markdown",
            "logs": "Logs",
            "config": "Config",
            "jpeg": "JPEG",
            "jpg": "JPEG",
            "png": "PNG",
            "gif": "GIF",
            "svg": "Vector",
            "mp4": "MP4",
            "mkv": "MKV",
            "avi": "AVI",
            "mp3": "MP3",
            "wav": "WAV",
            "flac": "FLAC",
            "zip": "ZIP",
            "rar": "RAR",
            "python": "Python",
            "py": "Python",
            "javascript": "JavaScript",
            "js": "JavaScript",
            "typescript": "TypeScript",
            "ts": "TypeScript",
            "java": "Java",
            "cpp": "C++",
            "c++": "C++",
            "csharp": "CSharp",
            "c#": "CSharp",
            "go": "Go",
            "rust": "Rust",
            "html": "HTML",
            "css": "CSS",
            "shell": "Shell",
            "bash": "Shell",
            "powershell": "PowerShell",
        }
        
        # Extension → likely already in subcategory folder
        self._extension_subcategory_map = {
            ".pdf": "PDF",
            ".doc": "Word",
            ".docx": "Word",
            ".xls": "Excel",
            ".xlsx": "Excel",
            ".ppt": "PowerPoint",
            ".pptx": "PowerPoint",
            ".txt": "Text",
            ".jpg": "JPEG",
            ".jpeg": "JPEG",
            ".png": "PNG",
            ".gif": "GIF",
            ".mp4": "MP4",
            ".mkv": "MKV",
            ".mp3": "MP3",
            ".wav": "WAV",
            ".zip": "ZIP",
            ".rar": "RAR",
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
        }
    
    def build_context(self, folder_node: FileNode) -> FolderContext:
        """
        Build context for a folder.
        
        Args:
            folder_node: Folder to analyze
            
        Returns:
            FolderContext with inferred information
        """
        context = FolderContext(folder_node.path)
        
        # Analyze folder name for hints
        self._analyze_folder_name(context)
        
        # Analyze contents if available
        if folder_node.children:
            self._analyze_contents(context, folder_node)
        
        return context
    
    def _analyze_folder_name(self, context: FolderContext):
        """Extract hints from folder name."""
        name_lower = context.name_lower
        
        # Check for category hints
        for keyword, category in self._category_hints.items():
            if keyword in name_lower:
                context.implies_category = category
                break
        
        # Check for subcategory hints
        for keyword, subcategory in self._subcategory_hints.items():
            if keyword in name_lower:
                context.implies_subcategory = subcategory
                # Also try to infer category from subcategory
                if not context.implies_category:
                    context.implies_category = self._infer_category_from_subcategory(subcategory)
                break
        
        # Check if folder name is an extension (e.g., "MP3", "PDF")
        if name_lower.startswith("."):
            context.implies_extension = name_lower
        else:
            # Check for extension without dot
            potential_ext = f".{name_lower}"
            if potential_ext in self._extension_subcategory_map:
                context.implies_extension = potential_ext
                if not context.implies_subcategory:
                    context.implies_subcategory = self._extension_subcategory_map[potential_ext]
    
    def _analyze_contents(self, context: FolderContext, folder_node: FileNode):
        """Analyze folder contents for context."""
        # Count files and extensions
        for child in folder_node.children:
            if child.is_file:
                context.file_count += 1
                ext = child.extension
                if ext:
                    context.extension_counts[ext] = context.extension_counts.get(ext, 0) + 1
        
        # Find dominant extension (if >50% of files)
        if context.extension_counts:
            total = context.file_count
            for ext, count in context.extension_counts.items():
                if count / total > 0.5:
                    context.dominant_extension = ext
                    break
    
    def _infer_category_from_subcategory(self, subcategory: str) -> Optional[str]:
        """Try to infer category from subcategory."""
        # Common mappings
        doc_subcats = {"PDF", "Word", "Excel", "PowerPoint", "Text", "Markdown", "Logs", "Config"}
        image_subcats = {"JPEG", "PNG", "GIF", "Bitmap", "Vector"}
        video_subcats = {"MP4", "MKV", "AVI", "MOV"}
        audio_subcats = {"MP3", "WAV", "FLAC", "AAC"}
        archive_subcats = {"ZIP", "RAR", "7-Zip", "Tar"}
        code_subcats = {"Python", "JavaScript", "TypeScript", "Java", "C++", "CSharp", "Go", "Rust", "HTML", "CSS", "Shell", "PowerShell"}
        
        if subcategory in doc_subcats:
            return "Documents"
        elif subcategory in image_subcats:
            return "Images"
        elif subcategory in video_subcats:
            return "Videos"
        elif subcategory in audio_subcats:
            return "Audio"
        elif subcategory in archive_subcats:
            return "Archives"
        elif subcategory in code_subcats:
            return "Code"
        
        return None
    
    def would_create_redundancy(
        self,
        parent_context: FolderContext,
        rule_result: RuleResult
    ) -> bool:
        """
        Check if placing file in parent would create redundant nesting.
        
        Examples of redundancy:
        - File: song.mp3, Parent: "MP3" folder → redundant
        - File: report.pdf, Parent: "PDF" folder → redundant
        - File: script.py, Parent: "Python" folder → redundant
        
        Args:
            parent_context: Context of parent folder
            rule_result: Classification of file
            
        Returns:
            True if would create redundancy
        """
        # Check if parent folder name matches the subcategory
        if parent_context.implies_subcategory == rule_result.subcategory:
            logger.debug(
                f"Redundancy detected: folder '{parent_context.name}' already implies "
                f"subcategory '{rule_result.subcategory}'"
            )
            return True
        
        # Check if parent folder name matches the file extension
        if parent_context.implies_extension:
            file_ext = rule_result.file.path.suffix.lower()
            if parent_context.implies_extension == file_ext:
                logger.debug(
                    f"Redundancy detected: folder '{parent_context.name}' already implies "
                    f"extension '{file_ext}'"
                )
                return True
        
        # Check if parent folder is dominated by this extension (>50% of files)
        if parent_context.dominant_extension:
            file_ext = rule_result.file.path.suffix.lower()
            if parent_context.dominant_extension == file_ext:
                logger.debug(
                    f"Redundancy detected: folder '{parent_context.name}' is dominated by "
                    f"'{file_ext}' files"
                )
                return True
        
        return False
    
    def get_context_hint(self, folder_node: FileNode) -> str:
        """
        Get a brief context description for a folder.
        
        Args:
            folder_node: Folder to describe
            
        Returns:
            Human-readable context hint
        """
        context = self.build_context(folder_node)
        
        hints = []
        if context.implies_category:
            hints.append(f"Category: {context.implies_category}")
        if context.implies_subcategory:
            hints.append(f"Type: {context.implies_subcategory}")
        if context.dominant_extension:
            hints.append(f"Mostly {context.dominant_extension} files")
        
        if hints:
            return ", ".join(hints)
        return "No specific context"


# Convenience function
def analyze_folder_context(folder_node: FileNode) -> FolderContext:
    """
    Convenience function to analyze folder context.
    
    Args:
        folder_node: Folder to analyze
        
    Returns:
        FolderContext
    """
    builder = ContextBuilder()
    return builder.build_context(folder_node)
