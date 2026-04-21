"""
Agent A: Document Reader

Responsibilities:
- Parse PDF documents (digital and scanned)
- Extract structured fields using GLM
- Store documents in MinIO
- Write extracted data to Redis for Agent B

Author: Chip/Azim
"""

from typing import Dict, List, Any


class AgentA:
    """Document reader and field extraction agent"""

    def __init__(self, glm_client, minio_client, redis_client):
        """
        Initialize Agent A with required clients

        Args:
            glm_client: GLM API client for field extraction
            minio_client: MinIO client for document storage
            redis_client: Redis client for state management
        """
        self.glm = glm_client
        self.minio = minio_client
        self.redis = redis_client

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
        extracted_fields = {
            "project_id": project_id,
            "documents_processed": len(documents),
            "fields": {}
        }

        for doc in documents:
            # TODO: Implement document processing
            # 1. Parse PDF using parsers.py
            # 2. Extract fields using prompts.py + GLM
            # 3. Store in MinIO
            # 4. Write to Redis
            pass

        return extracted_fields

    async def parse_pdf(self, file_path: str) -> str:
        """
        Parse PDF and extract text

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text content
        """
        # TODO: Implement using parsers.py
        # - Try pdfplumber first (digital PDFs)
        # - Fall back to PyMuPDF + Tesseract (scanned PDFs)
        pass

    async def extract_fields(self, text: str) -> Dict[str, Any]:
        """
        Extract structured fields from text using GLM

        Args:
            text: Raw text from PDF

        Returns:
            Structured field dictionary
        """
        # TODO: Implement using prompts.py + glm_client
        # Target fields (≥10):
        # - project_name, contractor, budget, start_date, end_date
        # - milestones, deliverables, risks, stakeholders, etc.
        pass

    async def store_document(self, file_path: str, project_id: str) -> str:
        """
        Upload document to MinIO

        Args:
            file_path: Local file path
            project_id: Project identifier

        Returns:
            MinIO object URL
        """
        # TODO: Implement using storage.py
        pass

    async def write_to_redis(self, project_id: str, data: Dict[str, Any]) -> None:
        """
        Write extracted data to Redis for Agent B

        Args:
            project_id: Project identifier
            data: Extracted fields
        """
        # TODO: Implement using redis_client
        # Key format: buildora:project:{project_id}:extracted_fields
        pass
