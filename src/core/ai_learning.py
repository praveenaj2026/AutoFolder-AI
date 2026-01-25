"""  AI Learning System - Collect user feedback to improve AI accuracy.

Phase 3.7 Feature: Track user corrections and learn from them.
Simplified version - stores feedback for future model improvements.

PERSISTENCE:
- YES, data persists across sessions!
- Feedback stored in: Documents/AutoFolder_Logs/ai_feedback.json
- Stats stored in: Documents/AutoFolder_Logs/ai_stats.json
- Data accumulates over time as you use the app
- Each organization operation is tracked and saved
- Accuracy estimates improve as more data is collected

HOW IT WORKS:
1. Every time you organize files, it records the AI's decisions
2. When you manually move files after organization, it learns from that
3. When you rename AI groups, it learns from that
4. Over time, statistics show AI accuracy trends
5. Data can be exported for model retraining (future feature)

USAGE:
- Just use the app normally - learning happens automatically
- Check "🧠 AI Learning Stats" button to see accumulated data
- More you use it, more accurate the stats become
- Feedback helps improve future versions of the AI model
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AILearningSystem:
    """
    Track user corrections to AI classifications for future improvements.
    
    Features:
    - Track when users move files after organization
    - Track AI group renames
    - Store feedback data for analysis
    - Generate accuracy reports
    """
    
    def __init__(self, config: Dict = None, data_folder: Path = None):
        """
        Initialize AI learning system.
        
        Args:
            config: Configuration dictionary
            data_folder: Where to store learning data
        """
        self.config = config or {}
        self.learning_config = self.config.get('ai_learning', {})
        
        # Settings
        self.enabled = self.learning_config.get('enabled', True)
        self.collect_corrections = self.learning_config.get('collect_corrections', True)
        
        # Data storage
        if data_folder is None:
            data_folder = Path.home() / "Documents" / "AutoFolder_Logs"
        
        self.data_folder = data_folder
        self.data_folder.mkdir(parents=True, exist_ok=True)
        
        self.feedback_file = self.data_folder / "ai_feedback.json"
        self.stats_file = self.data_folder / "ai_stats.json"
        
        # Load existing data
        self.feedback_data = self._load_feedback()
        self.stats = self._load_stats()
        
        logger.info(f"AI Learning System initialized: {len(self.feedback_data)} feedback entries")
    
    def _load_feedback(self) -> List[Dict]:
        """Load existing feedback data."""
        try:
            if self.feedback_file.exists():
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading feedback data: {e}")
        return []
    
    def _save_feedback(self):
        """Save feedback data to file."""
        try:
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving feedback data: {e}")
    
    def _load_stats(self) -> Dict:
        """Load AI statistics."""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading stats: {e}")
        
        return {
            'total_organized': 0,
            'total_corrections': 0,
            'accuracy_estimates': [],
            'common_corrections': {}
        }
    
    def _save_stats(self):
        """Save stats to file."""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    def record_organization(self, files_organized: int, ai_groups_created: int):
        """
        Record an organization operation.
        
        Args:
            files_organized: Number of files organized
            ai_groups_created: Number of AI groups created
        """
        if not self.enabled:
            return
        
        self.stats['total_organized'] += files_organized
        self.stats['last_organization'] = datetime.now().isoformat()
        self.stats['last_ai_groups'] = ai_groups_created
        
        self._save_stats()
        logger.debug(f"Recorded organization: {files_organized} files, {ai_groups_created} groups")
    
    def record_correction(
        self, 
        filename: str,
        original_group: str,
        corrected_group: str,
        file_extension: str = None,
        document_type: str = None
    ):
        """
        Record when a user corrects an AI classification.
        
        Args:
            filename: Name of the file
            original_group: AI's original grouping
            corrected_group: User's corrected grouping
            file_extension: File extension
            document_type: Detected document type (from content analysis)
        """
        if not self.enabled or not self.collect_corrections:
            return
        
        correction = {
            'timestamp': datetime.now().isoformat(),
            'filename': filename,
            'original_group': original_group,
            'corrected_group': corrected_group,
            'extension': file_extension,
            'document_type': document_type
        }
        
        self.feedback_data.append(correction)
        self._save_feedback()
        
        # Update stats
        self.stats['total_corrections'] += 1
        
        # Track common corrections
        correction_key = f"{original_group} → {corrected_group}"
        if correction_key not in self.stats['common_corrections']:
            self.stats['common_corrections'][correction_key] = 0
        self.stats['common_corrections'][correction_key] += 1
        
        self._save_stats()
        
        logger.info(f"Recorded correction: '{filename}' from '{original_group}' to '{corrected_group}'")
    
    def record_group_rename(self, old_name: str, new_name: str, file_count: int):
        """
        Record when a user renames an AI group.
        
        Args:
            old_name: Original AI group name
            new_name: User's new name
            file_count: Number of files in the group
        """
        if not self.enabled:
            return
        
        rename = {
            'timestamp': datetime.now().isoformat(),
            'type': 'group_rename',
            'old_name': old_name,
            'new_name': new_name,
            'file_count': file_count
        }
        
        self.feedback_data.append(rename)
        self._save_feedback()
        
        logger.info(f"Recorded group rename: '{old_name}' → '{new_name}' ({file_count} files)")
    
    def record_file_move(self, filename: str, from_group: str, to_group: str):
        """
        Record when a user moves a file to a different group.
        
        Args:
            filename: Name of the file
            from_group: Original group
            to_group: Destination group
        """
        self.record_correction(filename, from_group, to_group)
    
    def get_accuracy_estimate(self) -> Dict:
        """
        Calculate estimated AI accuracy based on corrections.
        
        Returns:
            Accuracy statistics
        """
        total_organized = self.stats.get('total_organized', 0)
        total_corrections = self.stats.get('total_corrections', 0)
        
        if total_organized == 0:
            return {
                'accuracy_percent': 100.0,
                'total_organized': 0,
                'total_corrections': 0,
                'message': 'No data yet'
            }
        
        # Estimate: files organized - corrections = correct classifications
        correct = total_organized - total_corrections
        accuracy = (correct / total_organized) * 100 if total_organized > 0 else 100
        
        return {
            'accuracy_percent': round(accuracy, 1),
            'total_organized': total_organized,
            'total_corrections': total_corrections,
            'correct_classifications': correct,
            'message': self._get_accuracy_message(accuracy)
        }
    
    def _get_accuracy_message(self, accuracy: float) -> str:
        """Get human-readable accuracy message."""
        if accuracy >= 95:
            return "🎯 Excellent! AI is very accurate"
        elif accuracy >= 85:
            return "✅ Good accuracy"
        elif accuracy >= 70:
            return "📊 Fair accuracy - more corrections will help"
        else:
            return "⚠️ Needs improvement - keep correcting!"
    
    def get_common_corrections(self, limit: int = 10) -> List[Dict]:
        """
        Get most common correction patterns.
        
        Args:
            limit: Maximum number of patterns to return
            
        Returns:
            List of correction patterns with counts
        """
        corrections = self.stats.get('common_corrections', {})
        
        sorted_corrections = sorted(
            corrections.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:limit]
        
        return [
            {'pattern': pattern, 'count': count}
            for pattern, count in sorted_corrections
        ]
    
    def get_learning_suggestions(self) -> List[str]:
        """
        Generate suggestions based on collected feedback.
        
        Returns:
            List of suggestions for improving AI
        """
        suggestions = []
        
        common = self.get_common_corrections(5)
        
        for item in common:
            pattern = item['pattern']
            count = item['count']
            if count >= 3:
                suggestions.append(
                    f"AI often confuses '{pattern}' ({count} corrections). "
                    f"Consider this pattern for future training."
                )
        
        accuracy = self.get_accuracy_estimate()
        if accuracy['accuracy_percent'] < 85:
            suggestions.append(
                f"Current accuracy is {accuracy['accuracy_percent']}%. "
                f"More corrections will help identify patterns."
            )
        
        if not suggestions:
            suggestions.append("AI is performing well! Keep using it to collect more data.")
        
        return suggestions
    
    def export_training_data(self, output_file: Path = None) -> Path:
        """
        Export collected data for potential model training.
        
        Args:
            output_file: Where to save (None = auto-generate)
            
        Returns:
            Path to exported file
        """
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = self.data_folder / f"training_data_{timestamp}.json"
        
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'total_entries': len(self.feedback_data),
            'stats': self.stats,
            'feedback': self.feedback_data
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Exported training data to {output_file}")
        return output_file
    
    def get_status(self) -> Dict:
        """Get learning system status."""
        accuracy = self.get_accuracy_estimate()
        
        return {
            'enabled': self.enabled,
            'collect_corrections': self.collect_corrections,
            'total_feedback_entries': len(self.feedback_data),
            'total_organized': self.stats.get('total_organized', 0),
            'total_corrections': self.stats.get('total_corrections', 0),
            'accuracy_percent': accuracy['accuracy_percent'],
            'data_file': str(self.feedback_file)
        }
    
    def clear_data(self):
        """Clear all collected data (for privacy or reset)."""
        self.feedback_data = []
        self.stats = {
            'total_organized': 0,
            'total_corrections': 0,
            'accuracy_estimates': [],
            'common_corrections': {}
        }
        
        self._save_feedback()
        self._save_stats()
        
        logger.info("AI learning data cleared")


# Standalone testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    learner = AILearningSystem()
    print(f"Status: {learner.get_status()}")
    
    # Simulate some data
    learner.record_organization(50, 5)
    learner.record_correction("resume.pdf", "Documents", "Resume")
    learner.record_correction("invoice.pdf", "Documents", "Invoices")
    
    print(f"\nAccuracy: {learner.get_accuracy_estimate()}")
    print(f"Suggestions: {learner.get_learning_suggestions()}")
