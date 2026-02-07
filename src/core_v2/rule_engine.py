"""
AutoFolder AI v2.0 - Rule Engine

Enhanced rule-based file classification with context awareness.
Improves on v1 with better extension matching and context hints.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from .models import FileNode, RuleResult

logger = logging.getLogger(__name__)


@dataclass
class Rule:
    """File classification rule."""
    extensions: Set[str]       # File extensions (lowercase with dot)
    category: str              # Main category
    subcategory: str           # Subcategory
    confidence: float = 0.9    # Rule confidence (0-1)
    context_hint: str = ""     # Hint for placement (e.g., "Source code", "Media files")


# Enhanced rule definitions (improved from v1)
RULES = [
    # Documents
    Rule({".pdf"}, "Documents", "PDF", 0.95, "PDF documents"),
    Rule({".doc", ".docx"}, "Documents", "Word", 0.95, "Word documents"),
    Rule({".xls", ".xlsx"}, "Documents", "Excel", 0.95, "Excel spreadsheets"),
    Rule({".ppt", ".pptx"}, "Documents", "PowerPoint", 0.95, "Presentations"),
    Rule({".txt", ".rtf"}, "Documents", "Text", 0.9, "Text files"),
    Rule({".odt", ".ods", ".odp"}, "Documents", "OpenOffice", 0.9, "OpenOffice documents"),
    Rule({".csv", ".tsv"}, "Documents", "Data", 0.85, "Tabular data"),
    Rule({".md", ".markdown"}, "Documents", "Markdown", 0.9, "Markdown documents"),
    Rule({".log"}, "Documents", "Logs", 0.8, "Log files"),
    Rule({".ini", ".conf", ".cfg"}, "Documents", "Config", 0.85, "Configuration files"),
    Rule({".json", ".yaml", ".yml", ".toml"}, "Documents", "Data", 0.85, "Structured data"),
    Rule({".xml"}, "Documents", "Data", 0.8, "XML data"),
    Rule({".srt", ".ass", ".vtt"}, "Documents", "Subtitles", 0.9, "Subtitle files"),
    Rule({".ics"}, "Documents", "Calendar", 0.9, "Calendar events"),
    
    # Images
    Rule({".jpg", ".jpeg"}, "Images", "JPEG", 0.95, "JPEG images"),
    Rule({".png"}, "Images", "PNG", 0.95, "PNG images"),
    Rule({".gif"}, "Images", "GIF", 0.95, "GIF animations"),
    Rule({".bmp"}, "Images", "Bitmap", 0.9, "Bitmap images"),
    Rule({".svg"}, "Images", "Vector", 0.9, "Vector graphics"),
    Rule({".webp"}, "Images", "WebP", 0.9, "WebP images"),
    Rule({".ico"}, "Images", "Icons", 0.9, "Icon files"),
    Rule({".psd"}, "Images", "Photoshop", 0.9, "Photoshop files"),
    Rule({".ai"}, "Images", "Illustrator", 0.9, "Illustrator files"),
    Rule({".raw", ".cr2", ".nef", ".orf"}, "Images", "RAW", 0.95, "RAW camera images"),
    Rule({".heic", ".heif"}, "Images", "HEIC", 0.95, "HEIC images"),
    
    # Videos
    Rule({".mp4", ".m4v"}, "Videos", "MP4", 0.95, "MP4 videos"),
    Rule({".mkv"}, "Videos", "MKV", 0.95, "MKV videos"),
    Rule({".avi"}, "Videos", "AVI", 0.9, "AVI videos"),
    Rule({".mov"}, "Videos", "MOV", 0.9, "QuickTime videos"),
    Rule({".wmv"}, "Videos", "WMV", 0.9, "Windows Media videos"),
    Rule({".flv"}, "Videos", "Flash", 0.85, "Flash videos"),
    Rule({".webm"}, "Videos", "WebM", 0.9, "WebM videos"),
    Rule({".mpeg", ".mpg"}, "Videos", "MPEG", 0.9, "MPEG videos"),
    Rule({".3gp"}, "Videos", "Mobile", 0.8, "Mobile videos"),
    
    # Audio
    Rule({".mp3"}, "Audio", "MP3", 0.95, "MP3 audio"),
    Rule({".wav"}, "Audio", "WAV", 0.95, "WAV audio"),
    Rule({".flac"}, "Audio", "FLAC", 0.95, "Lossless audio"),
    Rule({".m4a", ".aac"}, "Audio", "AAC", 0.9, "AAC audio"),
    Rule({".ogg", ".oga"}, "Audio", "Ogg", 0.9, "Ogg audio"),
    Rule({".wma"}, "Audio", "WMA", 0.9, "Windows Media audio"),
    Rule({".opus"}, "Audio", "Opus", 0.9, "Opus audio"),
    
    # Archives
    Rule({".zip"}, "Archives", "ZIP", 0.95, "ZIP archives"),
    Rule({".rar"}, "Archives", "RAR", 0.95, "RAR archives"),
    Rule({".7z"}, "Archives", "7-Zip", 0.95, "7-Zip archives"),
    Rule({".tar", ".tar.gz", ".tgz"}, "Archives", "Tar", 0.9, "Tar archives"),
    Rule({".gz", ".bz2", ".xz"}, "Archives", "Compressed", 0.85, "Compressed files"),
    Rule({".iso"}, "Archives", "Disk Images", 0.9, "Disk images"),
    Rule({".dmg"}, "Archives", "Disk Images", 0.9, "Mac disk images"),
    
    # Code - Programming Languages
    Rule({".py"}, "Code", "Python", 0.95, "Python scripts"),
    Rule({".js", ".mjs", ".cjs"}, "Code", "JavaScript", 0.95, "JavaScript code"),
    Rule({".ts", ".tsx"}, "Code", "TypeScript", 0.95, "TypeScript code"),
    Rule({".jsx"}, "Code", "React", 0.95, "React components"),
    Rule({".java"}, "Code", "Java", 0.95, "Java source"),
    Rule({".c", ".h"}, "Code", "C", 0.95, "C source"),
    Rule({".cpp", ".cc", ".cxx", ".hpp"}, "Code", "C++", 0.95, "C++ source"),
    Rule({".cs"}, "Code", "CSharp", 0.95, "C# source"),
    Rule({".go"}, "Code", "Go", 0.95, "Go source"),
    Rule({".rs"}, "Code", "Rust", 0.95, "Rust source"),
    Rule({".rb"}, "Code", "Ruby", 0.95, "Ruby scripts"),
    Rule({".php"}, "Code", "PHP", 0.95, "PHP scripts"),
    Rule({".swift"}, "Code", "Swift", 0.95, "Swift source"),
    Rule({".kt", ".kts"}, "Code", "Kotlin", 0.95, "Kotlin source"),
    Rule({".dart"}, "Code", "Dart", 0.95, "Dart source"),
    Rule({".lua"}, "Code", "Lua", 0.9, "Lua scripts"),
    Rule({".r", ".rmd"}, "Code", "R", 0.95, "R scripts"),
    Rule({".m"}, "Code", "MATLAB", 0.85, "MATLAB code"),
    Rule({".scala"}, "Code", "Scala", 0.95, "Scala source"),
    Rule({".pl", ".pm"}, "Code", "Perl", 0.9, "Perl scripts"),
    
    # Code - Shell & Scripts
    Rule({".sh", ".bash", ".zsh"}, "Code", "Shell", 0.95, "Shell scripts"),
    Rule({".ps1", ".psm1"}, "Code", "PowerShell", 0.95, "PowerShell scripts"),
    Rule({".bat", ".cmd"}, "Code", "Batch", 0.95, "Batch scripts"),
    
    # Code - Web
    Rule({".html", ".htm"}, "Code", "HTML", 0.95, "HTML files"),
    Rule({".css", ".scss", ".sass", ".less"}, "Code", "CSS", 0.95, "Stylesheets"),
    Rule({".vue"}, "Code", "Vue", 0.95, "Vue components"),
    Rule({".sql"}, "Code", "SQL", 0.95, "SQL scripts"),
    
    # Installers
    Rule({".exe"}, "Installers", "Windows", 0.9, "Windows executables"),
    Rule({".msi"}, "Installers", "Windows", 0.95, "Windows installers"),
    Rule({".dmg"}, "Installers", "Mac", 0.95, "Mac installers"),
    Rule({".deb"}, "Installers", "Debian", 0.95, "Debian packages"),
    Rule({".rpm"}, "Installers", "RedHat", 0.95, "RPM packages"),
    Rule({".appimage"}, "Installers", "Linux", 0.95, "AppImage packages"),
    Rule({".apk"}, "Installers", "Android", 0.95, "Android packages"),
    
    # Fonts
    Rule({".ttf", ".otf"}, "Fonts", "TrueType", 0.95, "Font files"),
    Rule({".woff", ".woff2"}, "Fonts", "Web", 0.95, "Web fonts"),
    
    # eBooks
    Rule({".epub"}, "eBooks", "EPUB", 0.95, "EPUB books"),
    Rule({".mobi", ".azw", ".azw3"}, "eBooks", "Kindle", 0.95, "Kindle books"),
    
    # 3D Models
    Rule({".obj", ".fbx", ".stl", ".blend", ".3ds"}, "3D Models", "Models", 0.9, "3D model files"),
    
    # Databases
    Rule({".db", ".sqlite", ".sqlite3"}, "Databases", "SQLite", 0.9, "SQLite databases"),
    Rule({".mdb", ".accdb"}, "Databases", "Access", 0.9, "Access databases"),
    
    # Backups
    Rule({".bak", ".backup", ".old"}, "Backups", "Backup", 0.85, "Backup files"),
    
    # Shortcuts
    Rule({".lnk"}, "Shortcuts", "Windows", 0.9, "Windows shortcuts"),
    Rule({".url"}, "Shortcuts", "Web", 0.9, "URL shortcuts"),
    
    # Torrents
    Rule({".torrent"}, "Torrents", "BitTorrent", 0.95, "Torrent files"),
]


class RuleEngine:
    """
    Enhanced rule-based file classifier.
    
    Matches files by extension with confidence scoring and context hints.
    """
    
    def __init__(self):
        """Initialize rule engine."""
        # Build extension lookup for fast matching
        self._extension_map: Dict[str, Rule] = {}
        for rule in RULES:
            for ext in rule.extensions:
                if ext not in self._extension_map:
                    self._extension_map[ext] = rule
                else:
                    # Keep higher confidence rule
                    existing = self._extension_map[ext]
                    if rule.confidence > existing.confidence:
                        self._extension_map[ext] = rule
        
        logger.info(f"Rule engine initialized with {len(RULES)} rules covering {len(self._extension_map)} extensions")
    
    def classify(self, file_node: FileNode) -> Optional[RuleResult]:
        """
        Classify a file using rules.
        
        Args:
            file_node: File to classify
            
        Returns:
            RuleResult if matched, None otherwise
        """
        if file_node.is_dir:
            return None
        
        ext = file_node.extension
        if not ext:
            return None
        
        # Look up rule
        rule = self._extension_map.get(ext)
        if not rule:
            return None
        
        return RuleResult(
            file=file_node.path,
            category=rule.category,
            subcategory=rule.subcategory,
            confidence=rule.confidence,
            matched_rule=ext,
            context_hint=rule.context_hint
        )
    
    def classify_batch(self, file_nodes: List[FileNode]) -> List[RuleResult]:
        """
        Classify multiple files.
        
        Args:
            file_nodes: List of files to classify
            
        Returns:
            List of RuleResults (only matched files)
        """
        results = []
        for node in file_nodes:
            result = self.classify(node)
            if result:
                results.append(result)
        return results
    
    def get_categories(self) -> Set[str]:
        """Get all available categories."""
        return {rule.category for rule in RULES}
    
    def get_subcategories(self, category: str) -> Set[str]:
        """Get subcategories for a category."""
        return {
            rule.subcategory
            for rule in RULES
            if rule.category == category
        }
    
    def get_extensions_for_category(self, category: str) -> Set[str]:
        """Get all extensions for a category."""
        extensions = set()
        for rule in RULES:
            if rule.category == category:
                extensions.update(rule.extensions)
        return extensions


def classify_file(file_node: FileNode) -> Optional[RuleResult]:
    """
    Convenience function to classify a single file.
    
    Args:
        file_node: File to classify
        
    Returns:
        RuleResult if matched, None otherwise
    """
    engine = RuleEngine()
    return engine.classify(file_node)
