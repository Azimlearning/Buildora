"""
Integration test for Agent A and Orchestrator

Tests the complete pipeline:
1. Agent A receives documents
2. Parses PDFs
3. Extracts fields via GLM
4. Stores in Firebase
5. Returns structured data

Author: Chip/Azim
"""

import asyncio
import pytest
from backend.agents.orchestrator import run_pipeline


@pytest.mark.asyncio
async def test_orchestrator_with_agent_a():
    """Test full orchestrator pipeline with Agent A"""

    # Mock document data
    test_documents = [
        {
            "filename": "test_contract.pdf",
            "file_path": "/tmp/test_contract.pdf",
            "size": 102400
        }
    ]

    # Run pipeline
    result = await run_pipeline(
        project_id="test-project-001",
        documents=test_documents
    )

    # Assertions
    assert result["project_id"] == "test-project-001"
    assert "extracted_fields" in result
    assert "alerts" in result
    assert "compliance_score" in result
    assert "reports" in result
    assert "notifications_sent" in result
    assert isinstance(result["errors"], list)

    print("\n=== Test Result ===")
    print(f"Project ID: {result['project_id']}")
    print(f"Extracted Fields: {result['extracted_fields']}")
    print(f"Alerts: {result['alerts']}")
    print(f"Compliance: {result['compliance_score']}")
    print(f"Reports: {result['reports']}")
    print(f"Notifications Sent: {result['notifications_sent']}")
    print(f"Errors: {result['errors']}")


def test_agent_a_initialization():
    """Test Agent A can be initialized with Firebase clients"""
    from backend.agents.agent_a.agent import AgentA
    from backend.core.glm_client import GLMClient
    from backend.core.firebase_client import FirestoreClient
    from backend.core.storage import FirebaseStorageClient

    glm = GLMClient()
    storage = FirebaseStorageClient()
    firestore = FirestoreClient()

    agent_a = AgentA(glm, storage, firestore)

    assert agent_a.glm is not None
    assert agent_a.storage is not None
    assert agent_a.db is not None

    print("\n✓ Agent A initialized successfully with Firebase clients")


if __name__ == "__main__":
    # Run tests
    print("Running Agent A integration tests...\n")

    # Test 1: Initialization
    test_agent_a_initialization()

    # Test 2: Full pipeline (requires async)
    print("\nRunning full pipeline test...")
    asyncio.run(test_orchestrator_with_agent_a())

    print("\n✓ All tests passed!")
