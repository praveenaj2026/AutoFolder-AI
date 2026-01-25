"""
Search Engine for Organized Files
Provides search and filter capabilities for organized files.
"""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re
import logging

logger = logging.getLogger(__name__)


class SearchEngine:
    """Search engine for organized files."""
    
    def __init__(self, organized_root: Path):
        """
        Initialize search engine.
        
        Args:
            organized_root: Root directory of organized files
        """
        self.root = organized_root
        self.index: Dict[Path, Dict] = {}
        
    def build_index(self) -> int:
        """
        Build search index of all organized files.
        
        Returns:
            Number of files indexed
        """
        logger.info(f"Building search index for: {self.root}")
        self.index.clear()
        
        if not self.root.exists():
            logger.warning(f"Root directory does not exist: {self.root}")
            return 0
        
        # Index all files recursively
        for file_path in self.root.rglob('*'):
            if file_path.is_file():
                try:
                    stat = file_path.stat()
                    
                    # Extract metadata from path structure (flexible)
                    # Can be: Category/AI_Group/Type/Date/filename OR any other structure
                    parts = file_path.relative_to(self.root).parts
                    
                    # Try to detect AutoFolder organized structure
                    category = parts[0] if len(parts) > 0 else 'Unknown'
                    ai_group = None
                    file_type = None
                    
                    # If path has Documents/Category/AI_Group structure
                    if len(parts) >= 3:
                        category = parts[0]
                        ai_group = parts[1] if parts[1] not in ['Audio', 'Video', 'Images', 'Code', 'Archives', 'Installers', 'Documents'] else None
                        file_type = parts[2] if len(parts) > 2 else None
                    
                    self.index[file_path] = {
                        'name': file_path.name,
                        'stem': file_path.stem,
                        'extension': file_path.suffix.lower(),
                        'size': stat.st_size,
                        'size_mb': stat.st_size / (1024 * 1024),
                        'modified': datetime.fromtimestamp(stat.st_mtime),
                        'category': category,
                        'ai_group': ai_group,
                        'file_type': file_type,
                        'date_folder': parts[3] if len(parts) > 3 else None,
                        'path': file_path,
                        'full_path_text': str(file_path).lower()
                    }
                    
                    logger.debug(f"Indexed: {file_path.name}")
                except Exception as e:
                    logger.error(f"Error indexing {file_path}: {e}")
        
        logger.info(f"Indexed {len(self.index)} files")
        return len(self.index)
    
    def search(
        self,
        query: str = "",
        category: Optional[str] = None,
        ai_group: Optional[str] = None,
        file_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        size_min_mb: Optional[float] = None,
        size_max_mb: Optional[float] = None,
        extension: Optional[str] = None
    ) -> List[Dict]:
        """
        Search files with filters.
        
        Args:
            query: Text search in filename
            category: Filter by category
            ai_group: Filter by AI group
            file_type: Filter by file type
            date_from: Filter by date (from)
            date_to: Filter by date (to)
            size_min_mb: Minimum file size in MB
            size_max_mb: Maximum file size in MB
            extension: Filter by file extension
            
        Returns:
            List of matching file metadata dicts
        """
        if not self.index:
            self.build_index()
        
        results = []
        query_lower = query.lower() if query else ""
        
        for file_path, metadata in self.index.items():
            # Text search in filename, stem, or full path
            if query_lower:
                name_match = query_lower in metadata['name'].lower()
                stem_match = query_lower in metadata['stem'].lower()
                path_match = query_lower in metadata['full_path_text']
                
                if not (name_match or stem_match or path_match):
                    continue
            
            # Category filter
            if category and category != "All" and metadata['category'] != category:
                continue
            
            # AI group filter
            if ai_group and ai_group != "All" and metadata['ai_group'] != ai_group:
                continue
            
            # File type filter
            if file_type and file_type != "All" and metadata['file_type'] != file_type:
                continue
            
            # Extension filter
            if extension and extension != "All" and metadata['extension'] != extension:
                continue
            
            # Date range filter
            if date_from and metadata['modified'] < date_from:
                continue
            if date_to and metadata['modified'] > date_to:
                continue
            
            # Size range filter
            if size_min_mb is not None and metadata['size_mb'] < size_min_mb:
                continue
            if size_max_mb is not None and metadata['size_mb'] > size_max_mb:
                continue
            
            results.append(metadata)
        
        logger.info(f"Search found {len(results)} results")
        return results
    
    def get_categories(self) -> List[str]:
        """Get list of all categories."""
        if not self.index:
            self.build_index()
        return sorted(set(m['category'] for m in self.index.values()))
    
    def get_ai_groups(self) -> List[str]:
        """Get list of all AI groups."""
        if not self.index:
            self.build_index()
        return sorted(set(m['ai_group'] for m in self.index.values() if m['ai_group']))
    
    def get_file_types(self) -> List[str]:
        """Get list of all file types."""
        if not self.index:
            self.build_index()
        return sorted(set(m['file_type'] for m in self.index.values() if m['file_type']))
    
    def get_extensions(self) -> List[str]:
        """Get list of all file extensions."""
        if not self.index:
            self.build_index()
        return sorted(set(m['extension'] for m in self.index.values() if m['extension']))
    
    def get_stats(self) -> Dict:
        """Get search index statistics."""
        if not self.index:
            self.build_index()
        
        total_size = sum(m['size'] for m in self.index.values())
        
        return {
            'total_files': len(self.index),
            'total_size_mb': total_size / (1024 * 1024),
            'total_size_gb': total_size / (1024 * 1024 * 1024),
            'categories': len(self.get_categories()),
            'ai_groups': len(self.get_ai_groups()),
            'file_types': len(self.get_file_types())
        }
