# 🚀 Buildora Quick Start Guide

**Current Version**: v0.1 (Agents A, C, E + Full API)  
**Status**: Ready for Testing  
**Missing**: Agent B (Monitor), Agent D (Telegram)

---

## ✅ Validation Complete

- ✅ All Python files compile successfully
- ✅ Backend imports working
- ✅ All API routers integrated
- ✅ Integration test passes
- ✅ Frontend configured

---

## 🎯 Start Development Servers

### Backend Server (Terminal 1)

```bash
# IMPORTANT: Run from project root, not backend directory
cd "C:\Users\User\Documents\Coding\Hackathon\UM Hackathon - Buildora\Buildora"
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Test**: Open http://localhost:8000/docs (Swagger UI)

---

### Frontend Server (Terminal 2)

```bash
cd "C:\Users\User\Documents\Coding\Hackathon\UM Hackathon - Buildora\Buildora\frontend"
npm install  # First time only
npm run dev
```

**Test**: Open http://localhost:5173

---

## 🧪 Quick Tests

### Test Backend API
```bash
# Health check
curl http://localhost:8000/

# Swagger UI (Interactive)
# Open: http://localhost:8000/docs
```

### Test Agent Pipeline
```bash
cd "C:\Users\User\Documents\Coding\Hackathon\UM Hackathon - Buildora\Buildora"
pytest backend/tests/test_integration_pipeline.py -v
```

---

## 📊 Available Endpoints

**Base URL**: http://localhost:8000

- `GET /` - Health check
- `GET /docs` - Swagger UI
- `POST /api/upload` - Upload documents
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `GET /api/projects/:id` - Get project
- `POST /api/milestones` - Add milestone
- `GET /api/reports/:id` - Get reports
- `POST /api/reports/:id/generate` - Generate report
- `GET /api/compliance/:id` - Get compliance score

---

## 🎬 Current Pipeline Flow

```
Upload PDF → Agent A (Extract Fields) → Agent C (Compliance Check) → Agent E (Generate Reports)
```

**Note**: Agent B (Monitor) and Agent D (Telegram) are placeholders.

---

## 🐛 Troubleshooting

**Port already in use:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Import errors:**
```bash
# Verify you're in project root
cd "C:\Users\User\Documents\Coding\Hackathon\UM Hackathon - Buildora\Buildora"
python -c "from backend.main import app; print('OK')"
```

---

## 📚 More Documentation

- **Full Testing Guide**: See `TESTING.md`
- **Integration Status**: See `INTEGRATION_STATUS.md`
- **Next Steps**: See `NEXT_STEPS.md`
- **Project Plan**: See `PLAN.md`

---

**Happy Testing! 🎉**
