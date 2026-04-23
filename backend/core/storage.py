"""
Firebase Storage Client

Handles document upload/download using Firebase Storage

Author: Chip/Azim
"""

import firebase_admin
from firebase_admin import credentials, storage
from typing import Optional
import os
from backend.core.config import get_settings


class FirebaseStorageClient:
    """Client for Firebase Storage operations"""

    def __init__(self):
        self.settings = get_settings()
        self._initialize_firebase()
        self.bucket = storage.bucket(self.settings.FIREBASE_STORAGE_BUCKET)

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
                    # Initialize with default credentials for local testing
                    firebase_admin.initialize_app()

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
        blob = self.bucket.blob(remote_path)

        # Auto-detect content type if not provided
        if content_type is None:
            if remote_path.endswith('.pdf'):
                content_type = 'application/pdf'
            elif remote_path.endswith('.jpg') or remote_path.endswith('.jpeg'):
                content_type = 'image/jpeg'
            elif remote_path.endswith('.png'):
                content_type = 'image/png'
            else:
                content_type = 'application/octet-stream'

        # Upload file
        blob.upload_from_filename(local_path, content_type=content_type)

        # Make publicly accessible (optional - adjust based on security needs)
        blob.make_public()

        return blob.public_url

    async def download_file(self, remote_path: str, local_path: str) -> str:
        """
        Download a file from Firebase Storage

        Args:
            remote_path: Remote path in Firebase Storage
            local_path: Local path to save file

        Returns:
            Local file path
        """
        blob = self.bucket.blob(remote_path)
        blob.download_to_filename(local_path)
        return local_path

    async def delete_file(self, remote_path: str) -> bool:
        """
        Delete a file from Firebase Storage

        Args:
            remote_path: Remote path in Firebase Storage

        Returns:
            True if deleted successfully
        """
        blob = self.bucket.blob(remote_path)
        blob.delete()
        return True

    async def file_exists(self, remote_path: str) -> bool:
        """
        Check if a file exists in Firebase Storage

        Args:
            remote_path: Remote path in Firebase Storage

        Returns:
            True if file exists
        """
        blob = self.bucket.blob(remote_path)
        return blob.exists()

    async def get_download_url(self, remote_path: str, expiration: int = 3600) -> str:
        """
        Get a signed download URL for a file

        Args:
            remote_path: Remote path in Firebase Storage
            expiration: URL expiration time in seconds (default 1 hour)

        Returns:
            Signed download URL
        """
        blob = self.bucket.blob(remote_path)
        url = blob.generate_signed_url(expiration=expiration)
        return url


# Global client instance
_storage_client: Optional[FirebaseStorageClient] = None


def get_storage_client() -> FirebaseStorageClient:
    """Get or create Firebase Storage client instance"""
    global _storage_client
    if _storage_client is None:
        _storage_client = FirebaseStorageClient()
    return _storage_client
