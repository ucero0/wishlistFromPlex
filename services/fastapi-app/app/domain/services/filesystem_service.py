"""Filesystem service for file operations."""
import logging
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
    
    def get_quarantine_path(self) -> str:
        """
        Get the quarantine path for downloaded files.
        
        Returns:
            Path to the quarantine directory
        """
        ...
    
    def build_path(self, *path_parts: str) -> str:
        """
        Build a path from multiple parts.
        
        Args:
            *path_parts: Path components to join
            
        Returns:
            Joined path string
        """
        ...
    
    def path_exists(self, path: str) -> bool:
        """
        Check if a path exists.
        
        Args:
            path: Path to check
            
        Returns:
            True if path exists, False otherwise
        """
        ...
    
    def is_file(self, path: str) -> bool:
        """
        Check if a path is a file.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is a file, False otherwise
        """
        ...
    
    def is_directory(self, path: str) -> bool:
        """
        Check if a path is a directory.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is a directory, False otherwise
        """
        ...
    
    def get_quarantine_file_path(self, filename: str) -> str:
        """
        Get the full path for a file in the quarantine directory.
        
        Args:
            filename: Name of the file
            
        Returns:
            Full path to the file in quarantine
        """
        ...
    
    def get_media_destination_path(self, media_type: str, filename: str) -> str:
        """
        Get the destination path for a media file based on type.
        
        Args:
            media_type: "movie" or "show"
            filename: Name of the file or directory
            
        Returns:
            Full destination path
        """
        ...
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        ...
    
    def delete_directory(self, directory_path: str) -> bool:
        """
        Delete a directory and all its contents.
        
        Args:
            directory_path: Path to the directory to delete
            
        Returns:
            True if successful, False otherwise
        """
        ...
    
    def move(self, source_path: str, destination_path: str) -> bool:
        """
        Move a file or directory from source to destination.
        Automatically handles both files and directories.
        
        Args:
            source_path: Source file or directory path
            destination_path: Destination file or directory path
            
        Returns:
            True if successful, False otherwise
        """
        ...
    
    def delete(self, path: str) -> bool:
        """
        Delete a file or directory.
        Automatically handles both files and directories.
        
        Args:
            path: Path to the file or directory to delete
            
        Returns:
            True if successful, False otherwise
        """
        ...
    
    def remove_non_media_files(self, path: str) -> int:
        """
        Remove all files that are not video media or subtitle files.
        Recursively processes directories.
        
        Args:
            path: Path to the file or directory to process
            
        Returns:
            Number of files removed
        """
        ...


class FilesystemServiceImpl:
    """Implementation of filesystem service."""
    
    def __init__(self):
        self.downloads_path = Path(settings.container_plex_media_path)
        self.media_movies_path = Path(settings.container_plex_media_path) / "movies"
        self.media_tvshows_path = Path(settings.container_plex_media_path) / "tvshows"
        self.media_quarantine_path = Path(settings.container_deluge_quarantine_path)
    
    def move_file(self, source_path: str, destination_path: str) -> bool:
        """Move a file from source to destination."""
        try:
            source = Path(source_path)
            destination = Path(destination_path)
            
            if not source.exists():
                logger.error(f"Source file does not exist: {source_path}")
                return False
            
            if not source.is_file():
                logger.error(f"Source path is not a file: {source_path}")
                return False
            
            # Create destination directory if it doesn't exist
            if not destination.parent.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created destination directory: {destination.parent}")
            
            # Move the file
            shutil.move(str(source), str(destination))
            logger.info(f"Moved file from {source_path} to {destination_path}")
            return True
        except Exception as e:
            logger.error(f"Error moving file from {source_path} to {destination_path}: {e}")
            return False
    
    def move_directory(self, source_path: str, destination_path: str) -> bool:
        """Move a directory from source to destination."""
        try:
            source = Path(source_path)
            destination = Path(destination_path)
            
            if not source.exists():
                logger.error(f"Source directory does not exist: {source_path}")
                return False
            
            if not source.is_dir():
                logger.error(f"Source path is not a directory: {source_path}")
                return False
            
            # Create destination parent directory if it doesn't exist
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.parent.exists():
                logger.info(f"Created destination parent directory: {destination.parent}")
            
            # Move the directory
            shutil.move(str(source), str(destination))
            logger.info(f"Moved directory from {source_path} to {destination_path}")
            return True
        except Exception as e:
            logger.error(f"Error moving directory from {source_path} to {destination_path}: {e}")
            return False
    
    def get_media_path(self, media_type: str) -> str:
        """Get the media path for a given media type."""
        if media_type.lower() == "movie":
            return str(self.media_movies_path)
        elif media_type.lower() == "show":
            return str(self.media_tvshows_path)
        else:
            logger.warning(f"Unknown media type: {media_type}, defaulting to movies path")
            return str(self.media_movies_path)
    
    def get_quarantine_path(self) -> str:
        """Get the quarantine path for downloaded files."""
        return str(self.media_quarantine_path)
    
    def build_path(self, *path_parts: str) -> str:
        """Build a path from multiple parts."""
        return str(Path(*path_parts))
    
    def path_exists(self, path: str) -> bool:
        """Check if a path exists."""
        return Path(path).exists()
    
    def is_file(self, path: str) -> bool:
        """Check if a path is a file."""
        return Path(path).is_file()
    
    def is_directory(self, path: str) -> bool:
        """Check if a path is a directory."""
        return Path(path).is_dir()
    
    def get_quarantine_file_path(self, filename: str) -> str:
        """Get the full path for a file in the quarantine directory."""
        return str(self.media_quarantine_path / filename)
    
    def get_media_destination_path(self, media_type: str, filename: str) -> str:
        """Get the destination path for a media file based on type."""
        destination_dir = Path(self.get_media_path(media_type))
        return str(destination_dir / filename)
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file."""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"File does not exist: {file_path}")
                return False
            
            if not path.is_file():
                logger.error(f"Path is not a file: {file_path}")
                return False
            
            path.unlink()
            logger.info(f"Deleted file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def delete_directory(self, directory_path: str) -> bool:
        """Delete a directory and all its contents."""
        try:
            path = Path(directory_path)
            if not path.exists():
                logger.warning(f"Directory does not exist: {directory_path}")
                return False
            
            if not path.is_dir():
                logger.error(f"Path is not a directory: {directory_path}")
                return False
            
            shutil.rmtree(path)
            logger.info(f"Deleted directory: {directory_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting directory {directory_path}: {e}")
            return False
    
    def _validate_source_path(self, source: Path, source_path: str) -> bool:
        """
        Validate that source path exists and is a file or directory.
        
        Args:
            source: Path object for the source
            source_path: Original source path string for logging
            
        Returns:
            True if valid, False otherwise
        """
        if not source.exists():
            logger.error(f"Source path does not exist: {source_path}")
            return False
        
        if not source.is_file() and not source.is_dir():
            logger.error(f"Source path is neither a file nor a directory: {source_path}")
            return False
        
        return True
    
    def _move_directory(self, source: Path, destination: Path, source_path: str, destination_path: str) -> bool:
        """
        Move a directory from source to destination.
        
        Args:
            source: Source Path object
            destination: Destination Path object
            source_path: Original source path string for logging
            destination_path: Original destination path string for logging
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create destination parent directory if it doesn't exist
            if not destination.parent.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created destination directory: {destination.parent}")
            
            # Move the directory
            shutil.move(str(source), str(destination))
            logger.info(f"Moved directory from {source_path} to {destination_path}")
            return True
        except Exception as e:
            logger.error(f"Error moving directory from {source_path} to {destination_path}: {e}")
            return False
    
    def move(self, source_path: str, destination_path: str) -> bool:
        """Move a file or directory from source to destination. Automatically handles both files and directories."""
        try:
            source = Path(source_path)
            destination = Path(destination_path)
            
            if not self._validate_source_path(source, source_path):
                return False
            
            # Determine if source is a file or directory
            is_file = source.is_file()
            is_dir = source.is_dir()
            
            if not is_file and not is_dir:
                logger.error(f"Source path is neither a file nor a directory: {source_path}")
                return False
            
            # Create destination directory if it doesn't exist
            if not destination.parent.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created destination directory: {destination.parent}")
            
            # Move the file or directory
            shutil.move(str(source), str(destination))
            item_type = "file" if is_file else "directory"
            logger.info(f"Moved {item_type} from {source_path} to {destination_path}")
            return True
        except Exception as e:
            logger.error(f"Error moving from {source_path} to {destination_path}: {e}")
            return False
    
    def delete(self, path: str) -> bool:
        """Delete a file or directory. Automatically handles both files and directories."""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                logger.warning(f"Path does not exist: {path}")
                return False
            
            # Determine if path is a file or directory
            is_file = path_obj.is_file()
            is_dir = path_obj.is_dir()
            
            if not is_file and not is_dir:
                logger.error(f"Path is neither a file nor a directory: {path}")
                return False
            
            # Delete based on type
            if is_file:
                path_obj.unlink()
                logger.info(f"Deleted file: {path}")
            else:
                shutil.rmtree(path_obj)
                logger.info(f"Deleted directory: {path}")
            
            return True
        except Exception as e:
            logger.error(f"Error deleting {path}: {e}")
            return False
    
    def remove_non_media_files(self, path: str) -> int:
        """
        Remove all files that are not video media or subtitle files.
        Recursively processes directories.
        
        Args:
            path: Path to the file or directory to process
            
        Returns:
            Number of files removed
        """
        # Define allowed extensions
        video_extensions = {
            '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v',
            '.mpg', '.mpeg', '.3gp', '.ogv', '.ts', '.m2ts', '.mts', '.vob',
            '.divx', '.xvid', '.asf', '.rm', '.rmvb', '.f4v', '.mxf'
        }
        subtitle_extensions = {
            '.srt', '.vtt', '.ass'
        }
        allowed_extensions = video_extensions | subtitle_extensions
        
        removed_count = 0
        
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                logger.warning(f"Path does not exist: {path}")
                return 0
            
            if path_obj.is_file():
                # Single file: check if it's a media file
                file_ext = path_obj.suffix.lower()
                if file_ext not in allowed_extensions:
                    logger.info(f"Removing non-media file: {path}")
                    if self.delete_file(path):
                        removed_count = 1
            elif path_obj.is_dir():
                # Directory: recursively process all files
                for file_path in path_obj.rglob('*'):
                    if file_path.is_file():
                        file_ext = file_path.suffix.lower()
                        
                        if file_ext not in allowed_extensions:
                            logger.info(f"Removing non-media file: {file_path}")
                            if self.delete_file(str(file_path)):
                                removed_count += 1
            else:
                logger.error(f"Path is neither a file nor a directory: {path}")
                return 0
            
            logger.info(f"Removed {removed_count} non-media file(s) from {path}")
            return removed_count
        except Exception as e:
            logger.error(f"Error removing non-media files from {path}: {e}")
            return removed_count

