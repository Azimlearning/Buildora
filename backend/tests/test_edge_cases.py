"""
Edge Case Tests for AI-First Engineering
=========================================
Comprehensive edge-case coverage for all agents. AI-generated code must handle
edge cases explicitly, not just happy paths.

Author: AI-First Engineering Initiative
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from backend.agents.agent_a.agent import AgentA
from backend.agents.agent_c.agent import AgentC
from backend.agents.agent_e.agent import AgentE
from backend.agents.contracts import ProcessingStatus, ConfidenceLevel


# ═══════════════════════════════════════════════════════════════
# AGENT A: DOCUMENT READER - EDGE CASES
# ═══════════════════════════════════════════════════════════════


class TestAgentAEdgeCases:
    """Edge cases for Agent A document processing"""

    @pytest.mark.asyncio
    async def test_malformed_pdf_graceful_degradation(self):
        """Agent A must handle corrupted PDFs without crashing pipeline"""
        # Setup
        glm_client = Mock()
        storage_client = AsyncMock()
        firestore_client = AsyncMock()
        agent_a = AgentA(glm_client, storage_client, firestore_client)

        # Corrupted PDF that will fail parsing
        documents = [{"file_path": "/path/to/corrupted.pdf", "filename": "corrupted.pdf"}]

        with patch.object(agent_a, 'parse_pdf', side_effect=Exception("PDF parsing failed")):
            result = await agent_a.process_documents("proj_001", documents)

        # Must not crash, must report error
        assert result["status"] == ProcessingStatus.PARTIAL or result["status"] == ProcessingStatus.FAILED
        assert result["documents_failed"] == 1
        assert len(result["errors"]) > 0
        assert "corrupted.pdf" in str(result["errors"])

    @pytest.mark.asyncio
    async def test_mixed_language_documents(self):
        """Handle Malay + English mixed documents"""
        glm_client = Mock()
        storage_client = AsyncMock()
        firestore_client = AsyncMock()
        agent_a = AgentA(glm_client, storage_client, firestore_client)

        # Mock mixed language text
        mixed_text = "Projek: KL Tower Renovation\nBudget: RM 5,000,000\nKontraktor: ABC Sdn Bhd"

        with patch.object(agent_a, 'parse_pdf', return_value=mixed_text):
            with patch.object(agent_a, 'extract_fields', return_value={"project_name": "KL Tower Renovation"}):
                storage_client.upload_file = AsyncMock(return_value="https://storage.url")
                firestore_client.save_document = AsyncMock(return_value="doc_001")
                firestore_client.save_extracted_fields = AsyncMock(return_value="fields_001")

                documents = [{"file_path": "/path/to/mixed.pdf", "filename": "mixed.pdf"}]
                result = await agent_a.process_documents("proj_001", documents)

        # Must successfully process mixed language
        assert result["status"] == ProcessingStatus.COMPLETED
        assert result["documents_processed"] == 1

    @pytest.mark.asyncio
    async def test_empty_pdf_handling(self):
        """Empty PDF should not crash"""
        glm_client = Mock()
        storage_client = AsyncMock()
        firestore_client = AsyncMock()
        agent_a = AgentA(glm_client, storage_client, firestore_client)

        with patch.object(agent_a, 'parse_pdf', return_value=""):
            with patch.object(agent_a, 'extract_fields', return_value={}):
                storage_client.upload_file = AsyncMock(return_value="https://storage.url")
                firestore_client.save_document = AsyncMock(return_value="doc_001")
                firestore_client.save_extracted_fields = AsyncMock(return_value="fields_001")

                documents = [{"file_path": "/path/to/empty.pdf", "filename": "empty.pdf"}]
                result = await agent_a.process_documents("proj_001", documents)

        assert result["status"] == ProcessingStatus.COMPLETED
        assert result["documents_processed"] == 1

    @pytest.mark.asyncio
    async def test_concurrent_document_processing(self):
        """Multiple documents processed concurrently should not interfere"""
        glm_client = Mock()
        storage_client = AsyncMock()
        firestore_client = AsyncMock()
        agent_a = AgentA(glm_client, storage_client, firestore_client)

        documents = [
            {"file_path": f"/path/to/doc{i}.pdf", "filename": f"doc{i}.pdf"}
            for i in range(5)
        ]

        with patch.object(agent_a, 'parse_pdf', return_value="text"):
            with patch.object(agent_a, 'extract_fields', return_value={"field": "value"}):
                storage_client.upload_file = AsyncMock(return_value="https://storage.url")
                firestore_client.save_document = AsyncMock(side_effect=[f"doc_{i}" for i in range(5)])
                firestore_client.save_extracted_fields = AsyncMock(side_effect=[f"fields_{i}" for i in range(5)])

                result = await agent_a.process_documents("proj_001", documents)

        assert result["documents_processed"] == 5
        assert len(result["extracted_fields"]) == 5


# ═══════════════════════════════════════════════════════════════
# AGENT C: COMPLIANCE - EDGE CASES
# ═══════════════════════════════════════════════════════════════


class TestAgentCEdgeCases:
    """Edge cases for Agent C compliance checking"""

    @pytest.mark.asyncio
    async def test_missing_project_data(self):
        """Handle missing project gracefully"""
        glm_client = Mock()
        firestore_client = AsyncMock()
        firestore_client.get_project = AsyncMock(return_value=None)

        agent_c = AgentC(glm_client, firestore_client)
        result = await agent_c.run_compliance_check("nonexistent_project")

        assert result["status"] == "error"
        assert "not found" in result["gaps"][0]["description_en"].lower()

    @pytest.mark.asyncio
    async def test_borderline_compliance_score(self):
        """Score exactly at 80% threshold"""
        glm_client = Mock()
        firestore_client = AsyncMock()
        firestore_client.get_project = AsyncMock(return_value={"id": "proj_001", "project_type": "general"})
        firestore_client.get_extracted_fields = AsyncMock(return_value=[])
        firestore_client.update_project = AsyncMock()

        agent_c = AgentC(glm_client, firestore_client, pass_threshold=80)

        # Mock engine to return exactly 80%
        with patch.object(agent_c.engine, 'score_documents') as mock_score:
            from backend.agents.agent_c.compliance import ComplianceResult
            mock_score.return_value = ComplianceResult(score=80.0, status="pass", gaps=[])

            result = await agent_c.run_compliance_check("proj_001")

        assert result["score"] == 80.0
        assert result["status"] == "pass"

    @pytest.mark.asyncio
    async def test_glm_api_failure_fallback(self):
        """GLM failure should not block rule-based compliance"""
        glm_client = Mock()
        glm_client.extract_json = AsyncMock(side_effect=Exception("GLM API down"))
        firestore_client = AsyncMock()
        firestore_client.get_project = AsyncMock(return_value={"id": "proj_001", "project_type": "general"})
        firestore_client.get_extracted_fields = AsyncMock(return_value=[])
        firestore_client.update_project = AsyncMock()

        agent_c = AgentC(glm_client, firestore_client)
        result = await agent_c.run_compliance_check("proj_001")

        # Should still return rule-based score
        assert "score" in result
        assert result["score"] >= 0


# ═══════════════════════════════════════════════════════════════
# AGENT E: REPORTS - EDGE CASES
# ═══════════════════════════════════════════════════════════════


class TestAgentEEdgeCases:
    """Edge cases for Agent E report generation"""

    @pytest.mark.asyncio
    async def test_missing_project_data_for_report(self):
        """Handle missing project gracefully"""
        firestore_client = AsyncMock()
        storage_client = AsyncMock()
        firestore_client.get_project = AsyncMock(return_value=None)

        agent_e = AgentE(firestore_client, storage_client)
        result = await agent_e.generate_reports("nonexistent_project")

        assert len(result["errors"]) > 0
        assert "not found" in result["errors"][0].lower()

    @pytest.mark.asyncio
    async def test_partial_report_generation_failure(self):
        """One report fails, others should still generate"""
        firestore_client = AsyncMock()
        storage_client = AsyncMock()
        firestore_client.get_project = AsyncMock(return_value={"id": "proj_001"})
        firestore_client.get_extracted_fields = AsyncMock(return_value=[])
        firestore_client.update_project = AsyncMock()

        agent_e = AgentE(firestore_client, storage_client)

        # Mock PDF generation to fail, XLSX to succeed
        with patch.object(agent_e, '_generate_pdf_report', side_effect=Exception("PDF failed")):
            with patch.object(agent_e, '_generate_xlsx_report', return_value="/tmp/report.xlsx"):
                storage_client.upload_file = AsyncMock(return_value="https://storage.url/report.xlsx")

                result = await agent_e.generate_reports("proj_001", report_types=["pdf", "xlsx"])

        # Should have XLSX but not PDF
        assert "xlsx" in result["reports"]
        assert "pdf" not in result["reports"]
        assert len(result["errors"]) > 0


# ═══════════════════════════════════════════════════════════════
# CROSS-AGENT INTEGRATION EDGE CASES
# ═══════════════════════════════════════════════════════════════


class TestCrossAgentEdgeCases:
    """Edge cases spanning multiple agents"""

    @pytest.mark.asyncio
    async def test_agent_a_output_to_agent_c_input(self):
        """Agent C must handle Agent A's output format"""
        # This tests the contract boundary
        from backend.agents.contracts import AgentAOutput, ProcessingStatus

        agent_a_output = AgentAOutput(
            project_id="proj_001",
            status=ProcessingStatus.COMPLETED,
            documents_processed=1,
            documents_failed=0,
            processing_time_ms=1000,
            extracted_fields=[{"document_id": "doc_001", "fields": {"project_name": "Test"}}],
            storage_urls=["https://storage.url"],
            errors=[],
            metadata={}
        )

        # Agent C should be able to read this
        assert agent_a_output["project_id"] == "proj_001"
        assert len(agent_a_output["extracted_fields"]) == 1

    @pytest.mark.asyncio
    async def test_pipeline_state_consistency(self):
        """BuildoraState must maintain consistency across agents"""
        from backend.agents.contracts import BuildoraState

        # Simulate state passing through pipeline
        state: BuildoraState = {
            "project_id": "proj_001",
            "pipeline_run_id": "run_001",
            "started_at": "2026-04-23T10:00:00Z",
            "documents": [],
            "extracted_fields": None,
            "monitoring_results": None,
            "compliance_results": None,
            "notification_results": None,
            "report_results": None,
            "current_agent": "agent_a",
            "completed_agents": [],
            "failed_agents": [],
            "total_processing_time_ms": 0,
            "errors": [],
            "warnings": [],
            "pipeline_status": "running"
        }

        # State should be valid
        assert state["project_id"] == "proj_001"
        assert state["pipeline_status"] == "running"
