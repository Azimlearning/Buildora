"""
Firebase Storage Client

Handles document upload/download using Firebase Storage

Author: Chip/Azim
"""

import firebase_admin
from firebase_admin import credentials, storage
from typing import Optional
import os
import atexit
import shutil
from datetime import timedelta
from backend.core.config import get_settings


class FirebaseStorageClient:
    """Client for Firebase Storage operations"""

    def __init__(self):
        self.settings = get_settings()
        self.is_mock = False
        self.mock_storage = {}
        self._initialize_firebase()
        if not self.is_mock:
            self.bucket = storage.bucket(self.settings.FIREBASE_STORAGE_BUCKET)
        else:
            # Register cleanup on exit for mock mode
            atexit.register(self._cleanup_mock_storage)

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        if not firebase_admin._apps:
            # Check if credentials file exists
            cred_path = self.settings.FIREBASE_CREDENTIALS
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': self.settings.FIREBASE_STORAGE_BUCKET
                })
            else:
                # For development without credentials
                if self.settings.DEBUG:
                    print(f"[Warning] Firebase credentials not found at {cred_path}")
                    print("[Warning] Running in mock mode for development")
                    self.is_mock = True
                else:
                    raise FileNotFoundError(f"Firebase credentials not found at {cred_path}")
        else:
            try:
                storage.bucket(self.settings.FIREBASE_STORAGE_BUCKET)
            except Exception as e:
                print(f"[Warning] Failed to get storage bucket: {e}")
                if self.settings.DEBUG:
                    self.is_mock = True
                else:
                    raise

    def _cleanup_mock_storage(self):
        """Clean up mock storage directory on process exit"""
        if os.path.exists("mock_storage"):
            shutil.rmtree("mock_storage", ignore_errors=True)

    async def upload_file(
        self,
        local_path: str,
        remote_path: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload a file to Firebase Storage

        Args:
            local_path: Local file path
            remote_path: Remote path in Firebase Storage (e.g., "projects/123/doc.pdf")
            content_type: MIME type (auto-detected if None)

        Returns:
            Public URL of uploaded file
        """
        if self.is_mock:
            import shutil
            import uuid
            os.makedirs("mock_storage", exist_ok=True)
            mock_url = f"mock_storage/{str(uuid.uuid4())}_{os.path.basename(local_path)}"
            shutil.copy2(local_path, mock_url)
            self.mock_storage[remote_path] = mock_url
            return f"http://localhost:8000/{mock_url}"

        try:
            blob = self.bucket.blob(remote_path)

            # Auto-detect content type if not provided
            if content_type is None:
                if remote_path.endswith('.pdf'):
                    content_type = 'application/pdf'
                elif remote_path.endswith(('.jpg', '.jpeg')):
                    content_type = 'image/jpeg'
                elif remote_path.endswith('.png'):
                    content_type = 'image/png'
                else:
                    content_type = 'application/octet-stream'

            blob.upload_from_filename(local_path, content_type=content_type)

            # Use signed URL instead of public — avoids exposing sensitive construction docs
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=1),
                method="GET"
            )
            return url
        except FileNotFoundError:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to upload file to {remote_path}: {e}")

    async def download_file(self, remote_path: str, local_path: str) -> str:
        """
        Download a file from Firebase Storage

        Args:
            remote_path: Remote path in Firebase Storage
            local_path: Local path to save file

        Returns:
            Local file path
        """
        if self.is_mock:
            import shutil
            if remote_path in self.mock_storage:
                shutil.copy2(self.mock_storage[remote_path], local_path)
            return local_path

        try:
            blob = self.bucket.blob(remote_path)
            blob.download_to_filename(local_path)
            return local_path
        except Exception as e:
            raise RuntimeError(f"Failed to download file {remote_path}: {e}")

    async def delete_file(self, remote_path: str) -> bool:
        """
        Delete a file from Firebase Storage

        Args:
            remote_path: Remote path in Firebase Storage

        Returns:
            True if deleted successfully
        """
        if self.is_mock:
            if remote_path in self.mock_storage:
                if os.path.exists(self.mock_storage[remote_path]):
                    os.remove(self.mock_storage[remote_path])
                del self.mock_storage[remote_path]
            return True

        try:
            blob = self.bucket.blob(remote_path)
            blob.delete()
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to delete file {remote_path}: {e}")

    async def file_exists(self, remote_path: str) -> bool:
        """
        Check if a file exists in Firebase Storage

        Args:
            remote_path: Remote path in Firebase Storage

        Returns:
            True if file exists
        """
        if self.is_mock:
            return remote_path in self.mock_storage

        try:
            blob = self.bucket.blob(remote_path)
            return blob.exists()
        except Exception as e:
            raise RuntimeError(f"Failed to check existence of {remote_path}: {e}")

    async def get_download_url(self, remote_path: str, expiration: int = 3600) -> str:
        """
        Get a signed download URL for a file

        Args:
            remote_path: Remote path in Firebase Storage
            expiration: URL expiration time in seconds (default 1 hour)

        Returns:
            Signed download URL
        """
        if self.is_mock:
            if remote_path in self.mock_storage:
                return f"http://localhost:8000/{self.mock_storage[remote_path]}"
            return ""

        try:
            blob = self.bucket.blob(remote_path)
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=1),
                method="GET"
            )
            return url
        except Exception as e:
            raise RuntimeError(f"Failed to generate signed URL for {remote_path}: {e}")


# Global client instance
_storage_client: Optional[FirebaseStorageClient] = None


def get_storage_client() -> FirebaseStorageClient:
    """Get or create Firebase Storage client instance"""
    global _storage_client
    if _storage_client is None:
        _storage_client = FirebaseStorageClient()
    return _storage_client
