# Testing Guide for Buildora

This document explains how to test each component of the Buildora system.

---

## 🧪 Testing Agent A (Document Reader)

Agent A is responsible for parsing PDF documents and extracting structured fields using Z.AI GLM-4-Flash.

### **Prerequisites**

#### Option 1: Testing WITH API Key (Full Integration)
You need:
1. **Z.AI API Key** from https://open.bigmodel.cn/
2. **Firebase Credentials** (service account JSON)
3. **Sample PDF documents** (construction contracts, project plans)

#### Option 2: Testing WITHOUT API Key (Mock Testing)
You can test the structure and logic without API keys using mocks.

---

## 🔑 Option 1: Full Integration Testing (WITH API Key)

### Step 1: Set Up Environment

1. **Get Z.AI API Key**
   ```bash
   # Visit https://open.bigmodel.cn/
   # Sign up and get your API key
   ```

2. **Configure `.env` file**
   ```bash
   cp .env.example .env
   ```

3. **Add your credentials to `.env`**
   ```env
   # Z.AI API Configuration
   GLM_API_KEY=your_actual_api_key_here
   GLM_MODEL=glm-4-flash
   GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/

   # Firebase Configuration
   FIREBASE_CREDENTIALS=path/to/serviceAccountKey.json
   FIREBASE_STORAGE_BUCKET=your-project.appspot.com

   # Optional: Debug mode
   DEBUG=true
   ```

### Step 2: Prepare Test Documents

Create a test PDF document or use a sample construction contract:

```bash
# Create a test directory
mkdir -p test_data/documents

# Place your PDF files here
# Example: test_data/documents/sample_contract.pdf
```

### Step 3: Run Agent A Test

```bash
# Run the integration test
python backend/tests/test_agent_a_integration.py
```

**Expected Output:**
```
Running Agent A integration tests...

✓ Agent A initialized successfully with Firebase clients

Running full pipeline test...
[Agent A] Processing 1 documents...
[Agent A] Successfully processed 1 documents
[Agent B] Checking for delays and cost variances...
[Agent E] Processing alerts and sending notifications...
[Agent C] Running compliance check...
[Agent D] Generating reports...

=== Test Result ===
Project ID: test-project-001
Extracted Fields: {
  "project_id": "test-project-001",
  "documents_processed": 1,
  "extracted_fields": [
    {
      "document_id": "doc_123",
      "filename": "sample_contract.pdf",
      "fields": {
        "project_name": "Building Construction Project",
        "contractor": "ABC Construction Ltd",
        "budget": 1500000.00,
        "start_date": "2024-01-15",
        "end_date": "2024-12-31",
        "milestones": [...],
        ...
      }
    }
  ]
}

✓ All tests passed!
```

### Step 4: Test Individual Components

**Test PDF Parsing Only:**
```python
# Create a test script: test_pdf_parsing.py
from backend.agents.agent_a.parsers import parse_pdf_with_fallback

text = parse_pdf_with_fallback("test_data/documents/sample_contract.pdf")
print(f"Extracted text length: {len(text)} characters")
print(f"First 500 chars:\n{text[:500]}")
```

**Test GLM Extraction Only:**
```python
# Create a test script: test_glm_extraction.py
import asyncio
from backend.core.glm_client import GLMClient
from backend.agents.agent_a.prompts import get_extraction_prompt

async def test_glm():
    client = GLMClient()

    sample_text = """
    PROJECT AGREEMENT
    Project Name: Building A Construction
    Contractor: ABC Construction Ltd
    Budget: RM 1,500,000
    Start Date: 15 January 2024
    End Date: 31 December 2024
    """

    prompt = get_extraction_prompt(sample_text)
    result = await client.extract_json(prompt)

    print("Extracted fields:")
    print(result)

asyncio.run(test_glm())
```

**Test Firebase Storage:**
```python
# Create a test script: test_firebase_storage.py
import asyncio
from backend.core.storage import FirebaseStorageClient

async def test_storage():
    client = FirebaseStorageClient()

    # Upload test file
    url = await client.upload_file(
        local_path="test_data/documents/sample_contract.pdf",
        remote_path="test/sample_contract.pdf"
    )

    print(f"Uploaded to: {url}")

    # Check if file exists
    exists = await client.file_exists("test/sample_contract.pdf")
    print(f"File exists: {exists}")

asyncio.run(test_storage())
```

---

## 🎭 Option 2: Mock Testing (WITHOUT API Key)

If you don't have API keys yet, you can still test the structure and logic using mocks.

### Step 1: Install Test Dependencies

```bash
pip install pytest pytest-asyncio pytest-mock
```

### Step 2: Create Mock Test

Create `backend/tests/test_agent_a_mock.py`:

```python
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
    with patch('backend.agents.agent_a.agent.parse_pdf_with_fallback') as mock_parse:
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
```

### Step 3: Run Mock Tests

```bash
# Run with pytest
pytest backend/tests/test_agent_a_mock.py -v

# Or run directly
python backend/tests/test_agent_a_mock.py
```

---

## 📊 Testing Summary

### What You Can Test NOW (Without API Keys)

✅ **Agent A Structure**
- Class initialization
- Method signatures
- Error handling
- Data flow logic

✅ **Orchestrator Flow**
- State management
- Agent sequencing
- Conditional edges

✅ **Code Quality**
- Import statements
- Type hints
- Async/await patterns

### What Requires API Keys

⏳ **Agent A Full Integration**
- Real PDF parsing
- GLM field extraction
- Firebase storage
- End-to-end pipeline

⏳ **Performance Testing**
- API response times
- Large document handling
- Concurrent requests

---

## 🚦 Testing Phases

### Phase 1: Mock Testing (NOW - No API Keys)
```bash
# Run all mock tests
pytest backend/tests/ -k mock -v
```

### Phase 2: Integration Testing (After API Keys)
```bash
# Set up .env with real credentials
# Then run integration tests
pytest backend/tests/test_agent_a_integration.py -v
```

### Phase 3: End-to-End Testing (After All Agents)
```bash
# Test complete pipeline
python backend/agents/orchestrator.py
```

---

## 🐛 Troubleshooting

### Issue: "Module not found"
```bash
# Install in development mode
pip install -e .
```

### Issue: "Firebase credentials not found"
```bash
# Check .env file
cat .env | grep FIREBASE_CREDENTIALS

# Verify file exists
ls -la path/to/serviceAccountKey.json
```

### Issue: "GLM API error"
```bash
# Verify API key
echo $GLM_API_KEY

# Test API connection
curl -H "Authorization: Bearer $GLM_API_KEY" \
     https://open.bigmodel.cn/api/paas/v4/chat/completions
```

---

## 📝 Test Checklist

Before submitting your agent implementation, ensure:

- [ ] Unit tests pass with mocks
- [ ] Integration tests pass with real API
- [ ] Error handling works correctly
- [ ] Documentation is updated
- [ ] Code follows project structure (FILE_STRUCTURE.md)

---

**Last Updated**: 2024-01-XX
**Document Owner**: Chip/Azim
