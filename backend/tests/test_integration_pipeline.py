import pytest
import asyncio
from backend.agents.orchestrator import run_pipeline

@pytest.mark.asyncio
async def test_full_pipeline():
    test_docs = [
        {"filename": "test_project_plan.pdf", "size": 1024000, "file_path": "test_project_plan.pdf"}
    ]
    
    # We create a dummy file for the test
    with open("test_project_plan.pdf", "w") as f:
        f.write("Dummy PDF content for testing")

    result = await run_pipeline("test-project-integration", test_docs)
    
    assert "extracted_fields" in result
    assert "alerts" in result
    assert "compliance_score" in result
    assert "reports" in result
    assert isinstance(result["alerts"], list)
