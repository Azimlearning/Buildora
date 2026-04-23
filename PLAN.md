# Buildora - Project Plan & Timeline

**Project**: Buildora - Construction Project Management System
**Team**: Chip/Azim, Khair, Farah, Harry, Aliasya
**Tech Stack**: FastAPI, LangGraph, Firebase, Z.AI GLM-4-Flash
**Repository**: https://github.com/Azimlearning/Buildora

---

## 📋 Project Overview

Buildora is a multi-agent system for construction project management that automates:
- Document parsing and field extraction
- Project monitoring and alerts
- Compliance checking (CIDB BISQ)
- Report generation
- Telegram notifications

---

## 🎯 Sprint Timeline

### **Sprint 1: Foundation & Agent A** ✅ COMPLETED
**Duration**: Initial Setup
**Owner**: Chip/Azim

- [x] Repository initialization
- [x] Project structure setup (FILE_STRUCTURE.md)
- [x] GitHub workflow documentation (GITHUB_MANAGEMENT.md)
- [x] Firebase architecture migration
- [x] Core infrastructure (config, glm_client, firebase_client, storage)
- [x] Agent A implementation (document parsing + field extraction)
- [x] Orchestrator setup with LangGraph
- [x] Integration tests
- [x] Documentation (README.md, FILE_STRUCTURE.md)

**Deliverables**: ✅ All completed and pushed to main branch

---

### **Sprint 2: Core Agents Development** 🔄 IN PROGRESS
**Duration**: TBD
**Status**: Waiting for API keys and team implementation

#### Agent B - Monitor (Harry)
**Status**: 🟡 Pending
**Dependencies**: Agent A output, Firebase setup

- [ ] Implement delay detection (>3 days threshold)
- [ ] Implement cost variance detection (>8% threshold)
- [ ] Anomaly detection logic
- [ ] Integration with Firestore to read extracted fields
- [ ] Alert generation and storage
- [ ] Unit tests for monitoring logic

**Files to create**:
- `backend/agents/agent_b/agent.py`
- `backend/agents/agent_b/monitors.py`
- `backend/agents/agent_b/thresholds.py`
- `backend/tests/test_agent_b.py`

---

#### Agent C - Compliance (Aliasya)
**Status**: ✅ COMPLETED
**Dependencies**: Agent A output, CIDB BISQ checklist

- [x] Implement CIDB BISQ scoring logic
- [x] Compliance gap detection
- [x] Integration with Firestore
- [x] Compliance report generation
- [x] Integrated into orchestrator pipeline
- [ ] Unit tests for compliance checks

**Files created**:
- `backend/agents/agent_c/agent.py` ✅
- `backend/agents/agent_c/compliance.py` ✅
- `backend/agents/agent_c/__init__.py` ✅
- `backend/tests/test_agent_c.py` (pending)

---

#### Agent D - Reports (TBD)
**Status**: ⚠️ REPLACED BY AGENT E
**Note**: Original Agent D functionality (PDF/XLSX reports) has been moved to Agent E.
Agent D is now reserved for Telegram notifications (not implemented yet).

---

#### Agent E - Output Generation (Chip/Azim)
**Status**: ✅ COMPLETED
**Dependencies**: All previous agents

- [x] PDF report generation (branded)
- [x] XLSX cost tracker generation
- [x] Template design
- [x] Integration with Firebase Storage
- [x] Integrated into orchestrator pipeline
- [ ] Unit tests for report generation

**Files created**:
- `backend/agents/agent_e/agent.py` ✅
- `backend/agents/agent_e/pdf_generator.py` ✅
- `backend/agents/agent_e/excel_generator.py` ✅
- `backend/agents/agent_e/__init__.py` ✅
- `backend/tests/test_agent_e.py` (pending)

---

### **Sprint 3: API Layer & Frontend** 🟡 PENDING
**Duration**: TBD
**Owner**: Farah (Frontend), Khair (API)

#### Backend API (Khair)
- [ ] Project CRUD endpoints
- [ ] Document upload endpoint
- [ ] Pipeline trigger endpoint
- [ ] Status/progress endpoints
- [ ] Report download endpoints
- [ ] API documentation (Swagger/OpenAPI)

**Files to create**:
- `backend/api/projects.py`
- `backend/api/documents.py`
- `backend/api/reports.py`
- `backend/api/health.py`
- `backend/tests/test_api.py`

#### Frontend (Farah)
- [ ] Project dashboard
- [ ] Document upload interface
- [ ] Real-time progress tracking
- [ ] Alert notifications display
- [ ] Report viewer/download
- [ ] Responsive design

**Files to create**:
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/ProjectDetail.tsx`
- `frontend/src/components/DocumentUpload.tsx`
- `frontend/src/components/AlertPanel.tsx`
- `frontend/src/services/api.ts`

---

### **Sprint 4: Integration & Testing** 🟡 PENDING
**Duration**: TBD
**Owner**: All team members

- [ ] End-to-end testing with real documents
- [ ] API integration testing
- [ ] Frontend-backend integration
- [ ] Performance testing
- [ ] Security audit
- [ ] Bug fixes

---

### **Sprint 5: Deployment & Documentation** 🟡 PENDING
**Duration**: TBD
**Owner**: Khair (DevOps), All (Docs)

- [ ] Firebase project setup (production)
- [ ] Environment configuration
- [ ] Docker deployment
- [ ] CI/CD pipeline setup
- [ ] User documentation
- [ ] Demo preparation

---

## 🔑 API Keys & Credentials Required

### **Immediate Priority**
- [ ] **Z.AI API Key** (GLM-4-Flash) - Required for Agent A testing
  - Get from: https://open.bigmodel.cn/
  - Add to `.env`: `GLM_API_KEY=your_key_here`

### **Sprint 2 Requirements**
- [ ] **Firebase Credentials** (Service Account JSON)
  - Create Firebase project
  - Download service account key
  - Add to `.env`: `FIREBASE_CREDENTIALS=path/to/serviceAccountKey.json`

- [ ] **Telegram Bot Token** (Agent E)
  - Create bot via @BotFather
  - Add to `.env`: `TELEGRAM_BOT_TOKEN=your_token`

### **Optional**
- [ ] **MinIO Credentials** (if not using Firebase Storage)
  - Only needed if Firebase Storage is insufficient

---

## 📊 Progress Tracking

### Overall Progress: 50% Complete

| Component | Status | Owner | Progress |
|-----------|--------|-------|----------|
| Project Setup | ✅ Done | Chip/Azim | 100% |
| Agent A | ✅ Done | Chip/Azim | 100% |
| Orchestrator | ✅ Done | Chip/Azim | 100% |
| Firebase Core | ✅ Done | Chip/Azim | 100% |
| Agent B | 🟡 Pending | Harry | 0% |
| Agent C | ✅ Done | Aliasya | 100% |
| Agent D | ⚠️ Skipped | - | N/A |
| Agent E | ✅ Done | Chip/Azim | 100% |
| Backend API | 🟡 Pending | Khair | 0% |
| Frontend | 🟡 Pending | Farah | 0% |
| Testing | 🟡 Pending | All | 30% |
| Deployment | 🟡 Pending | Khair | 0% |

---

## 🧪 Testing Strategy

### **Phase 1: Unit Testing** (Current)
- Test individual agent components
- Mock external dependencies (Firebase, GLM API)
- Run: `pytest backend/tests/`

### **Phase 2: Integration Testing** (After API keys)
- Test Agent A with real GLM API
- Test Firebase operations
- Test full orchestrator pipeline

### **Phase 3: End-to-End Testing** (After all agents)
- Test complete workflow with real documents
- Test all agent interactions
- Performance benchmarking

### **Phase 4: User Acceptance Testing** (Pre-deployment)
- Real-world document testing
- UI/UX validation
- Bug bash session

---

## 📝 Documentation Status

| Document | Status | Purpose |
|----------|--------|---------|
| README.md | ✅ Complete | Project overview, quick start |
| FILE_STRUCTURE.md | ✅ Complete | Mandatory file structure |
| GITHUB_MANAGEMENT.md | ✅ Complete | Branch workflow, PR process |
| PLAN.md | ✅ Complete | Timeline, checklist, progress |
| API_DOCS.md | 🟡 Pending | API endpoint documentation |
| USER_GUIDE.md | 🟡 Pending | End-user documentation |
| DEPLOYMENT.md | 🟡 Pending | Deployment instructions |

---

## 🚀 Quick Start for Team Members

### **For Agent Developers (Harry, Aliasya, TBD)**

1. **Clone the repository**
   ```bash
   git clone https://github.com/Azimlearning/Buildora.git
   cd Buildora
   ```

2. **Create your feature branch**
   ```bash
   git checkout -b feature/agent-b-monitor  # or agent-c, agent-d
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Add your API keys to .env
   ```

4. **Install dependencies**
   ```bash
   pip install -e .
   ```

5. **Create your agent files** (see FILE_STRUCTURE.md)
   ```
   backend/agents/agent_b/
   ├── __init__.py
   ├── agent.py
   └── [your modules]
   ```

6. **Follow the orchestrator pattern**
   - See `backend/agents/agent_a/agent.py` as reference
   - Implement async methods
   - Use Firebase clients for data storage
   - Add error handling

7. **Write tests**
   ```bash
   # Create test file
   backend/tests/test_agent_b.py

   # Run tests
   pytest backend/tests/test_agent_b.py -v
   ```

8. **Submit PR** (see GITHUB_MANAGEMENT.md)

---

### **For Frontend Developer (Farah)**

1. **Set up frontend** (after backend API is ready)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. **Connect to backend API**
   - API base URL: `http://localhost:8000`
   - See API_DOCS.md for endpoints

3. **Follow component structure**
   ```
   frontend/src/
   ├── pages/
   ├── components/
   ├── services/
   └── styles/
   ```

---

### **For DevOps (Khair)**

1. **Firebase setup**
   - Create Firebase project
   - Enable Firestore, Storage, Auth
   - Download service account key

2. **Environment configuration**
   - Set up `.env` for all environments
   - Configure Firebase security rules

3. **Docker deployment**
   ```bash
   docker-compose up -d
   ```

---

## 🐛 Known Issues & Blockers

### **Current Blockers**
1. **Z.AI API Key** - Required for Agent A testing
   - **Impact**: Cannot test document extraction
   - **Action**: Team to acquire API key
   - **Owner**: TBD

2. **Firebase Credentials** - Required for database operations
   - **Impact**: Cannot test data persistence
   - **Action**: Set up Firebase project
   - **Owner**: Khair

3. **Telegram Bot Token** - Required for Agent E
   - **Impact**: Cannot test notifications
   - **Action**: Create Telegram bot
   - **Owner**: Farah

### **Technical Debt**
- [ ] Add comprehensive error handling in all agents
- [ ] Implement retry logic for API calls
- [ ] Add logging throughout the system
- [ ] Optimize PDF parsing performance
- [ ] Add rate limiting for GLM API calls

---

## 📞 Team Communication

### **Daily Standup Questions**
1. What did you complete yesterday?
2. What are you working on today?
3. Any blockers?

### **Weekly Review**
- Review progress against timeline
- Update PLAN.md with actual progress
- Identify and resolve blockers
- Plan next week's tasks

### **Code Review Guidelines**
- See GITHUB_MANAGEMENT.md
- All PRs require 1 approval
- Run tests before submitting PR
- Update documentation if needed

---

## 🎓 Learning Resources

### **LangGraph**
- Official docs: https://langchain-ai.github.io/langgraph/
- See `backend/agents/orchestrator.py` for implementation

### **Firebase**
- Firestore: https://firebase.google.com/docs/firestore
- Storage: https://firebase.google.com/docs/storage
- Admin SDK: https://firebase.google.com/docs/admin/setup

### **FastAPI**
- Official docs: https://fastapi.tiangolo.com/
- See `backend/main.py` for setup

### **Z.AI GLM API**
- Documentation: https://open.bigmodel.cn/dev/api
- See `backend/core/glm_client.py` for implementation

---

## 📅 Milestones

- [x] **M1**: Project setup and Agent A (Completed)
- [ ] **M2**: All agents implemented (Target: TBD)
- [ ] **M3**: API and Frontend complete (Target: TBD)
- [ ] **M4**: Integration testing complete (Target: TBD)
- [ ] **M5**: Production deployment (Target: TBD)

---

## 🏆 Success Criteria

### **Minimum Viable Product (MVP)**
- [ ] Upload PDF documents
- [ ] Extract ≥10 fields automatically
- [ ] Detect delays and cost variances
- [ ] Generate compliance score
- [ ] Send Telegram alerts
- [ ] Generate PDF/XLSX reports

### **Stretch Goals**
- [ ] Real-time collaboration
- [ ] Mobile app
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Integration with external tools (Jira, Slack)

---

**Last Updated**: 2024-01-XX
**Next Review**: TBD
**Document Owner**: Chip/Azim
