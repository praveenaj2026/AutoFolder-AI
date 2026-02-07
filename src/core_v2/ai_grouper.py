"""
AI Grouper v2.0 - Semantic File Grouping

Uses sentence transformers to group files by semantic similarity,
going beyond simple extension-based classification.
"""

import logging
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple, Optional
from collections import Counter, defaultdict
from datetime import datetime

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

from .models import FileNode, RuleResult, AIResult
from .context_builder import ContextBuilder

# Try to import sentence transformer, fall back gracefully
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class AIGroupConfig:
    """
    Configuration for AI grouping.
    
    Attributes:
        min_group_size: Minimum files per AI group (default: 3)
        max_group_size: Maximum files per AI group (default: 50)
        similarity_threshold: Cosine similarity threshold 0-1 (default: 0.75)
        use_content_analysis: Read file contents for analysis (expensive)
        max_content_bytes: Max bytes to read for content analysis
        min_confidence: Minimum confidence to suggest AI grouping
    """
    min_group_size: int = 3
    max_group_size: int = 50
    similarity_threshold: float = 0.75
    use_content_analysis: bool = False
    max_content_bytes: int = 10000
    min_confidence: float = 0.7


class AIGrouper:
    """
    Groups files semantically using sentence transformers.
    
    Analyzes:
    - Filename patterns (primary)
    - File metadata (dates, sizes)
    - Optional content analysis (for text files)
    
    Generates AIResult objects for intelligent grouping.
    """
    
    def __init__(self, config: Optional[AIGroupConfig] = None):
        """
        Initialize AI grouper.
        
        Args:
            config: Optional configuration, uses defaults if None
        """
        self.config = config or AIGroupConfig()
        self.model: Optional['SentenceTransformer'] = None
        self.context_builder = ContextBuilder()
        
        # Check if sentence transformers available
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning(
                "sentence-transformers not available. "
                "AI grouping will use fallback mode."
            )
    
    def _load_model(self):
        """Lazy load sentence transformer model."""
        if self.model is not None:
            return
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("Cannot load model: sentence-transformers not installed")
            return
        
        try:
            logger.info("Loading sentence transformer model...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
    
    def group_files(
        self,
        file_nodes: List[FileNode],
        rule_results: List[RuleResult],
        context_builder: Optional[ContextBuilder] = None
    ) -> List[AIResult]:
        """
        Group files semantically.
        
        Args:
            file_nodes: Files to group
            rule_results: Rule-based classifications (for context)
            context_builder: Optional context builder (uses own if None)
            
        Returns:
            List of AIResult objects with group suggestions
        """
        if not file_nodes:
            return []
        
        logger.info(f"AI grouping {len(file_nodes)} files")
        
        # Use provided context builder or default
        cb = context_builder or self.context_builder
        
        # Filter to files only (no directories)
        files = [f for f in file_nodes if not f.is_dir]
        
        if len(files) < self.config.min_group_size:
            logger.info("Too few files for AI grouping")
            return []
        
        # Build rule result map for quick lookup
        rule_map = {r.file: r for r in rule_results}
        
        # Extract features from filenames
        features = self._extract_features(files)
        
        # Generate embeddings
        embeddings = self._generate_embeddings(features)
        
        if embeddings is None:
            logger.warning("Embeddings generation failed, using fallback grouping")
            return self._fallback_grouping(files, rule_map)
        
        # Cluster similar files
        clusters = self._cluster_files(files, embeddings)
        
        # Create AIResult objects
        ai_results = self._create_ai_results(clusters, files, rule_map)
        
        logger.info(f"Created {len(ai_results)} AI groups")
        return ai_results
    
    def _extract_features(self, files: List[FileNode]) -> List[str]:
        """
        Extract semantic features from filenames.
        
        Args:
            files: Files to analyze
            
        Returns:
            List of feature strings for embedding
        """
        features = []
        
        for file in files:
            # Start with filename without extension
            name = file.path.stem
            
            # Remove common separators and numbers
            name = re.sub(r'[_\-\.]', ' ', name)
            name = re.sub(r'\d+', '', name)
            
            # Clean up whitespace
            name = ' '.join(name.split())
            
            # Extract date patterns if present
            date_match = re.search(r'(\d{4})', file.path.stem)
            date_str = f" {date_match.group(1)}" if date_match else ""
            
            # Combine filename + extension hint
            ext = file.path.suffix.lower()
            ext_hint = self._get_extension_hint(ext)
            
            feature = f"{name}{date_str} {ext_hint}".strip()
            features.append(feature)
        
        return features
    
    def _get_extension_hint(self, ext: str) -> str:
        """Get semantic hint from extension."""
        ext_map = {
            '.jpg': 'photo', '.jpeg': 'photo', '.png': 'image',
            '.mp3': 'music', '.wav': 'audio', '.flac': 'music',
            '.mp4': 'video', '.avi': 'video', '.mkv': 'video',
            '.pdf': 'document', '.docx': 'document', '.txt': 'text',
            '.xlsx': 'spreadsheet', '.csv': 'data',
            '.py': 'code', '.js': 'code', '.java': 'code',
            '.zip': 'archive', '.rar': 'archive', '.7z': 'archive',
        }
        return ext_map.get(ext, '')
    
    def _generate_embeddings(self, features: List[str]) -> Optional[np.ndarray]:
        """
        Generate embeddings for features.
        
        Args:
            features: Feature strings
            
        Returns:
            Numpy array of embeddings, or None if failed
        """
        if not features:
            return None
        
        # Load model if not loaded
        self._load_model()
        
        if self.model is None:
            return None
        
        try:
            # Generate embeddings in batches
            embeddings = self.model.encode(
                features,
                batch_size=32,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            return embeddings
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None
    
    def _cluster_files(
        self,
        files: List[FileNode],
        embeddings: np.ndarray
    ) -> Dict[int, List[int]]:
        """
        Cluster files by embedding similarity.
        
        Args:
            files: File nodes
            embeddings: File embeddings
            
        Returns:
            Dictionary mapping cluster_id -> list of file indices
        """
        # Compute similarity matrix
        similarity_matrix = cosine_similarity(embeddings)
        
        # Convert similarity to distance (1 - similarity)
        # Clip to avoid negative values due to floating point precision
        distance_matrix = np.clip(1 - similarity_matrix, 0, 2)
        
        # Apply DBSCAN clustering
        eps = 1 - self.config.similarity_threshold
        clustering = DBSCAN(
            eps=eps,
            min_samples=self.config.min_group_size,
            metric='precomputed'
        ).fit(distance_matrix)
        
        # Group files by cluster
        clusters: Dict[int, List[int]] = defaultdict(list)
        for idx, label in enumerate(clustering.labels_):
            if label != -1:  # -1 is noise/outliers
                clusters[label].append(idx)
        
        # Filter out oversized clusters
        filtered = {}
        for cluster_id, indices in clusters.items():
            if len(indices) <= self.config.max_group_size:
                filtered[cluster_id] = indices
            else:
                logger.warning(
                    f"Cluster {cluster_id} too large ({len(indices)} files), "
                    f"max is {self.config.max_group_size}"
                )
        
        logger.debug(f"Found {len(filtered)} valid clusters")
        return filtered
    
    def _create_ai_results(
        self,
        clusters: Dict[int, List[int]],
        files: List[FileNode],
        rule_map: Dict[FileNode, RuleResult]
    ) -> List[AIResult]:
        """
        Create AIResult objects from clusters.
        
        Args:
            clusters: Cluster assignments
            files: File nodes
            rule_map: Map of file -> rule result
            
        Returns:
            List of AIResult objects
        """
        ai_results = []
        
        for cluster_id, indices in clusters.items():
            # Get files in this cluster
            cluster_files = [files[i] for i in indices]
            
            # Generate group name
            group_name = self._generate_group_name(cluster_files, rule_map)
            
            # Calculate confidence
            confidence = self._calculate_confidence(cluster_files, indices)
            
            # Create AIResult for each file in cluster
            if confidence >= self.config.min_confidence and len(cluster_files) >= 2:
                # Create one AIResult per file (as per models.py design)
                for file in cluster_files:
                    # Other files in the group (excluding this one)
                    similar = tuple(f for f in cluster_files if f != file)
                    
                    ai_result = AIResult(
                        file=file,
                        group=group_name,
                        confidence=confidence,
                        similar_files=similar,
                        embedding=None,
                        context_used=f"Semantic similarity grouping: {len(cluster_files)} related files"
                    )
                    ai_results.append(ai_result)
        
        return ai_results
    
    def _generate_group_name(
        self,
        files: List[FileNode],
        rule_map: Dict[FileNode, RuleResult]
    ) -> str:
        """
        Generate intelligent group name from file cluster.
        
        Args:
            files: Files in group
            rule_map: Rule results for context
            
        Returns:
            Group name string
        """
        # Extract common terms from filenames
        all_words = []
        for file in files:
            name = file.path.stem
            # Remove numbers and separators
            name = re.sub(r'[_\-\.\d]+', ' ', name)
            words = [w.lower() for w in name.split() if len(w) > 2]
            all_words.extend(words)
        
        # Find most common words
        if all_words:
            word_counts = Counter(all_words)
            # Get top 2 most common words
            common = [word for word, count in word_counts.most_common(2)
                     if count >= len(files) * 0.3]  # Present in 30%+ of files
            
            if common:
                # Check for year patterns
                year = self._extract_common_year(files)
                year_str = f" {year}" if year else ""
                
                # Capitalize and combine
                name = ' '.join(word.capitalize() for word in common)
                return f"{name}{year_str} Group"
        
        # Fallback: use rule-based category
        categories = [rule_map[f].category for f in files if f in rule_map]
        if categories:
            common_category = Counter(categories).most_common(1)[0][0]
            return f"{common_category} Group"
        
        return "Related Files"
    
    def _extract_common_year(self, files: List[FileNode]) -> Optional[str]:
        """Extract common year from filenames."""
        years = []
        for file in files:
            match = re.search(r'(20\d{2})', file.path.stem)
            if match:
                years.append(match.group(1))
        
        if years:
            year_counts = Counter(years)
            most_common_year, count = year_counts.most_common(1)[0]
            # If year appears in >50% of files
            if count >= len(files) * 0.5:
                return most_common_year
        
        return None
    
    def _calculate_confidence(
        self,
        files: List[FileNode],
        indices: List[int]
    ) -> float:
        """
        Calculate confidence score for group.
        
        Higher confidence when:
        - Group size is optimal (5-20 files)
        - Filenames are very similar
        - Files are close in time
        """
        base_confidence = 0.7
        
        # Size bonus: prefer medium groups
        size = len(files)
        if 5 <= size <= 20:
            size_bonus = 0.1
        elif 3 <= size < 5 or 20 < size <= 30:
            size_bonus = 0.05
        else:
            size_bonus = 0.0
        
        # Time proximity bonus
        if files:
            mtimes = [f.mtime for f in files if f.mtime]
            if len(mtimes) > 1:
                time_range = max(mtimes) - min(mtimes)
                # Files within 30 days
                if time_range < 30 * 24 * 3600:
                    time_bonus = 0.1
                else:
                    time_bonus = 0.0
            else:
                time_bonus = 0.0
        else:
            time_bonus = 0.0
        
        confidence = min(base_confidence + size_bonus + time_bonus, 0.99)
        return round(confidence, 2)
    
    def _fallback_grouping(
        self,
        files: List[FileNode],
        rule_map: Dict[FileNode, RuleResult]
    ) -> List[AIResult]:
        """
        Fallback grouping when ML model unavailable.
        
        Uses simple heuristics:
        - Common filename prefixes
        - Date patterns
        - Extension grouping
        """
        logger.info("Using fallback grouping (no ML model)")
        
        # Group by common prefix
        prefix_groups: Dict[str, List[FileNode]] = defaultdict(list)
        
        for file in files:
            # Extract first meaningful word (3+ chars)
            # First remove numbers and common separators
            name = file.path.stem
            name = re.sub(r'[_\-\.\d]+', ' ', name)
            words = [w for w in name.split() if len(w) >= 3]
            prefix = words[0].lower() if words else "misc"
            prefix_groups[prefix].append(file)
        
        # Create AI results for large enough groups
        ai_results = []
        for prefix, group_files in prefix_groups.items():
            if len(group_files) >= self.config.min_group_size:
                group_name = f"{prefix.capitalize()} Files"
                
                # Create one AIResult per file
                for file in group_files:
                    similar = tuple(f for f in group_files if f != file)
                    
                    ai_result = AIResult(
                        file=file,
                        group=group_name,
                        confidence=0.6,  # Lower confidence for fallback
                        similar_files=similar,
                        embedding=None,
                        context_used=f"Pattern-based grouping: common prefix '{prefix}'"
                    )
                    ai_results.append(ai_result)
        
        return ai_results


def group_files_semantically(
    file_nodes: List[FileNode],
    rule_results: List[RuleResult],
    config: Optional[AIGroupConfig] = None
) -> List[AIResult]:
    """
    Convenience function for semantic file grouping.
    
    Args:
        file_nodes: Files to group
        rule_results: Rule-based classifications
        config: Optional configuration
        
    Returns:
        List of AIResult objects
    """
    grouper = AIGrouper(config)
    return grouper.group_files(file_nodes, rule_results)
