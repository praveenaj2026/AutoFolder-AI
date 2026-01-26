"""
Smart File Renaming Module
Generates meaningful file names using AI and metadata.
"""

import re
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import logging
from utils.safe_file_ops import safe_stat, safe_get_size, safe_get_mtime, safe_exists

logger = logging.getLogger(__name__)


class SmartRenamer:
    """Generates smart file names based on AI groups and content."""
    
    # Common junk patterns to remove
    JUNK_PATTERNS = [
        r'^IMG_',
        r'^DSC_',
        r'^DCIM_',
        r'^Scan_',
        r'^Screenshot_',
        r'^WhatsApp Image ',
        r'^Copy of ',
        r'^Copy \(\d+\) of ',
        r'\(\d+\)$',  # Remove (1), (2) suffixes
        r'_\d{8}_\d{6}$',  # Remove timestamp patterns like _20240115_143022
        r' - Copy$',
        r'Untitled',
    ]
    
    def __init__(self, config: dict):
        """
        Initialize smart renamer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.rename_config = config.get('smart_rename', {})
        self.enabled = self.rename_config.get('enabled', True)
        
    def suggest_filename(
        self,
        file_path: Path,
        ai_group: Optional[str] = None,
        category: Optional[str] = None,
        file_metadata: Optional[Dict] = None
    ) -> str:
        """
        Generate smart filename suggestion (simplified - just cleans junk patterns).
        
        Args:
            file_path: Original file path
            ai_group: AI semantic group name (not used in simple mode)
            category: File category (not used in simple mode)
            file_metadata: Optional metadata dict (not used in simple mode)
            
        Returns:
            Cleaned filename with extension
        """
        logger.debug(f"suggest_filename called for: {file_path.name}, enabled: {self.enabled}")
        
        if not self.enabled:
            logger.debug(f"Smart rename is disabled, returning original name")
            return file_path.name
        
        try:
            # Extract components
            original_name = file_path.stem
            extension = file_path.suffix
            
            logger.debug(f"Cleaning filename stem: '{original_name}'")
            
            # Clean the original name (remove junk patterns like (1) (2) etc)
            cleaned_name = self._clean_filename(original_name)
            
            logger.debug(f"After cleaning: '{cleaned_name}'")
            
            # If cleaning removed everything, keep original
            if not cleaned_name or len(cleaned_name) < 2:
                logger.debug(f"Cleaning removed too much, keeping original: {file_path.name}")
                return file_path.name
            
            # Ensure valid filename
            cleaned_name = self._sanitize_filename(cleaned_name)
            
            result = f"{cleaned_name}{extension}"
            
            # Log the rename
            if result != file_path.name:
                logger.info(f"Smart rename: '{file_path.name}' → '{result}'")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating filename suggestion: {e}")
            return file_path.name
    
    def _clean_filename(self, name: str) -> str:
        """
        Clean filename by removing junk patterns.
        
        Args:
            name: Original filename (without extension)
            
        Returns:
            Cleaned filename
        """
        cleaned = name
        
        # Apply junk patterns from config
        patterns = self.rename_config.get('remove_patterns', self.JUNK_PATTERNS)
        for pattern in patterns:
            # Special handling for (1) (2) patterns - remove ALL occurrences
            if pattern == r'\(\d+\)$':
                # Keep removing until no more matches
                while re.search(r'\s*\(\d+\)\s*', cleaned):
                    cleaned = re.sub(r'\s*\(\d+\)\s*', ' ', cleaned)
            else:
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove extra spaces and underscores
        cleaned = re.sub(r'[\s_]+', '_', cleaned)
        cleaned = cleaned.strip('_- ')
        
        return cleaned
    
    def _extract_date(
        self, 
        file_path: Path,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Extract date from file metadata or name.
        
        Args:
            file_path: File path
            metadata: Optional metadata dict
            
        Returns:
            Date string in format YYYY-MMM or None
        """
        date_obj = None
        
        # Try metadata first
        if metadata and 'date' in metadata:
            date_obj = metadata['date']
        
        # Try file modification time
        if not date_obj:
            try:
                timestamp = safe_get_mtime(file_path)
                date_obj = datetime.fromtimestamp(timestamp)
            except Exception:
                pass
        
        # Try extracting from filename (YYYYMMDD pattern)
        if not date_obj:
            name = file_path.stem
            # Look for patterns like 20240115, 2024-01-15, 2024_01_15
            date_patterns = [
                r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})',
                r'(\d{8})',
            ]
            for pattern in date_patterns:
                match = re.search(pattern, name)
                if match:
                    try:
                        if len(match.groups()) == 3:
                            year, month, day = match.groups()
                            date_obj = datetime(int(year), int(month), int(day))
                        else:
                            date_str = match.group(1)
                            year = int(date_str[0:4])
                            month = int(date_str[4:6])
                            day = int(date_str[6:8])
                            date_obj = datetime(year, month, day)
                        break
                    except ValueError:
                        continue
        
        if date_obj:
            # Format: Jan2024, Feb2024, etc.
            return date_obj.strftime('%b%Y')
        
        return None
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize filename to be valid on all platforms.
        
        Args:
            name: Filename to sanitize
            
        Returns:
            Valid filename
        """
        # Remove invalid characters for Windows/Linux/Mac
        invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
        sanitized = re.sub(invalid_chars, '', name)
        
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip('. ')
        
        # Ensure not empty
        if not sanitized:
            sanitized = 'file'
        
        # Limit total length (Windows MAX_PATH considerations)
        max_length = self.rename_config.get('max_filename_length', 100)
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    def batch_suggest_filenames(
        self,
        files: List[Dict]
    ) -> List[Dict]:
        """
        Generate rename suggestions for multiple files.
        
        Args:
            files: List of file dicts with 'path', 'ai_group', 'category'
            
        Returns:
            List of dicts with added 'suggested_name' field
        """
        results = []
        
        for file_dict in files:
            file_path = Path(file_dict['path'])
            ai_group = file_dict.get('ai_group')
            category = file_dict.get('category')
            metadata = file_dict.get('metadata', {})
            
            suggested = self.suggest_filename(
                file_path,
                ai_group,
                category,
                metadata
            )
            
            file_dict['suggested_name'] = suggested
            file_dict['needs_rename'] = suggested != file_path.name
            results.append(file_dict)
        
        logger.info(f"Generated {len(results)} filename suggestions")
        return results
    
    def preview_rename(
        self,
        original_name: str,
        suggested_name: str
    ) -> Dict:
        """
        Preview the changes between original and suggested name.
        
        Args:
            original_name: Original filename
            suggested_name: Suggested filename
            
        Returns:
            Dict with comparison details
        """
        original_stem = Path(original_name).stem
        suggested_stem = Path(suggested_name).stem
        
        # Find what changed
        changes = []
        if original_stem != suggested_stem:
            changes.append(f"Name: {original_stem} → {suggested_stem}")
        
        return {
            'original': original_name,
            'suggested': suggested_name,
            'changes': changes,
            'is_different': original_name != suggested_name
        }
