"""
Profile Manager

Manages user-created and predefined organization profiles.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
import logging


logger = logging.getLogger(__name__)


class ProfileManager:
    """Manages organization profiles."""
    
    def __init__(self, profiles_dir: str = 'profiles'):
        """
        Initialize profile manager.
        
        Args:
            profiles_dir: Directory to store user profiles
        """
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        self.user_profiles: Dict[str, Dict] = {}
        self._load_user_profiles()
    
    def _load_user_profiles(self):
        """Load user-created profiles from disk."""
        try:
            for profile_file in self.profiles_dir.glob('*.json'):
                with open(profile_file, 'r') as f:
                    profile = json.load(f)
                    self.user_profiles[profile_file.stem] = profile
            
            logger.info(f"Loaded {len(self.user_profiles)} user profiles")
        except Exception as e:
            logger.error(f"Failed to load user profiles: {e}")
    
    def save_profile(self, name: str, profile: Dict) -> bool:
        """
        Save a user profile.
        
        Args:
            name: Profile name
            profile: Profile configuration
            
        Returns:
            True if successful
        """
        try:
            profile_file = self.profiles_dir / f"{name}.json"
            with open(profile_file, 'w') as f:
                json.dump(profile, f, indent=2)
            
            self.user_profiles[name] = profile
            logger.info(f"Profile saved: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save profile {name}: {e}")
            return False
    
    def load_profile(self, name: str) -> Optional[Dict]:
        """
        Load a profile by name.
        
        Args:
            name: Profile name
            
        Returns:
            Profile configuration or None
        """
        return self.user_profiles.get(name)
    
    def delete_profile(self, name: str) -> bool:
        """
        Delete a user profile.
        
        Args:
            name: Profile name
            
        Returns:
            True if successful
        """
        try:
            profile_file = self.profiles_dir / f"{name}.json"
            if profile_file.exists():
                profile_file.unlink()
            
            if name in self.user_profiles:
                del self.user_profiles[name]
            
            logger.info(f"Profile deleted: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete profile {name}: {e}")
            return False
    
    def get_all_profiles(self) -> List[str]:
        """Get list of all available profile names."""
        return list(self.user_profiles.keys())
    
    def export_profile(self, name: str, export_path: Path) -> bool:
        """
        Export a profile to a file.
        
        Args:
            name: Profile name
            export_path: Path to export file
            
        Returns:
            True if successful
        """
        profile = self.load_profile(name)
        if not profile:
            return False
        
        try:
            with open(export_path, 'w') as f:
                json.dump(profile, f, indent=2)
            logger.info(f"Profile exported: {name} -> {export_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export profile {name}: {e}")
            return False
    
    def import_profile(self, import_path: Path, name: str = None) -> bool:
        """
        Import a profile from a file.
        
        Args:
            import_path: Path to import file
            name: Profile name (optional, uses filename if not provided)
            
        Returns:
            True if successful
        """
        try:
            with open(import_path, 'r') as f:
                profile = json.load(f)
            
            if name is None:
                name = import_path.stem
            
            return self.save_profile(name, profile)
        except Exception as e:
            logger.error(f"Failed to import profile from {import_path}: {e}")
            return False
