"""
AI Classifier - Local AI for intelligent file organization

Uses local sentence transformers for content-based classification.
NO cloud APIs - fully offline.
"""

import logging
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
            
            # Use cache directory
            cache_dir = Path(self.ai_config.get('model_path', '../AI Model'))
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            self.model = SentenceTransformer(model_name, cache_folder=str(cache_dir))
            logger.info("AI model loaded successfully")
            
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
        
        # Extract text content if possible
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
    
    def get_status(self) -> Dict:
        """Get AI system status."""
        return {
            'enabled': self.enabled,
            'transformers_available': TRANSFORMERS_AVAILABLE,
            'model_loaded': self.model is not None,
            'model_name': self.ai_config.get('embedding_model', 'all-MiniLM-L6-v2') if self.enabled else None
        }
