"""Filesystem service for file operations."""
import logging
import os
import shutil
from pathlib import Path
from typing import Protocol, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class FilesystemService(Protocol):
    """Protocol for filesystem operations."""
    
    def move_file(self, source_path: str, destination_path: str) -> bool:
        """
        Move a file from source to destination.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            
        Returns:
            True if successful, False otherwise
        """
        ...
    
    def move_directory(self, source_path: str, destination_path: str) -> bool:
        """
        Move a directory from source to destination.
        
        Args:
            source_path: Source directory path
            destination_path: Destination directory path
            
        Returns:
            True if successful, False otherwise
        """
        ...
    
    def get_media_path(self, media_type: str) -> str:
        """
        Get the media path for a given media type.
        
        Args:
            media_type: "movie" or "show"
            
        Returns:
            Path to the media directory
        """
        ...


class FilesystemServiceImpl:
    """Implementation of filesystem service."""
    
    def __init__(self):
        self.downloads_path = settings.downloads_path
        self.media_movies_path = settings.media_movies_path
        self.media_tvshows_path = settings.media_tvshows_path
        self.media_quarantine_path = settings.media_quarantine_path
    
    def move_file(self, source_path: str, destination_path: str) -> bool:
        """Move a file from source to destination."""
        try:
            if not os.path.exists(source_path):
                logger.error(f"Source file does not exist: {source_path}")
                return False
            
            if not os.path.isfile(source_path):
                logger.error(f"Source path is not a file: {source_path}")
                return False
            
            # Create destination directory if it doesn't exist
            dest_dir = os.path.dirname(destination_path)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
                logger.info(f"Created destination directory: {dest_dir}")
            
            # Move the file
            shutil.move(source_path, destination_path)
            logger.info(f"Moved file from {source_path} to {destination_path}")
            return True
        except Exception as e:
            logger.error(f"Error moving file from {source_path} to {destination_path}: {e}")
            return False
    
    def move_directory(self, source_path: str, destination_path: str) -> bool:
        """Move a directory from source to destination."""
        try:
            if not os.path.exists(source_path):
                logger.error(f"Source directory does not exist: {source_path}")
                return False
            
            if not os.path.isdir(source_path):
                logger.error(f"Source path is not a directory: {source_path}")
                return False
            
            # Create destination parent directory if it doesn't exist
            dest_parent = os.path.dirname(destination_path)
            if dest_parent and not os.path.exists(dest_parent):
                os.makedirs(dest_parent, exist_ok=True)
                logger.info(f"Created destination parent directory: {dest_parent}")
            
            # Move the directory
            shutil.move(source_path, destination_path)
            logger.info(f"Moved directory from {source_path} to {destination_path}")
            return True
        except Exception as e:
            logger.error(f"Error moving directory from {source_path} to {destination_path}: {e}")
            return False
    
    def get_media_path(self, media_type: str) -> str:
        """Get the media path for a given media type."""
        if media_type.lower() == "movie":
            return self.media_movies_path
        elif media_type.lower() == "show":
            return self.media_tvshows_path
        else:
            logger.warning(f"Unknown media type: {media_type}, defaulting to movies path")
            return self.media_movies_path

