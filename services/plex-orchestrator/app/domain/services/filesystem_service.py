"""Filesystem service contract for file operations."""
from typing import Protocol

from app.domain.models.disk_usage import DiskUsageStats


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
    
    def get_path_size_bytes(self, path: str) -> int:
        """Total size in bytes of a file or directory tree."""
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
    
    def list_video_files(self, path: str) -> list[str]:
        """
        List video file paths under a file or directory (recursive for directories).

        Returns absolute/normalized paths as strings usable with move/rename helpers.
        """
        ...

    def resolve_access_path(self, path: str) -> str:
        """
        Resolve a Plex/host or quarantine path to a local path for I/O in this process.

        In Docker, Plex library paths like ``/plex2/...`` map under ``CONTAINER_HOST_FS_PREFIX``.
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

    def copy_file(self, source_path: str, destination_path: str) -> bool:
        """Copy a file from source to destination."""
        ...

    def copy_directory(self, source_path: str, destination_path: str) -> bool:
        """Copy a directory tree from source to destination."""
        ...

    def copy(self, source_path: str, destination_path: str) -> bool:
        """Copy a file or directory from source to destination."""
        ...

    def explain_move_failure(self, source_path: str, destination_path: str) -> str:
        """Explain why a move would fail (for ingest error reporting; does not move)."""
        ...

    def explain_copy_failure(self, source_path: str, destination_path: str) -> str:
        """Explain why a copy would fail (for ingest error reporting; does not copy)."""
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

    def get_volume_root(self, path: str) -> str:
        """
        Root of the volume or mount that contains this path.

        On Windows this is typically a drive root (e.g. ``C:\\``) or a UNC share root.
        On POSIX it is the mount point (e.g. ``/`` or ``/mnt/data``).

        Args:
            path: Any path under that volume; may be a file, directory, or a path whose
                parents exist (the nearest existing ancestor is used).

        Returns:
            Normalized volume/mount root path string.

        Raises:
            ValueError: If neither the path nor any parent path exists on disk.
        """
        ...

    def get_free_space_bytes(self, path: str) -> int:
        """
        Free space in bytes on the filesystem that contains the given path.

        Args:
            path: Any path on that filesystem (file or directory, or path with existing parent).

        Returns:
            Number of free bytes reported by the OS for that volume/mount.

        Raises:
            ValueError: If neither the path nor any parent path exists on disk.
        """
        ...

    def get_disk_usage(self, path: str) -> DiskUsageStats:
        """
        Total, used, and free bytes on the filesystem that contains the given path.

        Raises:
            ValueError: If neither the path nor any parent path exists on disk.
        """
        ...


