"""
File Analyzer

Analyzes files to extract metadata and determine content type.
"""

import mimetypes
from pathlib import Path
from typing import Dict, Optional
import logging

try:
    import filetype
except ImportError:
    filetype = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None


logger = logging.getLogger(__name__)


class FileAnalyzer:
    """Analyzes files to extract metadata and content information."""
    
    def __init__(self):
        """Initialize file analyzer."""
        mimetypes.init()
        
        # Category mapping
        self.categories = {
            'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.heic'],
            'video': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
            'executable': ['.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm', '.apk', '.bat', '.sh'],
            'code': ['.py', '.js', '.java', '.cpp', '.c', '.cs', '.html', '.css', '.php', '.rb', '.go', '.rs'],
            'data': ['.json', '.xml', '.yaml', '.yml', '.csv', '.sql']
        }
    
    def analyze_file(self, file_path: Path) -> Dict:
        """
        Analyze a file and return metadata.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with file metadata
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = file_path.stat()
        
        info = {
            'name': file_path.name,
            'stem': file_path.stem,
            'extension': file_path.suffix.lower(),
            'size': stat.st_size,
            'size_mb': stat.st_size / (1024 * 1024),
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'category': self.get_category(file_path),
            'mime_type': self.get_mime_type(file_path)
        }
        
        return info
    
    def get_category(self, file_path: Path) -> str:
        """
        Determine file category based on extension.
        
        Args:
            file_path: Path to file
            
        Returns:
            Category name
        """
        ext = file_path.suffix.lower()
        
        for category, extensions in self.categories.items():
            if ext in extensions:
                return category
        
        return 'other'
    
    def get_mime_type(self, file_path: Path) -> Optional[str]:
        """
        Get MIME type of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            MIME type string or None
        """
        # Try with filetype library first (more accurate)
        if filetype:
            try:
                kind = filetype.guess(str(file_path))
                if kind:
                    return kind.mime
            except:
                pass
        
        # Fallback to mimetypes
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type
    
    def extract_text_preview(self, file_path: Path, max_chars: int = 500) -> Optional[str]:
        """
        Extract text preview from file (for AI analysis).
        
        Args:
            file_path: Path to file
            max_chars: Maximum characters to extract
            
        Returns:
            Text preview or None
        """
        ext = file_path.suffix.lower()
        
        # Plain text files
        if ext in ['.txt', '.md', '.log', '.csv', '.json', '.xml', '.html']:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read(max_chars)
            except:
                return None
        
        # PDF files
        if ext == '.pdf' and PyPDF2:
            try:
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    if len(reader.pages) > 0:
                        text = reader.pages[0].extract_text()
                        return text[:max_chars] if text else None
            except:
                return None
        
        return None
    
    def is_likely_screenshot(self, file_path: Path) -> bool:
        """
        Heuristically determine if image is likely a screenshot.
        
        Args:
            file_path: Path to image file
            
        Returns:
            True if likely a screenshot
        """
        name_lower = file_path.name.lower()
        
        screenshot_keywords = [
            'screenshot', 'screen shot', 'screen_shot',
            'capture', 'snap', 'snip', 'screen',
            'scr_', 'ss_'
        ]
        
        for keyword in screenshot_keywords:
            if keyword in name_lower:
                return True
        
        return False
    
    def is_likely_download(self, file_path: Path) -> bool:
        """
        Heuristically determine if file was downloaded.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if likely downloaded
        """
        name_lower = file_path.name.lower()
        
        # Check for download suffixes
        if ' (1)' in file_path.name or ' (2)' in file_path.name:
            return True
        
        # Check for common download patterns
        download_patterns = ['download', 'tmp', 'temp', 'unnamed']
        
        for pattern in download_patterns:
            if pattern in name_lower:
                return True
        
        return False
