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
        self.is_mock = False
        self.mock_db = {"projects": {}, "documents": {}, "extracted_fields": {}, "alerts": {}, "reports": {}}
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK if not already initialized"""
        if not firebase_admin._apps:
            cred_path = self.settings.FIREBASE_CREDENTIALS
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
            else:
                if self.settings.DEBUG:
                    print(f"[Warning] Firebase credentials not found at {cred_path}")
                    print("[Warning] Running in mock mode for development")
                    self.is_mock = True
                else:
                    raise FileNotFoundError(f"Firebase credentials not found at {cred_path}")
        else:
            try:
                self.db = firestore.client()
            except Exception as e:
                print(f"[Warning] Failed to get Firestore client: {e}")
                self.is_mock = True

    # Project Operations
    async def create_project(self, project_data: Dict[str, Any]) -> str:
        """
        Create a new project

        Args:
            project_data: Project information

        Returns:
            Project ID
        """
        import uuid
        project_id = str(uuid.uuid4())
        
        if self.is_mock:
            project_data['created_at'] = datetime.now()
            project_data['updated_at'] = datetime.now()
            self.mock_db["projects"][project_id] = project_data
            return project_id

        project_data['created_at'] = firestore.SERVER_TIMESTAMP
        project_data['updated_at'] = firestore.SERVER_TIMESTAMP

        doc_ref = self.db.collection('projects').document()
        doc_ref.set(project_data)
        return doc_ref.id

    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        if self.is_mock:
            data = self.mock_db["projects"].get(project_id)
            if data:
                data_copy = data.copy()
                data_copy['id'] = project_id
                return data_copy
            return None

        doc = self.db.collection('projects').document(project_id).get()
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return None

    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update project fields"""
        if self.is_mock:
            if project_id in self.mock_db["projects"]:
                self.mock_db["projects"][project_id].update(updates)
                self.mock_db["projects"][project_id]['updated_at'] = datetime.now()
            return True

        updates['updated_at'] = firestore.SERVER_TIMESTAMP
        self.db.collection('projects').document(project_id).update(updates)
        return True

    async def list_projects(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all projects"""
        if self.is_mock:
            projects = []
            for pid, data in list(self.mock_db["projects"].items())[:limit]:
                data_copy = data.copy()
                data_copy['id'] = pid
                projects.append(data_copy)
            return projects

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
        import uuid
        doc_id = str(uuid.uuid4())
        
        if self.is_mock:
            document_data['project_id'] = project_id
            document_data['uploaded_at'] = datetime.now()
            self.mock_db["documents"][doc_id] = document_data
            return doc_id

        document_data['project_id'] = project_id
        document_data['uploaded_at'] = firestore.SERVER_TIMESTAMP

        doc_ref = self.db.collection('documents').document()
        doc_ref.set(document_data)
        return doc_ref.id

    async def get_documents(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a project"""
        if self.is_mock:
            return [
                {**d, 'id': did} 
                for did, d in self.mock_db["documents"].items() 
                if d.get('project_id') == project_id
            ]

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
        import uuid
        fields_id = str(uuid.uuid4())
        
        if self.is_mock:
            data = {
                'project_id': project_id,
                'document_id': document_id,
                'fields': fields,
                'extracted_at': datetime.now()
            }
            self.mock_db["extracted_fields"][fields_id] = data
            return fields_id

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
        if self.is_mock:
            return [
                {**d, 'id': did} 
                for did, d in self.mock_db["extracted_fields"].items() 
                if d.get('project_id') == project_id
            ]

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
        import uuid
        alert_id = str(uuid.uuid4())

        if self.is_mock:
            alert_data['project_id'] = project_id
            alert_data['created_at'] = datetime.now()
            alert_data['status'] = alert_data.get('status', 'active')
            self.mock_db["alerts"][alert_id] = alert_data
            return alert_id

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
        if self.is_mock:
            alerts = []
            for did, d in self.mock_db["alerts"].items():
                if d.get('project_id') == project_id:
                    if status and d.get('status') != status:
                        continue
                    alerts.append({**d, 'id': did})
            return alerts

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
        if self.is_mock:
            if alert_id in self.mock_db["alerts"]:
                self.mock_db["alerts"][alert_id]['status'] = status
                self.mock_db["alerts"][alert_id]['updated_at'] = datetime.now()
            return True

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
        import uuid
        report_id = str(uuid.uuid4())

        if self.is_mock:
            report_data['project_id'] = project_id
            report_data['generated_at'] = datetime.now()
            self.mock_db["reports"][report_id] = report_data
            return report_id

        report_data['project_id'] = project_id
        report_data['generated_at'] = firestore.SERVER_TIMESTAMP

        doc_ref = self.db.collection('reports').document()
        doc_ref.set(report_data)
        return doc_ref.id

    async def get_reports(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all reports for a project"""
        if self.is_mock:
            return [
                {**d, 'id': did} 
                for did, d in self.mock_db["reports"].items() 
                if d.get('project_id') == project_id
            ]

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
