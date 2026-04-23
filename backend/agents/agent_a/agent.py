"""
Agent A: Document Reader

Responsibilities:
- Parse PDF documents (digital and scanned)
- Extract structured fields using Z.AI GLM
- Store documents in Firebase Storage
- Write extracted data to Firestore for Agent B

Author: Chip/Azim
"""

from typing import Dict, List, Any
import os
from backend.agents.agent_a.parsers import parse_pdf
from backend.agents.agent_a.prompts import build_extraction_prompt
from backend.core.glm_client import GLMClient
from backend.core.storage import FirebaseStorageClient
from backend.core.firebase_client import FirestoreClient


class AgentA:
    """Document reader and field extraction agent"""

    def __init__(
        self,
        glm_client: GLMClient,
        storage_client: FirebaseStorageClient,
        firestore_client: FirestoreClient
    ):
        """
        Initialize Agent A with required clients

        Args:
            glm_client: Z.AI GLM API client for field extraction
            storage_client: Firebase Storage client for document storage
            firestore_client: Firestore client for database operations
        """
        self.glm = glm_client
        self.storage = storage_client
        self.db = firestore_client

    async def process_documents(
        self, project_id: str, documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Main processing pipeline for Agent A

        Args:
            project_id: Unique project identifier
            documents: List of document metadata with file paths

        Returns:
            Extracted fields dictionary
        """
        all_extracted_fields = []

        for doc in documents:
            try:
                file_path = doc.get("file_path")
                filename = doc.get("filename", os.path.basename(file_path))

                # 1. Parse PDF
                text = await self.parse_pdf(file_path)

                # 2. Extract fields using GLM
                fields = await self.extract_fields(text)

                # 3. Store document in Firebase Storage
                storage_path = f"projects/{project_id}/{filename}"
                storage_url = await self.storage.upload_file(
                    local_path=file_path,
                    remote_path=storage_path
                )

                # 4. Save document metadata to Firestore
                doc_id = await self.db.save_document(
                    project_id=project_id,
                    document_data={
                        "filename": filename,
                        "storage_path": storage_path,
                        "storage_url": storage_url,
                        "status": "processed"
                    }
                )

                # 5. Save extracted fields to Firestore
                fields_id = await self.db.save_extracted_fields(
                    project_id=project_id,
                    document_id=doc_id,
                    fields=fields
                )

                all_extracted_fields.append({
                    "document_id": doc_id,
                    "filename": filename,
                    "fields": fields,
                    "fields_id": fields_id
                })

            except Exception as e:
                print(f"Error processing document {doc.get('filename')}: {str(e)}")
                all_extracted_fields.append({
                    "filename": doc.get("filename"),
                    "error": str(e)
                })

        return {
            "project_id": project_id,
            "documents_processed": len(documents),
            "extracted_fields": all_extracted_fields
        }

    async def parse_pdf(self, file_path: str) -> str:
        """
        Parse PDF and extract text

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text content
        """
        return parse_pdf(file_path)

    async def extract_fields(self, text: str) -> Dict[str, Any]:
        """
        Extract structured fields from text using Z.AI GLM

        Args:
            text: Raw text from PDF

        Returns:
            Structured field dictionary with ≥10 fields
        """
        prompt = build_extraction_prompt(text)
        result = await self.glm.extract_json(prompt)

        return result

    async def store_document(self, file_path: str, project_id: str) -> str:
        """
        Upload document to Firebase Storage

        Args:
            file_path: Local file path
            project_id: Project identifier

        Returns:
            Firebase Storage URL
        """
        filename = os.path.basename(file_path)
        remote_path = f"projects/{project_id}/{filename}"
        return await self.storage.upload_file(file_path, remote_path)

    async def save_to_firestore(self, project_id: str, data: Dict[str, Any]) -> str:
        """
        Write extracted data to Firestore for Agent B

        Args:
            project_id: Project identifier
            data: Extracted fields

        Returns:
            Document ID in Firestore
        """
        return await self.db.save_extracted_fields(
            project_id=project_id,
            document_id=data.get("document_id"),
            fields=data
        )
