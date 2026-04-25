# File Structure - MANDATORY

**⚠️ THIS STRUCTURE IS STRICT AND MUST BE FOLLOWED ⚠️**

All team members MUST adhere to this exact folder structure. Do NOT create files outside this structure without team approval.

---

## Complete Project Structure

```
buildora/
├── docker-compose.yml          [Chip/Azim] - one command starts everything
├── .env.example                [Chip/Azim] - template for all API keys
├── .gitignore                  [All] - ignore .env, __pycache__, node_modules
├── README.md                   [All] - setup guide + demo link for judges
├── pyproject.toml              [Chip/Azim] - Python config + pytest settings
├── GITHUB_MANAGEMENT.md        [All] - Git workflow (READ THIS FIRST)
├── FILE_STRUCTURE.md           [All] - This file
│
├── backend/                    [Python/FastAPI]
│   ├── Dockerfile              [Chip/Azim] - builds the Python container
│   ├── main.py                 [Chip/Azim] - FastAPI app entry point
│   │
│   ├── agents/                 [Core AI Logic]
│   │   ├── __init__.py
│   │   ├── orchestrator.py     [Chip/Azim] - LangGraph graph — wires all 4 agents
│   │   │
│   │   ├── agent_a/            [Document Reader - Chip/Azim]
│   │   │   ├── __init__.py
│   │   │   ├── agent.py        [Chip/Azim] - main Agent A logic
│   │   │   ├── parsers.py      [Chip/Azim] - pdfplumber + PyMuPDF + Tesseract OCR
│   │   │   └── prompts.py      [Chip/Azim] - GLM prompts for field extraction
│   │   │
│   │   ├── agent_b/            [Monitor - Khair]
│   │   │   ├── __init__.py
│   │   │   ├── agent.py        [Khair] - main Agent B logic
│   │   │   └── delay_checker.py [Khair] - delay >3 days + cost >8% logic
│   │   │
│   │   ├── agent_c/            [Permits/Compliance - Harry + Aliasya]
│   │   │   ├── __init__.py
│   │   │   ├── agent.py        [Aliasya] - main Agent C logic — conditional
│   │   │   ├── compliance.py   [Aliasya] - CIDB scoring + gap detection
│   │   │   └── knowledge_base/
│   │   │       └── cidb_bisq.json [Harry] - CIDB BISQ checklist — Harry digitises manually
│   │   │
│   │   ├── agent_d/            [Reports - Farah]
│   │   │   ├── __init__.py
│   │   │   ├── agent.py        [Farah] - main Agent D logic
│   │   │   ├── pdf_generator.py [Farah] - ReportLab branded PDF
│   │   │   └── excel_generator.py [Farah] - openpyxl XLSX cost tracker
│   │   │
│   │   └── agent_e/            [Alerts & Reminders - Harry]
│   │       ├── __init__.py
│   │       ├── agent.py        [Harry] - main Agent E logic
│   │       ├── telegram_notifier.py [Harry] - Telegram message sender
│   │       └── reminder_scheduler.py [Harry] - Schedule and send reminders
│   │
│   ├── api/                    [REST Endpoints]
│   │   ├── __init__.py
│   │   ├── upload.py           [Chip/Azim] - POST /upload — receives files from browser
│   │   ├── projects.py         [Chip/Azim] - GET/POST /projects
│   │   ├── milestones.py       [Khair] - POST /milestones — Agent B reads this
│   │   └── reports.py          [Farah] - GET /reports/{id} — triggers Agent D
│   │
│   ├── core/                   [Shared Utilities]
│   │   ├── __init__.py
│   │   ├── config.py           [Chip/Azim] - reads all .env settings
│   │   ├── firebase_client.py  [Khair] - Firebase Firestore + Realtime DB
│   │   ├── glm_client.py       [Chip/Azim] - wraps all Z.AI GLM API calls
│   │   └── storage.py          [Chip/Azim] - Firebase Storage for file upload/download
│   │
│   └── tests/                  [Test Suite]
│       ├── __init__.py
│       ├── conftest.py         [Chip/Azim] - shared test fixtures
│       ├── test_glm_response_parse.py [Chip/Azim] - Day 1
│       ├── test_state_handoff.py [Aliasya] - Day 2 — GATE: A writes, B reads
│       ├── test_extract_fields.py [Aliasya] - Day 3 — ≥10 fields, ≥80% accuracy
│       ├── test_extract_ocr.py [Aliasya] - Day 4 — scanned PDF fallback
│       ├── test_delay_logic.py [Khair] - Day 5 — delay >3 days triggers flag
│       ├── test_cost_variance.py [Khair] - Day 6 — cost >8% triggers queue
│       ├── test_compliance_check.py [Aliasya] - Day 8 — Agent C pass/fail scoring
│       ├── test_report_output.py [Farah] - Day 10 — valid PDF + correct XLSX
│       └── test_pipeline_e2e.py [All] - Day 11 — full pipeline in <15s
│
├── frontend/                   [React Application - Farah]
│   ├── Dockerfile              [Farah] - builds the React container
│   ├── package.json            [Farah] - npm dependencies
│   ├── vite.config.js          [Farah] - build config
│   ├── tailwind.config.js      [Farah] - Tailwind CSS config
│   ├── index.html              [Farah] - HTML entry point
│   │
│   └── src/
│       ├── main.jsx            [Farah] - React entry point
│       ├── App.jsx             [Farah] - routing + layout
│       │
│       ├── components/         [Reusable UI Components]
│       │   ├── UploadZone.jsx  [Farah] - drag-and-drop file upload
│       │   ├── AgentPanel.jsx  [Farah] - live agent trace — P0 demo hook
│       │   ├── ProjectDashboard.jsx [Farah] - project list + health score
│       │   ├── MilestoneForm.jsx [Farah] - PM submits milestone updates
│       │   ├── ComplianceScore.jsx [Farah] - Agent C result display
│       │   └── ReportDownload.jsx [Farah] - Agent D PDF/XLSX download
│       │
│       ├── pages/              [Route Pages]
│       │   ├── Home.jsx        [Farah] - landing + upload page
│       │   ├── Project.jsx     [Farah] - per-project detail view
│       │   └── DemoMode.jsx    [Farah] - pre-loaded demo data for judges
│       │
│       └── api/                [API Client]
│           └── client.js       [Farah] - all HTTP calls to FastAPI
│
├── data/                       [Demo & Test Data]
│   └── demo/
│       └── sample_project.json [All] - realistic Malaysian construction demo data
│
└── Ref documents/              [Reference Materials - DO NOT MODIFY]
    ├── buildora_architecture_and_structure.html
    └── Buildora_PRD_v2 (1).docx
```

---

## File Naming Conventions

### Python Files
- **Snake case:** `agent_a.py`, `redis_client.py`, `delay_checker.py`
- **Test files:** `test_<feature>.py`
- **Private modules:** `_internal.py` (if needed)

### JavaScript/React Files
- **PascalCase for components:** `UploadZone.jsx`, `AgentPanel.jsx`
- **camelCase for utilities:** `client.js`, `helpers.js`
- **Config files:** `vite.config.js`, `tailwind.config.js`

### Configuration Files
- **Lowercase with dots:** `docker-compose.yml`, `.env.example`, `.gitignore`
- **Python config:** `pyproject.toml`

---

## Import Path Rules

### Backend Python Imports
```python
# Absolute imports from project root
from backend.agents.orchestrator import run_pipeline
from backend.core.firebase_client import get_firestore, get_realtime_db
from backend.core.glm_client import GLMClient

# Relative imports within same package
from .parsers import extract_pdf_text
from .prompts import EXTRACTION_PROMPT
```

### Frontend JavaScript Imports
```javascript
// Absolute imports (configure in vite.config.js)
import { uploadFile } from '@/api/client'
import UploadZone from '@/components/UploadZone'

// Relative imports
import './App.css'
import { helper } from './utils/helpers'
```

---

## What Goes Where?

### Backend Structure

| Directory | Purpose | Who Owns |
|-----------|---------|----------|
| `agents/` | All AI agent logic (A, B, C, D, E) | Chip/Azim, Khair, Harry, Aliasya, Farah |
| `api/` | FastAPI route handlers | Chip/Azim, Khair, Farah |
| `core/` | Shared utilities (Firebase, GLM, Storage, config) | Chip/Azim, Khair |
| `tests/` | All test files | All team members |

### Frontend Structure

| Directory | Purpose | Who Owns |
|-----------|---------|----------|
| `components/` | Reusable React components | Farah |
| `pages/` | Route-level page components | Farah |
| `api/` | HTTP client for backend calls | Farah |

---

## Rules for Adding New Files

### ✅ ALLOWED (with team notification)
- New test files in `backend/tests/`
- New React components in `frontend/src/components/`
- New utility functions in existing directories
- New prompts in `agent_*/prompts.py`

### ⚠️ REQUIRES TEAM APPROVAL
- New top-level directories
- New agent subdirectories
- New API endpoint files
- Changes to Docker or config files

### ❌ FORBIDDEN
- Files outside this structure
- Duplicate functionality in different locations
- Test files outside `backend/tests/`
- Config files with hardcoded secrets

---

## Directory Ownership & Permissions

| Owner | Primary Directories | Can Modify |
|-------|---------------------|------------|
| **Chip/Azim** | `backend/agents/orchestrator.py`<br>`backend/agents/agent_a/`<br>`backend/api/upload.py`<br>`backend/core/` | All backend infrastructure |
| **Farah** | `frontend/`<br>`backend/agents/agent_d/`<br>`backend/api/reports.py` | All frontend + Agent D + UI/UX fonts |
| **Khair** | `backend/core/firebase_client.py`<br>`backend/agents/agent_b/agent.py`<br>`backend/api/milestones.py` | Firebase + Agent B |
| **Harry** | `backend/agents/agent_e/`<br>`backend/agents/agent_c/knowledge_base/` | Agent E (Alerts/Reminders) + CIDB data |
| **Aliasya** | `backend/agents/agent_c/agent.py`<br>`backend/agents/agent_c/compliance.py` | Agent C logic |

---

## Before Creating a New File

1. **Check this document** - Does it fit the structure?
2. **Check if it already exists** - Use `find` or IDE search
3. **Ask in team chat** - "I'm adding `<filename>` to `<directory>`, any objections?"
4. **Update this doc** - If approved, add it to the structure above

---

## Questions?

- **"Where should I put X?"** → Check this doc first, then ask Chip/Azim
- **"Can I create a new folder?"** → Ask the team in chat
- **"This structure doesn't work for my feature"** → Discuss with team, we'll adapt if needed

**Remember:** Consistency > Convenience. Follow the structure! 🏗️
