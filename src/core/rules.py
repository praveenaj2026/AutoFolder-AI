"""
Rule Engine

Defines and applies organization rules to files.
"""

from pathlib import Path
from typing import Dict, List
import re
from datetime import datetime, timedelta


class RuleEngine:
    """Engine for managing and applying organization rules."""
    
    def __init__(self):
        """Initialize rule engine with predefined profiles."""
        self.profiles = self._load_profiles()
    
    def _load_profiles(self) -> Dict[str, List[Dict]]:
        """Load predefined organization profiles."""
        
        return {
            'downloads': [
                {
                    'name': 'Documents',
                    'type': 'extension',
                    'patterns': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx'],
                    'target_folder': 'Documents'
                },
                {
                    'name': 'Images',
                    'type': 'extension',
                    'patterns': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico'],
                    'target_folder': 'Images'
                },
                {
                    'name': 'Videos',
                    'type': 'extension',
                    'patterns': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
                    'target_folder': 'Videos'
                },
                {
                    'name': 'Audio',
                    'type': 'extension',
                    'patterns': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
                    'target_folder': 'Audio'
                },
                {
                    'name': 'Archives',
                    'type': 'extension',
                    'patterns': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
                    'target_folder': 'Archives'
                },
                {
                    'name': 'Installers',
                    'type': 'extension',
                    'patterns': ['.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm', '.apk'],
                    'target_folder': 'Installers'
                },
                {
                    'name': 'Code',
                    'type': 'extension',
                    'patterns': ['.py', '.js', '.java', '.cpp', '.c', '.cs', '.html', '.css', '.php', '.json', '.xml'],
                    'target_folder': 'Code'
                }
            ],
            
            'media': [
                {
                    'name': 'Photos',
                    'type': 'extension',
                    'patterns': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic'],
                    'target_folder': 'Photos'
                },
                {
                    'name': 'Screenshots',
                    'type': 'name_pattern',
                    'patterns': [r'screenshot', r'screen shot', r'capture', r'snap'],
                    'target_folder': 'Screenshots'
                },
                {
                    'name': 'Videos',
                    'type': 'extension',
                    'patterns': ['.mp4', '.avi', '.mkv', '.mov', '.wmv'],
                    'target_folder': 'Videos'
                },
                {
                    'name': 'Recordings',
                    'type': 'name_pattern',
                    'patterns': [r'recording', r'record', r'replay', r'clip'],
                    'target_folder': 'Recordings'
                }
            ],
            
            'gaming': [
                {
                    'name': 'Game Recordings',
                    'type': 'name_pattern',
                    'patterns': [r'recording', r'replay', r'clip', r'gameplay'],
                    'target_folder': 'Recordings'
                },
                {
                    'name': 'Screenshots',
                    'type': 'name_pattern',
                    'patterns': [r'screenshot', r'screen', r'capture'],
                    'target_folder': 'Screenshots'
                },
                {
                    'name': 'Mods',
                    'type': 'extension',
                    'patterns': ['.pak', '.mod', '.vpk', '.wad'],
                    'target_folder': 'Mods'
                },
                {
                    'name': 'Saves',
                    'type': 'name_pattern',
                    'patterns': [r'save', r'savegame', r'\.sav'],
                    'target_folder': 'Saves'
                }
            ],
            
            'work': [
                {
                    'name': 'Documents',
                    'type': 'extension',
                    'patterns': ['.doc', '.docx', '.pdf', '.txt'],
                    'target_folder': 'Documents'
                },
                {
                    'name': 'Spreadsheets',
                    'type': 'extension',
                    'patterns': ['.xls', '.xlsx', '.csv'],
                    'target_folder': 'Spreadsheets'
                },
                {
                    'name': 'Presentations',
                    'type': 'extension',
                    'patterns': ['.ppt', '.pptx'],
                    'target_folder': 'Presentations'
                },
                {
                    'name': 'Code',
                    'type': 'extension',
                    'patterns': ['.py', '.js', '.html', '.css', '.json'],
                    'target_folder': 'Code'
                }
            ],
            
            'by_date': [
                {
                    'name': 'This Week',
                    'type': 'date_range',
                    'days_ago': 7,
                    'target_folder': 'This Week'
                },
                {
                    'name': 'This Month',
                    'type': 'date_range',
                    'days_ago': 30,
                    'target_folder': 'This Month'
                },
                {
                    'name': 'This Year',
                    'type': 'date_range',
                    'days_ago': 365,
                    'target_folder': 'This Year'
                },
                {
                    'name': 'Older',
                    'type': 'date_range',
                    'days_ago': 99999,
                    'target_folder': 'Older'
                }
            ]
        }
    
    def get_profile_rules(self, profile_name: str) -> List[Dict]:
        """Get rules for a specific profile."""
        return self.profiles.get(profile_name, [])
    
    def get_available_profiles(self) -> List[str]:
        """Get list of available profile names."""
        return list(self.profiles.keys())
    
    def get_default_rules(self) -> List[Dict]:
        """Get default rules (downloads profile)."""
        return self.get_profile_rules('downloads')
    
    def matches_rule(self, file_path: Path, rule: Dict) -> bool:
        """
        Check if a file matches a rule.
        
        Args:
            file_path: Path to file
            rule: Rule dictionary
            
        Returns:
            True if file matches rule
        """
        rule_type = rule.get('type', 'extension')
        
        if rule_type == 'extension':
            return self._matches_extension(file_path, rule)
        elif rule_type == 'name_pattern':
            return self._matches_name_pattern(file_path, rule)
        elif rule_type == 'date_range':
            return self._matches_date_range(file_path, rule)
        elif rule_type == 'size_range':
            return self._matches_size_range(file_path, rule)
        
        return False
    
    def _matches_extension(self, file_path: Path, rule: Dict) -> bool:
        """Check if file extension matches rule."""
        patterns = rule.get('patterns', [])
        file_ext = file_path.suffix.lower()
        return file_ext in patterns
    
    def _matches_name_pattern(self, file_path: Path, rule: Dict) -> bool:
        """Check if filename matches pattern."""
        patterns = rule.get('patterns', [])
        filename = file_path.name.lower()
        
        for pattern in patterns:
            if re.search(pattern.lower(), filename):
                return True
        return False
    
    def _matches_date_range(self, file_path: Path, rule: Dict) -> bool:
        """Check if file modification date is within range."""
        try:
            days_ago = rule.get('days_ago', 0)
            cutoff_date = datetime.now() - timedelta(days=days_ago)
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            return file_mtime >= cutoff_date
        except:
            return False
    
    def _matches_size_range(self, file_path: Path, rule: Dict) -> bool:
        """Check if file size is within range."""
        try:
            min_size = rule.get('min_size_bytes', 0)
            max_size = rule.get('max_size_bytes', float('inf'))
            file_size = file_path.stat().st_size
            return min_size <= file_size <= max_size
        except:
            return False
    
    def create_custom_rule(
        self,
        name: str,
        rule_type: str,
        patterns: List[str],
        target_folder: str
    ) -> Dict:
        """
        Create a custom rule.
        
        Args:
            name: Rule name
            rule_type: Type of rule (extension, name_pattern, etc.)
            patterns: List of patterns to match
            target_folder: Target folder name
            
        Returns:
            Rule dictionary
        """
        return {
            'name': name,
            'type': rule_type,
            'patterns': patterns,
            'target_folder': target_folder
        }
