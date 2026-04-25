"""
Mock tests for Agent A (no API keys required)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.agents.agent_a.agent import AgentA


@pytest.mark.asyncio
async def test_agent_a_with_mocks():
    """Test Agent A with mocked dependencies"""

    # Mock GLM client
    mock_glm = AsyncMock()
    mock_glm.extract_json.return_value = {
        "project_name": "Mock Project",
        "contractor": "Mock Contractor",
        "budget": 1000000,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "milestones": ["Foundation", "Structure", "Finishing"]
    }

    # Mock Storage client
    mock_storage = AsyncMock()
    mock_storage.upload_file.return_value = "https://storage.example.com/mock.pdf"

    # Mock Firestore client
    mock_firestore = AsyncMock()
    mock_firestore.save_document.return_value = "doc_mock_123"
    mock_firestore.save_extracted_fields.return_value = "field_mock_456"

    # Create Agent A with mocks
    agent_a = AgentA(mock_glm, mock_storage, mock_firestore)

    # Mock PDF parsing
    with patch('backend.agents.agent_a.agent.parse_pdf') as mock_parse:
        mock_parse.return_value = "Mock PDF content with project details"

        # Test document processing
        result = await agent_a.process_documents(
            project_id="test-project-001",
            documents=[
                {
                    "filename": "mock_contract.pdf",
                    "file_path": "/tmp/mock_contract.pdf"
                }
            ]
        )

    # Assertions
    assert result["project_id"] == "test-project-001"
    assert result["documents_processed"] == 1
    assert len(result["extracted_fields"]) == 1

    extracted = result["extracted_fields"][0]
    assert extracted["filename"] == "mock_contract.pdf"
    assert extracted["fields"]["project_name"] == "Mock Project"
    assert extracted["fields"]["budget"] == 1000000

    # Verify mocks were called
    mock_glm.extract_json.assert_called_once()
    mock_storage.upload_file.assert_called_once()
    mock_firestore.save_document.assert_called_once()
    mock_firestore.save_extracted_fields.assert_called_once()

    print("\n✓ Mock test passed! Agent A structure is correct.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_agent_a_with_mocks())
