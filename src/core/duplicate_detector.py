"""
Duplicate File Detection Module
Detects and manages duplicate files based on content hashing.
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """Detects duplicate files using content-based hashing."""
    
    def __init__(self):
        """Initialize duplicate detector."""
        self.hash_cache: Dict[Path, str] = {}
        self.size_cache: Dict[Path, int] = {}
        
    def compute_file_hash(self, file_path: Path, algorithm: str = 'sha256') -> str:
        """
        Compute hash of file content.
        
        Args:
            file_path: Path to file
            algorithm: Hash algorithm (sha256, md5)
            
        Returns:
            Hex string of file hash
        """
        # Check cache first
        if file_path in self.hash_cache:
            return self.hash_cache[file_path]
        
        try:
            if algorithm == 'sha256':
                hasher = hashlib.sha256()
            elif algorithm == 'md5':
                hasher = hashlib.md5()
            else:
                hasher = hashlib.sha256()
            
            # Read file in chunks for memory efficiency
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            
            file_hash = hasher.hexdigest()
            self.hash_cache[file_path] = file_hash
            return file_hash
            
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            return ""
    
    def get_file_size(self, file_path: Path) -> int:
        """
        Get file size in bytes.
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in bytes
        """
        if file_path in self.size_cache:
            return self.size_cache[file_path]
        
        try:
            size = file_path.stat().st_size
            self.size_cache[file_path] = size
            return size
        except Exception as e:
            logger.error(f"Error getting file size {file_path}: {e}")
            return 0
    
    def find_duplicates(
        self, 
        files: List[Path],
        algorithm: str = 'sha256'
    ) -> Dict[str, List[Path]]:
        """
        Find duplicate files based on content hash.
        
        Args:
            files: List of file paths to check
            algorithm: Hash algorithm to use
            
        Returns:
            Dictionary mapping hash to list of duplicate file paths
            Only includes hashes with 2+ files
        """
        logger.info(f"Scanning {len(files)} files for duplicates...")
        
        # Step 1: Group by file size (fast pre-filter)
        size_groups: Dict[int, List[Path]] = defaultdict(list)
        for file_path in files:
            if not file_path.exists() or not file_path.is_file():
                continue
            size = self.get_file_size(file_path)
            if size > 0:  # Skip empty files
                size_groups[size].append(file_path)
        
        logger.info(f"Found {len(size_groups)} unique file sizes")
        
        # Step 2: Hash only files with same size (potential duplicates)
        hash_groups: Dict[str, List[Path]] = defaultdict(list)
        files_to_hash = []
        
        for size, paths in size_groups.items():
            if len(paths) > 1:  # Only hash if multiple files have same size
                files_to_hash.extend(paths)
        
        logger.info(f"Hashing {len(files_to_hash)} potential duplicate files...")
        
        for file_path in files_to_hash:
            file_hash = self.compute_file_hash(file_path, algorithm)
            if file_hash:
                hash_groups[file_hash].append(file_path)
        
        # Step 3: Filter to only groups with duplicates (2+ files)
        duplicates = {
            hash_val: paths 
            for hash_val, paths in hash_groups.items() 
            if len(paths) > 1
        }
        
        logger.info(f"Found {len(duplicates)} duplicate groups")
        return duplicates
    
    def analyze_duplicates(self, duplicates: Dict[str, List[Path]]) -> Dict:
        """
        Analyze duplicate file groups and compute statistics.
        
        Args:
            duplicates: Dictionary from find_duplicates()
            
        Returns:
            Dictionary with analysis results:
            - total_duplicate_files: Total number of duplicate files
            - duplicate_groups: Number of duplicate groups
            - wasted_space: Total wasted storage space in bytes
            - wasted_space_mb: Wasted space in MB
            - largest_duplicate_group: Largest group info
        """
        if not duplicates:
            return {
                'total_duplicate_files': 0,
                'duplicate_groups': 0,
                'wasted_space': 0,
                'wasted_space_mb': 0.0,
                'largest_duplicate_group': None
            }
        
        total_files = sum(len(paths) for paths in duplicates.values())
        total_groups = len(duplicates)
        
        # Calculate wasted space (keep 1 copy, rest is wasted)
        wasted_space = 0
        largest_group = None
        largest_group_size = 0
        
        for hash_val, paths in duplicates.items():
            if paths:
                file_size = self.get_file_size(paths[0])
                # Wasted space = (number of copies - 1) * file_size
                wasted = (len(paths) - 1) * file_size
                wasted_space += wasted
                
                if len(paths) > largest_group_size:
                    largest_group_size = len(paths)
                    largest_group = {
                        'count': len(paths),
                        'size': file_size,
                        'size_mb': file_size / (1024 * 1024),
                        'sample_file': paths[0].name
                    }
        
        return {
            'total_duplicate_files': total_files,
            'duplicate_groups': total_groups,
            'wasted_space': wasted_space,
            'wasted_space_mb': wasted_space / (1024 * 1024),
            'largest_duplicate_group': largest_group
        }
    
    def select_files_to_keep(
        self, 
        duplicate_group: List[Path],
        strategy: str = 'newest'
    ) -> Tuple[Path, List[Path]]:
        """
        Select which file to keep and which to remove from duplicate group.
        
        Args:
            duplicate_group: List of duplicate file paths
            strategy: Selection strategy:
                - 'newest': Keep most recently modified
                - 'oldest': Keep oldest file
                - 'shortest_path': Keep file with shortest path
                - 'longest_name': Keep file with longest name
                
        Returns:
            Tuple of (file_to_keep, files_to_remove)
        """
        if not duplicate_group:
            return None, []
        
        if len(duplicate_group) == 1:
            return duplicate_group[0], []
        
        try:
            if strategy == 'newest':
                # Keep most recently modified
                sorted_files = sorted(
                    duplicate_group, 
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
                )
            elif strategy == 'oldest':
                # Keep oldest file
                sorted_files = sorted(
                    duplicate_group, 
                    key=lambda p: p.stat().st_mtime
                )
            elif strategy == 'shortest_path':
                # Keep file with shortest path
                sorted_files = sorted(
                    duplicate_group, 
                    key=lambda p: len(str(p))
                )
            elif strategy == 'longest_name':
                # Keep file with longest name
                sorted_files = sorted(
                    duplicate_group, 
                    key=lambda p: len(p.name),
                    reverse=True
                )
            else:
                # Default: keep first file
                sorted_files = duplicate_group
            
            keep = sorted_files[0]
            remove = sorted_files[1:]
            
            return keep, remove
            
        except Exception as e:
            logger.error(f"Error selecting files: {e}")
            return duplicate_group[0], duplicate_group[1:]
    
    def clear_cache(self):
        """Clear hash and size caches."""
        self.hash_cache.clear()
        self.size_cache.clear()
        logger.debug("Cleared duplicate detector cache")
