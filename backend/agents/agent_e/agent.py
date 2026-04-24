"""
Agent E: Output Generation
===========================
Agent E generates professional reports and exports:
  1. PDF Project Report (branded, comprehensive)
  2. XLSX Cost Tracker (detailed breakdown)
  3. Compliance Summary Report
  4. Timeline Gantt Chart (optional)

Workflow:
  1. Read project state from Firestore (all agent outputs)
  2. Generate branded PDF report with:
     - Project overview
     - Extracted fields summary
     - Compliance score and gaps
     - Alerts and recommendations
  3. Generate XLSX cost tracker with:
     - Budget breakdown
     - Cost variance analysis
     - Timeline tracking
  4. Upload reports to Firebase Storage
  5. Return download URLs

Author: Chip/Azim
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from backend.agents.contracts import (
    AgentEInput,
    AgentEOutput,
    ReportMetadata,
    ProcessingStatus,
)
from backend.agents.agent_e.pdf_generator import ReportGenerator
from backend.agents.agent_e.excel_generator import ExcelGenerator
from backend.core.firebase_client import FirestoreClient
from backend.core.storage import FirebaseStorageClient

logger = logging.getLogger(__name__)


class AgentE:
    """
    Output Generation agent.

    Generates professional PDF and XLSX reports from project data.
    """

    def __init__(
        self,
        firestore_client: FirestoreClient,
        storage_client: FirebaseStorageClient,
    ):
        """
        Args:
            firestore_client: Firestore client for reading project data.
            storage_client:   Firebase Storage client for uploading reports.
        """
        self.db = firestore_client
        self.storage = storage_client
        self.pdf_generator = ReportGenerator()
        self.excel_generator = ExcelGenerator()

    # ── Main entry point ─────────────────────────────────────

    async def generate_reports(
        self,
        project_id: str,
        report_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate all requested reports for a project.

        Args:
            project_id:    Firestore project ID.
            report_types:  List of report types to generate.
                          Options: ["pdf", "xlsx", "compliance", "timeline"]
                          Default: ["pdf", "xlsx"]

        Returns:
            Dict with report URLs and metadata.
        """
        logger.info(f"[Agent E] Generating reports for project {project_id}")

        report_types = report_types or ["pdf", "xlsx"]
        results = {
            "project_id": project_id,
            "generated_at": datetime.utcnow().isoformat(),
            "reports": {},
            "errors": []
        }

        # ── Step 1: Load project data ────────────────────────
        try:
            project_data = await self._load_project_data(project_id)
        except Exception as e:
            error_msg = f"Failed to load project data: {str(e)}"
            logger.error(f"[Agent E] {error_msg}")
            results["errors"].append(error_msg)
            return results

        # ── Step 2: Generate PDF report ──────────────────────
        if "pdf" in report_types:
            try:
                pdf_path = await self._generate_pdf_report(project_id, project_data)
                pdf_url = await self.storage.upload_file(
                    pdf_path,
                    f"reports/{project_id}/project_report.pdf"
                )
                results["reports"]["pdf"] = {
                    "url": pdf_url,
                    "filename": "project_report.pdf",
                    "type": "application/pdf"
                }
                logger.info(f"[Agent E] PDF report generated: {pdf_url}")
            except Exception as e:
                error_msg = f"PDF generation failed: {str(e)}"
                logger.error(f"[Agent E] {error_msg}")
                results["errors"].append(error_msg)

        # ── Step 3: Generate XLSX cost tracker ───────────────
        if "xlsx" in report_types:
            try:
                xlsx_path = await self._generate_xlsx_report(project_id, project_data)
                xlsx_url = await self.storage.upload_file(
                    xlsx_path,
                    f"reports/{project_id}/cost_tracker.xlsx"
                )
                results["reports"]["xlsx"] = {
                    "url": xlsx_url,
                    "filename": "cost_tracker.xlsx",
                    "type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                }
                logger.info(f"[Agent E] XLSX report generated: {xlsx_url}")
            except Exception as e:
                error_msg = f"XLSX generation failed: {str(e)}"
                logger.error(f"[Agent E] {error_msg}")
                results["errors"].append(error_msg)

        # ── Step 4: Generate compliance summary ──────────────
        if "compliance" in report_types:
            try:
                compliance_path = await self._generate_compliance_summary(
                    project_id, project_data
                )
                compliance_url = await self.storage.upload_file(
                    compliance_path,
                    f"reports/{project_id}/compliance_summary.pdf"
                )
                results["reports"]["compliance"] = {
                    "url": compliance_url,
                    "filename": "compliance_summary.pdf",
                    "type": "application/pdf"
                }
                logger.info(f"[Agent E] Compliance summary generated: {compliance_url}")
            except Exception as e:
                error_msg = f"Compliance summary generation failed: {str(e)}"
                logger.error(f"[Agent E] {error_msg}")
                results["errors"].append(error_msg)

        # ── Step 5: Save report metadata to Firestore ────────
        await self._save_report_metadata(project_id, results)

        logger.info(
            f"[Agent E] Generated {len(results['reports'])} reports "
            f"with {len(results['errors'])} errors"
        )
        return results

    # ── Private helpers ──────────────────────────────────────

    async def _load_project_data(self, project_id: str) -> Dict[str, Any]:
        """Load all project data from Firestore."""
        project = await self.db.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        extracted_fields = await self.db.get_extracted_fields(project_id)

        return {
            "project": project,
            "extracted_fields": extracted_fields,
            "compliance_score": project.get("compliance_score", {}),
            "alerts": project.get("alerts", []),
        }

    async def _generate_pdf_report(
        self, project_id: str, project_data: Dict[str, Any]
    ) -> str:
        """Generate PDF project report."""
        return await self.pdf_generator.generate_project_report(
            project_id=project_id,
            project_data=project_data
        )

    async def _generate_xlsx_report(
        self, project_id: str, project_data: Dict[str, Any]
    ) -> str:
        """Generate XLSX cost tracker."""
        return await self.excel_generator.generate_cost_tracker(
            project_id=project_id,
            project_data=project_data
        )

    async def _generate_compliance_summary(
        self, project_id: str, project_data: Dict[str, Any]
    ) -> str:
        """Generate compliance summary PDF."""
        return await self.pdf_generator.generate_compliance_summary(
            project_id=project_id,
            compliance_data=project_data.get("compliance_score", {})
        )

    async def _save_report_metadata(
        self, project_id: str, results: Dict[str, Any]
    ) -> None:
        """Save report metadata to Firestore."""
        try:
            await self.db.update_project(project_id, {
                "reports": results["reports"],
                "last_report_generated": results["generated_at"]
            })
        except Exception as e:
            logger.error(f"[Agent E] Failed to save report metadata: {e}")
