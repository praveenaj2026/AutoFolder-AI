"""
Undo Manager

Manages undo history for file organization operations.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


class UndoManager:
    """Manages undo/redo operations for file organization."""
    
    def __init__(self, max_history: int = 10, history_file: str = '.undo_journal/history.json'):
        """
        Initialize undo manager.
        
        Args:
            max_history: Maximum number of operations to keep
            history_file: Path to history file
        """
        self.max_history = max_history
        self.history_file = Path(history_file)
        self.history: List[Dict] = []
        
        # Create directory if needed
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing history
        self._load_history()
    
    def save_operation(self, operation: Dict):
        """
        Save an operation to history.
        
        Args:
            operation: Operation dictionary with details
        """
        # Add timestamp if not present
        if 'timestamp' not in operation:
            operation['timestamp'] = datetime.now()
        
        # Convert datetime to string for JSON serialization
        if isinstance(operation['timestamp'], datetime):
            operation['timestamp'] = operation['timestamp'].isoformat()
        
        # Convert Path objects to strings
        for op in operation.get('operations', []):
            if isinstance(op.get('source'), Path):
                op['source'] = str(op['source'])
            if isinstance(op.get('target'), Path):
                op['target'] = str(op['target'])
        
        # Add to history
        self.history.append(operation)
        
        # Trim history if too long
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        # Persist to disk
        self._save_history()
        
        logger.info(f"Operation saved to undo history ({len(self.history)} total)")
    
    def get_last_operation(self) -> Optional[Dict]:
        """
        Get the most recent operation.
        
        Returns:
            Operation dictionary or None
        """
        if not self.history:
            return None
        
        # Convert string paths back to Path objects
        op = self.history[-1].copy()
        for item in op.get('operations', []):
            if 'source' in item:
                item['source'] = Path(item['source'])
            if 'target' in item:
                item['target'] = Path(item['target'])
        
        return op
    
    def remove_last_operation(self):
        """Remove the most recent operation from history."""
        if self.history:
            self.history.pop()
            self._save_history()
            logger.info("Last operation removed from history")
    
    def get_history(self) -> List[Dict]:
        """Get all operations in history."""
        return self.history.copy()
    
    def clear_history(self):
        """Clear all history."""
        self.history = []
        self._save_history()
        logger.info("Undo history cleared")
    
    def _load_history(self):
        """Load history from disk."""
        if not self.history_file.exists():
            return
        
        try:
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)
            logger.debug(f"Loaded {len(self.history)} operations from history")
        except Exception as e:
            logger.error(f"Failed to load undo history: {e}")
            self.history = []
    
    def _save_history(self):
        """Save history to disk."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
            logger.debug("Undo history saved to disk")
        except Exception as e:
            logger.error(f"Failed to save undo history: {e}")
