"""
AI Classifier - Local AI for intelligent file organization

Uses local sentence transformers for content-based classification.
NO cloud APIs - fully offline.
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re

# Conditional imports for AI features
try:
    from sentence_transformers import SentenceTransformer
    import torch
    import numpy as np
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    from ..core.file_analyzer import FileAnalyzer
except ImportError:
    from core.file_analyzer import FileAnalyzer

# Import content analyzer for Phase 3.7
try:
    from ..core.content_analyzer import ContentAnalyzer
except ImportError:
    try:
        from core.content_analyzer import ContentAnalyzer
    except ImportError:
        ContentAnalyzer = None


logger = logging.getLogger(__name__)


class AIClassifier:
    """Local AI classifier for intelligent file organization."""
    
    def __init__(self, config: dict):
        """
        Initialize AI classifier.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.ai_config = config.get('ai', {})
        self.enabled = self.ai_config.get('enabled', False) and TRANSFORMERS_AVAILABLE
        
        self.model = None
        self.file_analyzer = FileAnalyzer()
        
        # Phase 3.7: Content analyzer for PDF/OCR analysis
        self.content_analyzer = None
        if ContentAnalyzer:
            try:
                self.content_analyzer = ContentAnalyzer(config)
                logger.info(f"Content analyzer initialized: {self.content_analyzer.get_status()}")
            except Exception as e:
                logger.warning(f"Content analyzer not available: {e}")
        
        # Predefined categories with semantic descriptions
        self.categories = {
            'work': {
                'description': 'work documents, professional files, business reports, spreadsheets, presentations',
                'keywords': ['report', 'invoice', 'proposal', 'contract', 'meeting', 'presentation', 'budget']
            },
            'personal': {
                'description': 'personal documents, letters, resumes, certificates, forms',
                'keywords': ['resume', 'cv', 'certificate', 'personal', 'letter', 'form']
            },
            'financial': {
                'description': 'financial documents, invoices, receipts, tax forms, bank statements',
                'keywords': ['invoice', 'receipt', 'tax', 'bank', 'statement', 'payment']
            },
            'academic': {
                'description': 'academic papers, research, thesis, study materials, lecture notes',
                'keywords': ['research', 'thesis', 'paper', 'study', 'lecture', 'university', 'college']
            },
            'media': {
                'description': 'photos, videos, music, entertainment files',
                'keywords': ['photo', 'video', 'music', 'movie', 'song', 'album']
            },
            'screenshots': {
                'description': 'screenshots, screen captures, snapshots',
                'keywords': ['screenshot', 'capture', 'snap', 'screen']
            },
            'downloads': {
                'description': 'downloaded files, installers, temporary files',
                'keywords': ['download', 'installer', 'setup', 'temp']
            },
            'projects': {
                'description': 'project files, source code, development files',
                'keywords': ['project', 'source', 'code', 'development', 'repository']
            }
        }
        
        if self.enabled:
            self._load_model()
        else:
            if not TRANSFORMERS_AVAILABLE:
                logger.warning("AI features disabled: sentence-transformers not installed")
            else:
                logger.info("AI features disabled in configuration")
    
    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            model_name = self.ai_config.get('embedding_model', 'all-MiniLM-L6-v2')
            logger.info(f"Loading AI model: {model_name}")
            
            # Use cache directory.
            # - In dev: relative to project root
            # - In frozen EXE: relative to the EXE folder
            if getattr(sys, 'frozen', False):
                app_root = Path(sys.executable).resolve().parent
            else:
                app_root = Path(__file__).resolve().parents[2]

            configured = self.ai_config.get('model_path', 'models')
            cache_dir = Path(configured)
            if not cache_dir.is_absolute():
                cache_dir = app_root / cache_dir
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Force offline mode - use cached model only, no internet required
            self.model = SentenceTransformer(
                model_name, 
                cache_folder=str(cache_dir),
                local_files_only=True  # OFFLINE MODE: Use cached model only
            )
            logger.info("AI model loaded successfully (offline mode)")
            
        except Exception as e:
            logger.error(f"Failed to load AI model: {e}")
            self.enabled = False
    
    def classify_file(self, file_path: Path) -> Optional[Dict]:
        """
        Classify a file using AI.
        
        Args:
            file_path: Path to file
            
        Returns:
            Classification result with category and confidence
        """
        if not self.enabled:
            return None
        
        try:
            # Get file info
            file_info = self.file_analyzer.analyze_file(file_path)
            
            # Build description for classification
            description = self._build_file_description(file_path, file_info)
            
            if not description:
                return None
            
            # Get embeddings
            desc_embedding = self.model.encode(description, convert_to_tensor=True)
            
            # Calculate similarity with each category
            similarities = {}
            for category, info in self.categories.items():
                cat_embedding = self.model.encode(info['description'], convert_to_tensor=True)
                similarity = torch.nn.functional.cosine_similarity(
                    desc_embedding.unsqueeze(0),
                    cat_embedding.unsqueeze(0)
                ).item()
                similarities[category] = similarity
            
            # Get best match
            best_category = max(similarities, key=similarities.get)
            confidence = similarities[best_category]
            
            threshold = self.ai_config.get('confidence_threshold', 0.7)
            
            if confidence >= threshold:
                logger.debug(f"AI classified '{file_path.name}' as '{best_category}' (confidence: {confidence:.2f})")
                return {
                    'category': best_category,
                    'confidence': confidence,
                    'all_scores': similarities
                }
            else:
                logger.debug(f"AI classification below threshold for '{file_path.name}' (best: {confidence:.2f})")
                return None
                
        except Exception as e:
            logger.error(f"Error classifying file {file_path.name}: {e}")
            return None
    
    def suggest_folder_name(self, files: List[Path]) -> List[Tuple[str, float]]:
        """
        Suggest folder names based on file contents.
        
        Args:
            files: List of file paths
            
        Returns:
            List of (folder_name, confidence) tuples
        """
        if not self.enabled or not files:
            return []
        
        try:
            # Classify all files
            classifications = []
            for file_path in files[:50]:  # Limit to first 50 files
                result = self.classify_file(file_path)
                if result:
                    classifications.append(result['category'])
            
            if not classifications:
                return []
            
            # Find most common categories
            from collections import Counter
            category_counts = Counter(classifications)
            
            # Generate suggestions
            suggestions = []
            total = len(classifications)
            
            for category, count in category_counts.most_common(5):
                confidence = count / total
                if confidence >= 0.3:  # At least 30% of files
                    suggestions.append((category.title(), confidence))
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting folder names: {e}")
            return []
    
    def find_duplicates(self, files: List[Path]) -> List[List[Path]]:
        """
        Find semantically similar files (duplicates with different names).
        
        Args:
            files: List of file paths
            
        Returns:
            List of duplicate groups
        """
        if not self.enabled or len(files) < 2:
            return []
        
        try:
            # Build descriptions and embeddings for all files
            file_data = []
            for file_path in files[:100]:  # Limit to prevent memory issues
                info = self.file_analyzer.analyze_file(file_path)
                description = self._build_file_description(file_path, info)
                if description:
                    embedding = self.model.encode(description, convert_to_tensor=True)
                    file_data.append({
                        'path': file_path,
                        'embedding': embedding
                    })
            
            if len(file_data) < 2:
                return []
            
            # Find similar pairs
            duplicates = []
            similarity_threshold = 0.85  # Very high similarity
            
            for i in range(len(file_data)):
                group = [file_data[i]['path']]
                
                for j in range(i + 1, len(file_data)):
                    similarity = torch.nn.functional.cosine_similarity(
                        file_data[i]['embedding'].unsqueeze(0),
                        file_data[j]['embedding'].unsqueeze(0)
                    ).item()
                    
                    if similarity >= similarity_threshold:
                        group.append(file_data[j]['path'])
                
                if len(group) > 1:
                    duplicates.append(group)
            
            logger.info(f"Found {len(duplicates)} groups of similar files")
            return duplicates
            
        except Exception as e:
            logger.error(f"Error finding duplicates: {e}")
            return []
    
    def _build_file_description(self, file_path: Path, file_info: Dict) -> str:
        """Build a text description of the file for AI analysis."""
        
        parts = []
        
        # Filename (cleaned)
        name = file_path.stem
        # Remove common suffixes and numbers
        name = re.sub(r'[\(\)\[\]\d_-]+', ' ', name)
        name = ' '.join(name.split())
        parts.append(name)
        
        # File category
        category = file_info.get('category', 'unknown')
        if category != 'other':
            parts.append(f"{category} file")
        
        # Phase 3.7: Use content analyzer for PDFs and images
        if self.content_analyzer and self.content_analyzer.is_available():
            try:
                analysis = self.content_analyzer.analyze_file(file_path)
                if analysis.get('analyzed'):
                    # Add detected document type
                    doc_type = analysis.get('document_type')
                    if doc_type and doc_type != 'Unknown':
                        parts.append(doc_type.lower().replace('_', ' '))
                        parts.append(f"type {doc_type}")
                    
                    # Add keywords found
                    keywords = analysis.get('keywords_found', [])
                    if keywords:
                        parts.extend(keywords[:5])
                    
                    # Add text preview (high value for AI grouping)
                    text_preview = analysis.get('text_preview', '')
                    if text_preview:
                        parts.append(text_preview)
                    
                    logger.debug(f"Content analysis enhanced: {file_path.name} -> {doc_type}")
            except Exception as e:
                logger.debug(f"Content analysis skipped for {file_path.name}: {e}")
        
        # Fallback: Extract text content if content analyzer didn't work
        if len(parts) <= 2:
            text_preview = self.file_analyzer.extract_text_preview(file_path, max_chars=200)
            if text_preview:
                # Clean and truncate
                text_preview = ' '.join(text_preview.split())[:200]
                parts.append(text_preview)
        
        # Check for special patterns
        if self.file_analyzer.is_likely_screenshot(file_path):
            parts.append("screenshot image")
        
        if self.file_analyzer.is_likely_download(file_path):
            parts.append("downloaded file")
        
        return ' '.join(parts)
    
    def create_semantic_groups(self, files: List[Path], min_group_size: int = 2) -> Dict[str, List[Path]]:
        """
        Group files by semantic similarity for intelligent organization.
        
        Args:
            files: List of file paths to group
            min_group_size: Minimum files to form a group
            
        Returns:
            Dictionary mapping group names to file lists
        """
        if not self.enabled or len(files) < min_group_size:
            return {}
        
        try:
            logger.info(f"Creating semantic groups for {len(files)} files")
            
            # Limit for performance (process in batches if needed)
            files_to_process = files[:500]  
            
            # Build embeddings for all files
            file_data = []
            for file_path in files_to_process:
                try:
                    info = self.file_analyzer.analyze_file(file_path)
                    description = self._build_file_description(file_path, info)
                    if description:
                        embedding = self.model.encode(description, convert_to_tensor=True)
                        file_data.append({
                            'path': file_path,
                            'embedding': embedding,
                            'description': description
                        })
                except Exception as e:
                    logger.debug(f"Error processing {file_path.name}: {e}")
                    continue
            
            if len(file_data) < min_group_size:
                return {}
            
            # Convert to numpy for clustering
            embeddings = np.array([f['embedding'].cpu().numpy() for f in file_data])
            
            # Use simple similarity-based clustering
            groups = {}
            used_indices = set()
            group_id = 0
            similarity_threshold = 0.65  # Files with 65%+ similarity are grouped
            
            for i in range(len(file_data)):
                if i in used_indices:
                    continue
                
                # Start new group with this file
                group_members = [i]
                used_indices.add(i)
                
                # Find similar files
                for j in range(i + 1, len(file_data)):
                    if j in used_indices:
                        continue
                    
                    similarity = np.dot(embeddings[i], embeddings[j]) / (
                        np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                    )
                    
                    if similarity >= similarity_threshold:
                        group_members.append(j)
                        used_indices.add(j)
                
                # Create group if meets minimum size
                if len(group_members) >= min_group_size:
                    # Generate smart group name based on common themes
                    group_files = [file_data[idx]['path'] for idx in group_members]
                    group_name = self._generate_group_name(group_files, file_data, group_members)
                    groups[group_name] = group_files
                    logger.debug(f"Created group '{group_name}' with {len(group_files)} files")
                    group_id += 1
            
            logger.info(f"Created {len(groups)} semantic groups from {len(files_to_process)} files")
            return groups
            
        except Exception as e:
            logger.error(f"Error creating semantic groups: {e}", exc_info=True)
            return {}
    
    def _generate_group_name(self, files: List[Path], file_data: List[Dict], indices: List[int]) -> str:
        """Generate a descriptive name for a group of similar files."""
        try:
            # Extract common words from filenames
            all_words = []
            for idx in indices:
                name = file_data[idx]['path'].stem.lower()
                # Clean and split
                name = re.sub(r'[^a-z0-9\s]', ' ', name)
                words = [w for w in name.split() if len(w) > 3 and not w.isdigit()]
                all_words.extend(words)
            
            # Find most common meaningful word
            from collections import Counter
            if all_words:
                word_counts = Counter(all_words)
                # Remove common generic words
                stop_words = {'file', 'document', 'image', 'photo', 'copy', 'new', 'untitled'}
                meaningful_words = [w for w, c in word_counts.most_common(10) 
                                   if w not in stop_words and c >= 2]
                
                if meaningful_words:
                    # Use top word
                    return meaningful_words[0].title()
            
            # Fallback: Use category-based name
            categories = Counter([f.suffix.lower().strip('.') for f in files])
            if categories:
                top_ext = categories.most_common(1)[0][0].upper()
                return f"{top_ext} Collection"
            
            return "Similar Items"
            
        except Exception as e:
            logger.debug(f"Error generating group name: {e}")
            return f"Group {len(indices)}"
    
    def get_status(self) -> Dict:
        """Get AI system status."""
        status = {
            'enabled': self.enabled,
            'transformers_available': TRANSFORMERS_AVAILABLE,
            'model_loaded': self.model is not None,
            'model_name': self.ai_config.get('embedding_model', 'all-MiniLM-L6-v2') if self.enabled else None
        }
        
        # Phase 3.7: Add content analyzer status
        if self.content_analyzer:
            content_status = self.content_analyzer.get_status()
            status['content_analysis'] = content_status
        else:
            status['content_analysis'] = {'enabled': False, 'pdf_available': False, 'ocr_available': False}
        
        return status
