# 🏗️ Buildora

> **AI-powered construction project management platform for Malaysian construction projects.**
> Built for UM Hackathon 2025 — automated compliance, monitoring, and reporting across a 5-agent pipeline.

---

## 📄 Submission Documents

All hackathon submission documents are located in the [`Submission_documents/`](./Submission_documents/) folder:

| Document | File |
|----------|------|
| 📊 **Slides (Pitch Deck)** | `Buildora AI for Malaysia Construction.pptx` |
| 📑 **Slides (PDF)** | `Buildora AI for Malaysia Construction.pdf` |
| 📋 **PRD** *(Product Requirements Document)* | Included in submission package |
| 🏛️ **SAD** *(System Architecture Document)* | Included in submission package |
| 🧪 **QATD** *(QA & Test Document)* | Included in submission package |

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Azimlearning/Buildora.git
cd Buildora

# 2. Set up environment
cp .env.example .env
# Edit .env with your API keys (see Environment Variables section below)

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. Start Backend (Terminal 1) — run from project root
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 5. Start Frontend (Terminal 2)
cd frontend
npm install
npm run dev
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |

---

## 👥 Team Members & Responsibilities

| Member | Component | Branch |
|--------|-----------|--------|
| **Azim (Chip)** | Backend + Orchestrator + Agent A | `azim` |
| **Farah** | Frontend + Agent D + UI/UX | `farah` |
| **Khaidhir** | Firebase + Agent B (Monitor) | `khaidhir` |
| **Harry** | Agent E (Alerts) + CIDB data | `development` |
| **Aliasya** | Agent C (Compliance logic) | `aliasya` |

---

## 🏛️ Architecture

```
PM Browser → React Frontend → FastAPI Backend → LangGraph Orchestrator
                                                        ↓
                        ┌───────────────────────────────┼────────────────────┐
                        ↓                               ↓                    ↓
                    Agent A                         Agent B             Agent C
                (Doc Reader)                      (Monitor)          (Compliance)
                        ↓                               ↓                    ↓
                        └───────────────────────── Agent D ──────────── Agent E
                                                  (Reports)            (Alerts)
                                                      ↓                    ↓
                                              PDF + XLSX              Telegram
                                                      └──── Firebase ──────┘
```

---

## 🤖 System Components

| Agent | Role | Key Tech |
|-------|------|----------|
| **Agent A** | PDF parsing & field extraction | pdfplumber, PyMuPDF, Tesseract OCR, Z.AI GLM |
| **Agent B** | Delay & cost variance monitoring (>3 days, >8%) | Firebase Realtime DB |
| **Agent C** | CIDB BISQ compliance scoring | Rule-based + GLM fallback |
| **Agent D** | Report generation — branded PDF + XLSX | ReportLab, OpenPyXL |
| **Agent E** | Alerts & reminders | Telegram Bot API |
| **Orchestrator** | LangGraph state machine coordinating all 5 agents | LangGraph |
| **Chat** | AI assistant for project Q&A | OpenAI GPT-3.5-turbo |

**Databases:**
- **Firebase Firestore** — Project records & metadata
- **Firebase Realtime Database** — Shared inter-agent state store
- **Firebase Storage** — Document storage

---

## 🗂️ Project Structure

```
Buildora/
├── backend/
│   ├── agents/
│   │   ├── agent_a/         # Doc reader & field extractor
│   │   ├── agent_b/         # Project monitor
│   │   ├── agent_c/         # Compliance checker
│   │   ├── agent_d/         # Report generator
│   │   ├── agent_e/         # Alerts & Telegram
│   │   └── orchestrator/    # LangGraph pipeline
│   ├── api/                 # REST endpoints
│   │   ├── chat.py          # AI chat endpoint
│   │   ├── projects.py
│   │   ├── reports.py
│   │   ├── upload.py
│   │   └── notifications.py
│   └── core/                # Shared utilities & Firebase client
├── frontend/
│   └── src/
│       ├── components/      # UI components (Chat, Pipeline, Reports...)
│       ├── pages/           # Home, Project pages
│       └── api/             # API client
├── Submission_documents/    # 📋 Hackathon deliverables (slides, PRD, SAD, QATD)
├── knowledge_base.json      # CIDB domain knowledge
├── .env.example             # Environment variable template
└── QUICKSTART.md            # Detailed setup guide
```

---

## 🔑 Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
# Z.AI (GLM) — field extraction
GLM_API_KEY=your_key_here
GLM_API_URL=https://api.z.ai/api/paas/v4/chat/completions
GLM_MODEL=glm-4-flash
GLM_FALLBACK_MODE=true       # Use rule-based fallback on API errors

# Firebase
FIREBASE_PROJECT_ID=buildora-a06f8
FIREBASE_CREDENTIALS=./firebase-credentials.json
FIREBASE_STORAGE_BUCKET=buildora-a06f8.appspot.com

# OpenAI (Chat feature)
OPENAI_API_KEY=your_key_here

# Telegram (Agent E alerts)
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## 🌐 API Endpoints

```
GET   /                         # Health check
GET   /health                   # Detailed health status
POST  /api/upload               # Upload project documents
GET   /api/projects             # List all projects
POST  /api/projects             # Create new project
POST  /api/milestones           # Update milestone status
GET   /api/reports/{id}         # Generate & download report
POST  /api/chat                 # AI project assistant (chat)
GET   /api/notifications        # Get project notifications
GET   /api/pipeline/status/{id} # Real-time pipeline SSE stream
```

---

## 🛠️ Tech Stack

**Backend:** FastAPI · Python 3.10+ · LangGraph · pdfplumber · PyMuPDF · Tesseract OCR · ReportLab · OpenPyXL · Z.AI GLM · OpenAI

**Frontend:** React 18 · Vite · Tailwind CSS · Custom fonts

**Infrastructure:** Firebase (Firestore · Realtime DB · Storage) · Python 3.10+

---

## 🐛 Troubleshooting

**Backend won't start:**
```bash
# Make sure you're running from the project ROOT, not /backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Firebase connection errors:**
- Confirm `firebase-credentials.json` is in the project root
- Check `FIREBASE_PROJECT_ID` in `.env` matches your Firebase project

**GLM API 401 errors:**
- Your key was likely activated via Google/GitHub SSO instead of the invitation email
- Solution: Use another team member's activation link or contact the Z.AI team

**Chat not working:**
- Ensure `OPENAI_API_KEY` is set in your `.env` file (not hardcoded)

---

## 📜 License

Proprietary — UM Hackathon 2025

## 💬 Support

- Architecture questions → Check `Ref documents/`
- Git issues → Ask Azim
- Bugs → Open a GitHub Issue
