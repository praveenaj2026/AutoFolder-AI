"""
Smart File Renaming Module
Generates meaningful file names using AI and metadata.
"""

import re
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import logging

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
        Generate smart filename suggestion.
        
        Args:
            file_path: Original file path
            ai_group: AI semantic group name
            category: File category (Documents, Images, etc.)
            file_metadata: Optional metadata dict with 'date', 'size', etc.
            
        Returns:
            Suggested filename with extension
        """
        if not self.enabled:
            return file_path.name
        
        try:
            # Extract components
            original_name = file_path.stem
            extension = file_path.suffix
            
            # Clean the original name
            cleaned_name = self._clean_filename(original_name)
            
            # Extract date from metadata or file
            date_str = self._extract_date(file_path, file_metadata)
            
            # Build new name based on format
            name_format = self.rename_config.get('name_format', '{ai_group}_{date}_{original}')
            
            parts = []
            
            # Add AI group if enabled and available
            if self.rename_config.get('include_ai_group', True) and ai_group:
                # Clean AI group name (remove special chars)
                clean_group = re.sub(r'[^\w\s-]', '', ai_group)
                clean_group = re.sub(r'\s+', '_', clean_group.strip())
                parts.append(clean_group)
            
            # Add date if enabled and available
            if self.rename_config.get('include_date', True) and date_str:
                parts.append(date_str)
            
            # Add cleaned original name if it has meaningful content
            if cleaned_name and len(cleaned_name) > 2:
                # Limit length
                max_length = self.rename_config.get('max_original_length', 30)
                if len(cleaned_name) > max_length:
                    cleaned_name = cleaned_name[:max_length]
                parts.append(cleaned_name)
            elif not parts:
                # If no other parts, keep original
                parts.append(original_name[:40])
            
            # Join parts
            if name_format == '{ai_group}_{date}_{original}':
                new_name = '_'.join(parts)
            elif name_format == '{ai_group}_{original}_{date}':
                if len(parts) >= 3:
                    new_name = f"{parts[0]}_{parts[2]}_{parts[1]}"
                else:
                    new_name = '_'.join(parts)
            elif name_format == '{date}_{ai_group}_{original}':
                if len(parts) >= 2:
                    new_name = f"{parts[1]}_{parts[0]}_{parts[2] if len(parts) > 2 else ''}"
                else:
                    new_name = '_'.join(parts)
            else:
                new_name = '_'.join(parts)
            
            # Remove double underscores and trim
            new_name = re.sub(r'_+', '_', new_name)
            new_name = new_name.strip('_')
            
            # Ensure valid filename
            new_name = self._sanitize_filename(new_name)
            
            return f"{new_name}{extension}"
            
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
                timestamp = file_path.stat().st_mtime
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
