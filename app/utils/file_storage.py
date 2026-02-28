"""File storage utility for handling uploads."""

import os
import uuid
from pathlib import Path
from typing import Optional
import shutil

from fastapi import UploadFile


class FileStorageService:
    """Service for storing uploaded files locally."""

    def __init__(self, base_upload_dir: str = "uploads", base_url: str = ""):
        """
        Initialize file storage service.

        Args:
            base_upload_dir: Base directory for uploads (relative to project root)
            base_url: Base URL for serving files (e.g., "https://your-domain.com")
        """
        self.base_upload_dir = Path(base_upload_dir)
        self.base_url = base_url.rstrip("/") if base_url else ""

        # Ensure base directory exists
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)

    def get_subdir_path(self, subdir: str) -> Path:
        """Get full path for a subdirectory, creating it if needed."""
        subdir_path = self.base_upload_dir / subdir
        subdir_path.mkdir(parents=True, exist_ok=True)
        return subdir_path

    async def save_file(
        self,
        file: UploadFile,
        subdir: str = "",
        custom_filename: Optional[str] = None
    ) -> str:
        """
        Save an uploaded file to disk.

        Args:
            file: UploadFile from FastAPI
            subdir: Subdirectory within uploads (e.g., "logos", "documents")
            custom_filename: Optional custom filename (otherwise uses UUID)

        Returns:
            URL path to access the file
        """
        # Get file extension
        file_extension = Path(file.filename).suffix or ""

        # Generate filename
        if custom_filename:
            filename = custom_filename
        else:
            filename = f"{uuid.uuid4()}{file_extension}"

        # Get target directory
        if subdir:
            target_dir = self.get_subdir_path(subdir)
            relative_path = f"{subdir}/{filename}"
        else:
            target_dir = self.base_upload_dir
            relative_path = filename

        file_path = target_dir / filename

        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Return URL path
        if self.base_url:
            return f"{self.base_url}/uploads/{relative_path}"
        else:
            return f"/uploads/{relative_path}"

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file by its path.

        Args:
            file_path: Path or URL to the file

        Returns:
            True if deleted, False if not found
        """
        # Convert URL path to filesystem path
        if file_path.startswith("/uploads/"):
            relative_path = file_path.replace("/uploads/", "", 1)
            fs_path = self.base_upload_dir / relative_path
        elif file_path.startswith("http"):
            # Extract path from URL
            path_parts = file_path.split("/uploads/")
            if len(path_parts) > 1:
                relative_path = path_parts[1]
                fs_path = self.base_upload_dir / relative_path
            else:
                return False
        else:
            fs_path = self.base_upload_dir / file_path

        # Delete if exists
        if fs_path.exists() and fs_path.is_file():
            fs_path.unlink()
            return True

        return False

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        if file_path.startswith("/uploads/"):
            relative_path = file_path.replace("/uploads/", "", 1)
            fs_path = self.base_upload_dir / relative_path
        else:
            fs_path = self.base_upload_dir / file_path

        return fs_path.exists() and fs_path.is_file()


# Global instance
file_storage = FileStorageService(
    base_upload_dir="uploads",
    base_url=""  # Set via environment variable in production
)
