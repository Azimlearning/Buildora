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
import time
from backend.agents.contracts import (
    AgentAInput,
    AgentAOutput,
    DocumentMetadata,
    ProcessingStatus,
)
from backend.agents.agent_a.parsers import parse_document
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
    ) -> AgentAOutput:
        """
        Main processing pipeline for Agent A

        Args:
            project_id: Unique project identifier
            documents: List of document metadata with file paths

        Returns:
            AgentAOutput with processing results and metadata
        """
        start_time = time.time()
        all_extracted_fields = []
        storage_urls = []
        errors = []
        documents_failed = 0

        for doc in documents:
            try:
                file_path = doc.get("file_path")
                filename = doc.get("filename", os.path.basename(file_path))

                # 1. Parse PDF
                text = await self.parse_pdf(file_path)

                # 2. Extract fields using GLM/heuristic
                fields = await self.extract_fields(text)

                # 3. Store document in Firebase Storage (non-fatal — extraction proceeds even if this fails)
                storage_path = f"projects/{project_id}/{filename}"
                storage_url = None
                try:
                    storage_url = await self.storage.upload_file(
                        local_path=file_path,
                        remote_path=storage_path
                    )
                    storage_urls.append(storage_url)
                except Exception as storage_err:
                    print(f"[Agent A] Storage upload skipped for {filename}: {storage_err}")
                    storage_url = f"local://{file_path}"  # fallback local reference

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
                error_msg = f"Error processing document {doc.get('filename')}: {str(e)}"
                print(error_msg)
                errors.append(error_msg)
                documents_failed += 1
                all_extracted_fields.append({
                    "filename": doc.get("filename"),
                    "error": str(e)
                })

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Update project with extracted metadata from first document
        if all_extracted_fields:
            # Merge fields from all successfully processed docs (first doc takes priority)
            merged = {}
            for ef in reversed(all_extracted_fields):
                f = ef.get("fields", {})
                if f and not ef.get("error"):
                    merged.update(f)

            update_data = {}
            # Map extracted fields to project-level keys
            field_map = {
                "contractor": "contractor",
                "client": "client",
                "location": "location",
                "cidb_grade": "cidb_grade",
                "cidb_registration": "cidb_registration",
                "scope": "scope",
                "start_date": "start_date",
                "end_date": "end_date",
                "contract_value": "contract_value",
                "project_type": "project_type",
                "documents_found": "documents_found",
                "_extraction_method": "_extraction_method",
                "_confidence_score": "_confidence_score",
            }
            for src_key, dst_key in field_map.items():
                val = merged.get(src_key)
                # Skip falsy / placeholder values
                if val is None or val == "" or val == 0 or val == 0.0:
                    continue
                if isinstance(val, list) and len(val) == 0:
                    continue
                if val in ("Unknown Contractor", "Unnamed Project"):
                    continue
                update_data[dst_key] = val

            # Override project name only if we got a real one
            extracted_name = merged.get("project_name", "")
            if extracted_name and extracted_name not in ("Unnamed Project", ""):
                update_data["project_name_extracted"] = extracted_name

            # Always mark as processed
            update_data["status"] = "processed"

            if update_data:
                try:
                    await self.db.update_project(project_id, update_data)
                    print(f"[Agent A] Updated project with extracted fields: {list(update_data.keys())}")
                except Exception as e:
                    print(f"[Agent A] Failed to update project metadata: {e}")

        return AgentAOutput(
            project_id=project_id,
            status=ProcessingStatus.COMPLETED if documents_failed == 0 else ProcessingStatus.PARTIAL,
            documents_processed=len(documents) - documents_failed,
            documents_failed=documents_failed,
            processing_time_ms=processing_time_ms,
            extracted_fields=all_extracted_fields,
            storage_urls=storage_urls,
            errors=errors,
            metadata={"total_documents": len(documents)}
        )

    async def parse_pdf(self, file_path: str) -> str:
        """
        Parse PDF and extract text

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text content
        """
        return parse_document(file_path)

    async def extract_fields(self, text: str) -> Dict[str, Any]:
        """
        Extract structured fields from text using Z.AI GLM.
        Falls back to regex-based heuristics when GLM is unavailable.

        Args:
            text: Raw text from PDF

        Returns:
            Structured field dictionary with ≥10 fields and a confidence score
        """
        prompt = build_extraction_prompt(text)
        result = await self.glm.extract_json(prompt)

        # If GLM returned empty (fallback mode or 401), use heuristic extraction
        if not result or result.get("parse_error"):
            result = self._heuristic_extract(text)
        else:
            # Add confidence score for LLM extraction if not present
            if "_confidence_score" not in result:
                result["_confidence_score"] = 0.85  # High confidence for LLM

        return result
    def _heuristic_extract(self, text: str) -> Dict[str, Any]:
        """
        Rule-based field extraction when GLM is unavailable.
        Extracts common construction document fields via regex patterns.
        """
        import re
        t = text or ""

        def find(pattern, default=""):
            try:
                m = re.search(pattern, t, re.IGNORECASE | re.MULTILINE)
                if not m:
                    return default
                # Use group(1) if there's a capture group, else group(0)
                try:
                    return m.group(1).strip()
                except IndexError:
                    return m.group(0).strip()
            except re.error:
                return default

        def find_all(pattern):
            try:
                return [m.strip() for m in re.findall(pattern, t, re.IGNORECASE)]
            except re.error:
                return []

        # Project name — look for "Project:" or "Projek:" prefixes
        project_name = (
            find(r"(?:project|projek)\s*(?:name|nama)?\s*[:\-]\s*(.+?)(?:\n|,|$)") or
            find(r"(?:tajuk|title)\s*[:\-]\s*(.+?)(?:\n|,|$)") or
            find(r"^(.{10,60})\n", "Unnamed Project")
        )

        # Contractor / company — wrap SDN BHD match in a capture group
        contractor = (
            find(r"(?:contractor|kontraktor|syarikat)\s*[:\-]\s*(.+?)(?:\n|,|$)") or
            find(r"(?:company|firma)\s*[:\-]\s*(.+?)(?:\n|,|$)") or
            find(r"([A-Z][A-Za-z\s]+(?:SDN\.?\s*BHD\.?|Sdn\.?\s*Bhd\.?))", "Unknown Contractor")
        )

        # Dates
        dates = find_all(r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b")
        start_date = dates[0] if dates else ""
        end_date = dates[-1] if len(dates) > 1 else ""

        # Money / budget
        budget_raw = find(r"(?:budget|nilai|contract\s*value|nilai\s*kontrak)\s*[:\-]?\s*(?:RM\s*)?([\d,]+(?:\.\d+)?)")
        try:
            contract_value = float(budget_raw.replace(",", "")) if budget_raw else 0.0
        except ValueError:
            contract_value = 0.0

        # CIDB grade
        cidb_grade = find(r"\b(G[1-7])\b", "G5")

        # Location
        location = (
            find(r"(?:location|lokasi|alamat|address)\s*[:\-]\s*(.+?)(?:\n|,|$)") or
            find(r"(Kuala Lumpur|Selangor|Johor|Penang|Sabah|Sarawak)", "Malaysia")
        )

        # Scope / type
        scope = (
            find(r"(?:scope|skop|description|penerangan)\s*[:\-]\s*(.+?)(?:\n|\.|,|$)") or
            find(r"((?:pembinaan|construction|renovation|development)\s+.{5,50})", "General Construction")
        )

        # Project type — wrap in capture group
        project_type = find(r"(residential|commercial|industrial|mixed|education|public)", "general")

        # Document types found in the text
        doc_keywords = []
        for kw in ["cover letter", "surat iringan", "land title", "hakmilik", "geotechnical",
                   "traffic", "assessment", "cukai", "feasibility", "survey", "earthwork",
                   "permit", "compliance", "inspection", "certificate", "approval"]:
            if kw.lower() in t.lower():
                doc_keywords.append(kw)

        return {
            "project_name": project_name,
            "contractor": contractor,
            "client": find(r"(?:client|pelanggan|owner|pemilik)\s*[:\-]\s*(.+?)(?:\n|,|$)", ""),
            "start_date": start_date,
            "end_date": end_date,
            "contract_value": contract_value,
            "cidb_grade": cidb_grade,
            "cidb_registration": find(r"(?:CIDB|cidb)\s*(?:no\.?|registration|nombor)?\s*[:\-]?\s*(\w{6,20})", ""),
            "location": location,
            "scope": scope,
            "project_type": project_type,
            "documents_found": doc_keywords,
            "_extraction_method": "heuristic_fallback",
            "_confidence_score": 0.40,  # Lower confidence for heuristic extraction
        }

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
