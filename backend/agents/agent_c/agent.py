"""
Agent C: Permits & Compliance Checker
======================================
Agent C is the "knowledgeable friend" who has memorised the entire
CIDB/DBKL checklist and checks your documents before you submit.

Workflow:
  1. Read project state + extracted fields from Firestore (Agent A output).
  2. Determine project type → select correct Borang (A1–A8) + stage checklist.
  3. Run the deterministic ComplianceEngine for document gap analysis and
     contractor licence validation.
  4. Send the project data + initial gaps to Z.AI GLM for deeper analysis
     (catches nuanced issues the rule engine cannot).
  5. Pre-fill ePermit form fields from structured project data.
  6. Return a ComplianceResult (score %, gap list, pre-filled forms, pass/fail).
  7. Write results back to Firestore for Agent B/E to consume.

If the score is below 80 %, Agent E later sends a Telegram message via
Agent B listing exactly what is missing.

Author: Aliasya
"""

from typing import Dict, List, Any, Optional
import json
import logging

from backend.agents.agent_c.compliance import (
    ComplianceEngine,
    ComplianceResult,
    BorangType,
    BORANG_TYPE_MAP,
    EPERMIT_FIELDS,
    ProjectStage,
)
from backend.core.glm_client import GLMClient
from backend.core.firebase_client import FirestoreClient

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# GLM PROMPT — sent AFTER the deterministic engine runs so GLM
# can do a second-pass, AI-powered gap analysis.
# ─────────────────────────────────────────────────────────────

COMPLIANCE_ANALYSIS_PROMPT = """You are a senior CIDB compliance auditor for construction projects in Kuala Lumpur.

You have been given:
1. The project data (extracted by Agent A).
2. A preliminary gap list from the rule-based engine.

Your job:
- Confirm or adjust the gap list.
- Flag any ADDITIONAL documents that may be required based on project specifics
  (e.g., EIA for environmentally sensitive areas, TNB clearance for projects near substations).
- For each gap, explain WHY it matters and what delay it could cause.
- Suggest a priority order for resolving the gaps.

PROJECT DATA:
{project_data}

PRELIMINARY GAP LIST:
{gap_list}

PROJECT TYPE: {project_type}
PROJECT STAGE: {project_stage}
CONTRACTOR GRADE: {contractor_grade}

Return your analysis as a JSON object with these keys:
- "confirmed_gaps": list of gap IDs you confirm are missing
- "additional_gaps": list of {{description, reason, priority}} for new gaps found
- "risk_notes": list of risk observations
- "recommendations": list of action items sorted by priority
"""


class AgentC:
    """
    Permits & Compliance agent.

    Combines deterministic rule-checking (ComplianceEngine) with
    AI-powered analysis (GLM) for comprehensive compliance scoring.
    """

    def __init__(
        self,
        glm_client: GLMClient,
        firestore_client: FirestoreClient,
        pass_threshold: int = 80,
    ):
        """
        Args:
            glm_client:       Z.AI GLM client for AI-powered gap analysis.
            firestore_client:  Firestore client for reading/writing project data.
            pass_threshold:   Minimum score (%) to consider a project compliant.
        """
        self.glm = glm_client
        self.db = firestore_client
        self.engine = ComplianceEngine(pass_threshold=pass_threshold)
        self.pass_threshold = pass_threshold

    # ── Main entry point ─────────────────────────────────────

    async def run_compliance_check(
        self,
        project_id: str,
        stage: str = "P2-KM",
        permit_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Full compliance check pipeline.

        Args:
            project_id:   Firestore project ID.
            stage:        Current project stage (P2-KM, P2-PJ, P6-CCC …).
            permit_types: Optional list of ePermit types to pre-fill
                          ("excavation", "road_closure", "material_transport").

        Returns:
            Dict with score, gaps, pre-filled forms, and metadata.
        """
        logger.info(f"[Agent C] Starting compliance check for project {project_id}")

        # ── Step 1: Read project state from Firestore ────────
        project = await self.db.get_project(project_id)
        if not project:
            return self._error_result(f"Project {project_id} not found")

        extracted_fields = await self.db.get_extracted_fields(project_id)

        # Flatten all extracted fields into a single dict
        project_data = self._flatten_extracted_fields(project, extracted_fields)
        logger.info(f"[Agent C] Loaded {len(extracted_fields)} document field sets")

        # ── Step 2: Determine Borang type ────────────────────
        project_type = project_data.get("project_type", "general")
        borang = self.engine.resolve_borang_type(project_type)
        logger.info(f"[Agent C] Project type '{project_type}' → Borang {borang.value}")

        # ── Step 3: Collect submitted document names ─────────
        submitted_docs = self._collect_document_names(extracted_fields)

        # ── Step 4: Rule-based compliance scoring ────────────
        result = self.engine.score_documents(submitted_docs, stage=stage)
        result.borang_type = borang.value
        result.stage = stage
        logger.info(f"[Agent C] Rule engine score: {result.score:.1f}%")

        # ── Step 5: Contractor licence validation ────────────
        contractor_grade = project_data.get("cidb_grade", "")
        contractor_cat = project_data.get("cidb_category", "")
        contractor_spec = project_data.get("cidb_specialization", "")
        project_value = self._parse_value(project_data.get("project_value", 0))

        if contractor_grade:
            is_valid, issues = self.engine.validate_contractor_license(
                grade=contractor_grade,
                category=contractor_cat,
                specialization=contractor_spec,
                project_value=project_value,
            )
            result.contractor_valid = is_valid
            result.contractor_issues = issues
            if not is_valid:
                logger.warning(f"[Agent C] Contractor licence issues: {issues}")

        # ── Step 6: GLM deep analysis ────────────────────────
        try:
            glm_analysis = await self._glm_deep_analysis(
                project_data=project_data,
                gaps=result.gaps,
                project_type=project_type,
                stage=stage,
                contractor_grade=contractor_grade,
            )
            # Merge GLM findings into result
            if glm_analysis and not glm_analysis.get("parse_error"):
                additional = glm_analysis.get("additional_gaps", [])
                for gap in additional:
                    result.gaps.append({
                        "id": "GLM",
                        "description_en": gap.get("description", ""),
                        "mandatory": True,
                        "note": gap.get("reason", ""),
                    })
                    result.total_items += 1
                # Recalculate score after adding GLM gaps
                if result.total_items > 0:
                    result.score = (result.satisfied_items / result.total_items) * 100
                    result.status = (
                        "pass" if result.score >= self.pass_threshold
                        else "warning" if result.score >= 60
                        else "fail"
                    )
        except Exception as e:
            logger.error(f"[Agent C] GLM analysis failed (non-fatal): {e}")

        # ── Step 7: Pre-fill ePermit forms ───────────────────
        permit_types = permit_types or []
        for ptype in permit_types:
            result.prefilled_forms[ptype] = self.engine.prefill_epermit_fields(
                permit_type=ptype,
                project_data=project_data,
            )

        # ── Step 8: Persist results to Firestore ─────────────
        await self._save_compliance_result(project_id, result)

        logger.info(
            f"[Agent C] Final score: {result.score:.1f}% ({result.status}) "
            f"— {len(result.gaps)} gaps found"
        )
        return result.to_dict()

    # ── Private helpers ──────────────────────────────────────

    def _flatten_extracted_fields(
        self,
        project: Dict[str, Any],
        extracted_list: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Merge project metadata with all extracted field sets."""
        merged = dict(project)
        for entry in extracted_list:
            fields = entry.get("fields", {})
            if isinstance(fields, dict):
                for k, v in fields.items():
                    if v is not None and k not in merged:
                        merged[k] = v
        return merged

    def _collect_document_names(
        self, extracted_list: List[Dict[str, Any]]
    ) -> List[str]:
        """Build a list of document description strings for matching."""
        names = []
        for entry in extracted_list:
            fields = entry.get("fields", {})
            # Use document filename as a signal
            if "filename" in entry:
                names.append(entry["filename"])
            # Also include any extracted doc-type labels
            if isinstance(fields, dict):
                for key in ("document_type", "form_type", "report_type", "title"):
                    val = fields.get(key)
                    if val:
                        names.append(str(val))
        return names

    def _parse_value(self, val) -> float:
        """Safely parse a project value to float."""
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            cleaned = val.replace(",", "").replace("RM", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        return 0.0

    async def _glm_deep_analysis(
        self,
        project_data: Dict[str, Any],
        gaps: List[Dict[str, Any]],
        project_type: str,
        stage: str,
        contractor_grade: str,
    ) -> Dict[str, Any]:
        """Send project + gaps to GLM for AI-powered second pass."""
        # Truncate project_data to avoid exceeding token limits
        safe_data = {
            k: v for k, v in project_data.items()
            if isinstance(v, (str, int, float, bool)) and k != "id"
        }
        prompt = COMPLIANCE_ANALYSIS_PROMPT.format(
            project_data=json.dumps(safe_data, default=str, indent=2),
            gap_list=json.dumps(gaps, default=str, indent=2),
            project_type=project_type,
            project_stage=stage,
            contractor_grade=contractor_grade or "Not provided",
        )
        return await self.glm.extract_json(prompt)

    async def _save_compliance_result(
        self, project_id: str, result: ComplianceResult
    ) -> None:
        """Persist compliance result to Firestore for downstream agents."""
        try:
            await self.db.update_project(project_id, {
                "compliance_score": result.to_dict(),
                "compliance_status": result.status,
            })
        except Exception as e:
            logger.error(f"[Agent C] Failed to save results: {e}")

    def _error_result(self, message: str) -> Dict[str, Any]:
        """Return an error-state compliance result."""
        return ComplianceResult(
            score=0,
            status="error",
            gaps=[{"id": "ERR", "description_en": message, "mandatory": True}],
        ).to_dict()
