"""
Firebase Firestore Client

Handles database operations using Firestore

Author: Chip/Azim
"""

from firebase_admin import firestore
from typing import Dict, Any, List, Optional
from datetime import datetime
import firebase_admin
from firebase_admin import credentials
import os
from backend.core.config import get_settings


class FirestoreClient:
    """Client for Firestore database operations"""

    def __init__(self):
        self.settings = get_settings()
        self._initialize_firebase()
        self.db = firestore.client()

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK if not already initialized"""
        if not firebase_admin._apps:
            cred_path = self.settings.FIREBASE_CREDENTIALS
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                if self.settings.DEBUG:
                    print(f"[Warning] Firebase credentials not found at {cred_path}")
                    print("[Warning] Running in mock mode for development")
                    firebase_admin.initialize_app()

    # Project Operations
    async def create_project(self, project_data: Dict[str, Any]) -> str:
        """
        Create a new project

        Args:
            project_data: Project information

        Returns:
            Project ID
        """
        project_data['created_at'] = firestore.SERVER_TIMESTAMP
        project_data['updated_at'] = firestore.SERVER_TIMESTAMP

        doc_ref = self.db.collection('projects').document()
        doc_ref.set(project_data)
        return doc_ref.id

    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        doc = self.db.collection('projects').document(project_id).get()
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return None

    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update project fields"""
        updates['updated_at'] = firestore.SERVER_TIMESTAMP
        self.db.collection('projects').document(project_id).update(updates)
        return True

    async def list_projects(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all projects"""
        docs = self.db.collection('projects').limit(limit).stream()
        projects = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            projects.append(data)
        return projects

    # Document Operations
    async def save_document(
        self,
        project_id: str,
        document_data: Dict[str, Any]
    ) -> str:
        """
        Save a document to a project

        Args:
            project_id: Project ID
            document_data: Document information (filename, storage_path, etc.)

        Returns:
            Document ID
        """
        document_data['project_id'] = project_id
        document_data['uploaded_at'] = firestore.SERVER_TIMESTAMP

        doc_ref = self.db.collection('documents').document()
        doc_ref.set(document_data)
        return doc_ref.id

    async def get_documents(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a project"""
        docs = self.db.collection('documents').where(
            'project_id', '==', project_id
        ).stream()

        documents = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            documents.append(data)
        return documents

    # Extracted Fields Operations
    async def save_extracted_fields(
        self,
        project_id: str,
        document_id: str,
        fields: Dict[str, Any]
    ) -> str:
        """
        Save extracted fields from a document

        Args:
            project_id: Project ID
            document_id: Document ID
            fields: Extracted field data

        Returns:
            Fields record ID
        """
        data = {
            'project_id': project_id,
            'document_id': document_id,
            'fields': fields,
            'extracted_at': firestore.SERVER_TIMESTAMP
        }

        doc_ref = self.db.collection('extracted_fields').document()
        doc_ref.set(data)
        return doc_ref.id

    async def get_extracted_fields(
        self,
        project_id: str
    ) -> List[Dict[str, Any]]:
        """Get all extracted fields for a project"""
        docs = self.db.collection('extracted_fields').where(
            'project_id', '==', project_id
        ).stream()

        fields = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            fields.append(data)
        return fields

    # Alert Operations
    async def create_alert(
        self,
        project_id: str,
        alert_data: Dict[str, Any]
    ) -> str:
        """
        Create an alert

        Args:
            project_id: Project ID
            alert_data: Alert information (type, severity, message, etc.)

        Returns:
            Alert ID
        """
        alert_data['project_id'] = project_id
        alert_data['created_at'] = firestore.SERVER_TIMESTAMP
        alert_data['status'] = alert_data.get('status', 'active')

        doc_ref = self.db.collection('alerts').document()
        doc_ref.set(alert_data)
        return doc_ref.id

    async def get_alerts(
        self,
        project_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get alerts for a project, optionally filtered by status"""
        query = self.db.collection('alerts').where('project_id', '==', project_id)

        if status:
            query = query.where('status', '==', status)

        docs = query.stream()
        alerts = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            alerts.append(data)
        return alerts

    async def update_alert_status(self, alert_id: str, status: str) -> bool:
        """Update alert status (active, resolved, dismissed)"""
        self.db.collection('alerts').document(alert_id).update({
            'status': status,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        return True

    # Report Operations
    async def save_report(
        self,
        project_id: str,
        report_data: Dict[str, Any]
    ) -> str:
        """
        Save a generated report

        Args:
            project_id: Project ID
            report_data: Report content and metadata

        Returns:
            Report ID
        """
        report_data['project_id'] = project_id
        report_data['generated_at'] = firestore.SERVER_TIMESTAMP

        doc_ref = self.db.collection('reports').document()
        doc_ref.set(report_data)
        return doc_ref.id

    async def get_reports(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all reports for a project"""
        docs = self.db.collection('reports').where(
            'project_id', '==', project_id
        ).stream()

        reports = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            reports.append(data)
        return reports


# Global client instance
_firestore_client: Optional[FirestoreClient] = None


def get_firestore_client() -> FirestoreClient:
    """Get or create Firestore client instance"""
    global _firestore_client
    if _firestore_client is None:
        _firestore_client = FirestoreClient()
    return _firestore_client
