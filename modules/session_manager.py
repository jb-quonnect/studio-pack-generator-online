"""
Studio Pack Generator Online - Session Manager

Manages temporary directories and session state for ephemeral file processing.
Each user session gets a unique temporary folder that is cleaned up after use.
"""

import os
import shutil
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class SessionState:
    """Holds state for a single user session."""
    
    # Temporary directory for this session
    temp_dir: str = ""
    
    # Subdirectories
    input_dir: str = ""      # For uploaded files
    output_dir: str = ""     # For generated pack
    assets_dir: str = ""     # For processed assets
    
    # Counter for generated files (for resource warning)
    files_generated: int = 0
    
    # Warning threshold
    file_warning_threshold: int = 500
    
    # Pack metadata
    pack_title: str = "Mon Pack"
    pack_description: str = ""
    
    # Processing options
    add_delay: bool = False
    night_mode: bool = False
    normalize_audio: bool = True
    
    # TTS settings
    tts_model: str = "fr_FR-siwis-medium"
    
    # Asset tracking: maps original path -> SHA1 filename
    asset_map: Dict[str, str] = field(default_factory=dict)
    
    # Node structure for story.json
    nodes: list = field(default_factory=list)


class SessionManager:
    """
    Manages temporary file storage for a user session.
    
    Creates isolated temp directories and handles cleanup.
    """
    
    def __init__(self):
        self._session: Optional[SessionState] = None
        self._base_temp_dir: Optional[str] = None
    
    @property
    def session(self) -> SessionState:
        """Get current session, creating one if needed."""
        if self._session is None:
            self.create_session()
        return self._session
    
    def create_session(self) -> SessionState:
        """
        Create a new session with a unique temporary directory.
        
        Returns:
            New SessionState with initialized directories
        """
        # Clean up any existing session
        if self._session is not None:
            self.cleanup_session()
        
        # Create base temp directory
        self._base_temp_dir = tempfile.mkdtemp(prefix="spg_")
        
        # Create subdirectories
        input_dir = os.path.join(self._base_temp_dir, "input")
        output_dir = os.path.join(self._base_temp_dir, "output")
        assets_dir = os.path.join(self._base_temp_dir, "output", "assets")
        
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(assets_dir, exist_ok=True)
        
        self._session = SessionState(
            temp_dir=self._base_temp_dir,
            input_dir=input_dir,
            output_dir=output_dir,
            assets_dir=assets_dir
        )
        
        logger.info(f"Created session in {self._base_temp_dir}")
        return self._session
    
    def cleanup_session(self) -> None:
        """
        Clean up the current session's temporary files.
        
        Removes all files and directories associated with the session.
        """
        if self._base_temp_dir and os.path.exists(self._base_temp_dir):
            try:
                shutil.rmtree(self._base_temp_dir)
                logger.info(f"Cleaned up session: {self._base_temp_dir}")
            except Exception as e:
                logger.error(f"Failed to cleanup session: {e}")
        
        self._session = None
        self._base_temp_dir = None
    
    def increment_file_count(self, count: int = 1) -> int:
        """
        Increment the generated file counter.
        
        Args:
            count: Number to add to counter
            
        Returns:
            New total count
        """
        self.session.files_generated += count
        return self.session.files_generated
    
    def is_over_threshold(self) -> bool:
        """
        Check if file count exceeds warning threshold.
        
        Returns:
            True if over threshold
        """
        return self.session.files_generated >= self.session.file_warning_threshold
    
    def get_warning_message(self) -> Optional[str]:
        """
        Get warning message if over threshold.
        
        Returns:
            Warning message or None
        """
        if self.is_over_threshold():
            return (
                f"⚠️ Attention: {self.session.files_generated} fichiers générés. "
                f"Seuil d'avertissement ({self.session.file_warning_threshold}) dépassé. "
                "Vérifiez que cela est intentionnel."
            )
        return None
    
    def save_uploaded_file(self, uploaded_file, subfolder: str = "") -> str:
        """
        Save an uploaded file to the session's input directory.
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            subfolder: Optional subfolder within input_dir
            
        Returns:
            Path to saved file
        """
        target_dir = self.session.input_dir
        if subfolder:
            target_dir = os.path.join(target_dir, subfolder)
            os.makedirs(target_dir, exist_ok=True)
        
        file_path = os.path.join(target_dir, uploaded_file.name)
        
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        logger.debug(f"Saved uploaded file: {file_path}")
        return file_path
    
    def register_asset(self, original_path: str, sha1_filename: str) -> None:
        """
        Register an asset in the session's asset map.
        
        Args:
            original_path: Original file path
            sha1_filename: SHA1-based filename in assets/
        """
        self.session.asset_map[original_path] = sha1_filename
    
    def get_asset_path(self, original_path: str) -> Optional[str]:
        """
        Get the SHA1-based asset path for an original file.
        
        Args:
            original_path: Original file path
            
        Returns:
            Path in assets/ or None if not registered
        """
        sha1_name = self.session.asset_map.get(original_path)
        if sha1_name:
            return f"assets/{sha1_name}"
        return None
    
    def get_output_zip_path(self) -> str:
        """
        Get the path for the output ZIP file.
        
        Returns:
            Path for output ZIP
        """
        safe_title = self.session.pack_title.replace(' ', '_')[:50]
        return os.path.join(self.session.temp_dir, f"{safe_title}.zip")


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    Get the global session manager instance.
    
    Returns:
        SessionManager singleton
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def reset_session_manager() -> SessionManager:
    """
    Reset the global session manager (cleanup and create new).
    
    Returns:
        New SessionManager instance
    """
    global _session_manager
    if _session_manager is not None:
        _session_manager.cleanup_session()
    _session_manager = SessionManager()
    return _session_manager
