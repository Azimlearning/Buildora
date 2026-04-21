# Buildora

AI-powered construction project management system for Malaysian construction projects.

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Azimlearning/Buildora.git
cd Buildora

# 2. Copy environment template
cp .env.example .env
# Edit .env with your API keys

# 3. Start all services
docker-compose up -d

# 4. Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# MinIO Console: http://localhost:9001
```

## Team Members & Responsibilities

| Member | Component | Branch Prefix |
|--------|-----------|---------------|
| **Chip/Azim** | Backend + Orchestrator + Agent A | `azim/` |
| **Farah** | Frontend + Agent D | `farah/` |
| **Khair** | Database + Redis + Agent B | `khair/` |
| **Harry** | Agent B (Telegram) + Agent C (CIDB data) | `harry/` |
| **Aliasya** | Agent C (Compliance logic) | `ali/` |

## Architecture

```
PM Browser → React Frontend → FastAPI → LangGraph Orchestrator
                                            ↓
                    ┌───────────────────────┼───────────────────────┐
                    ↓                       ↓                       ↓
                Agent A              Agent B              Agent C → Agent D
            (Doc Reader)           (Monitor)           (Compliance)  (Reports)
                    ↓                       ↓                       ↓
                MinIO                  Telegram              PDF + XLSX
                    └───────────────── Redis ─────────────────┘
```

## System Components

- **Agent A**: PDF parsing & field extraction (pdfplumber, PyMuPDF, Tesseract OCR, GLM)
- **Agent B**: Delay & cost variance monitoring (>3 days, >8% triggers Telegram alerts)
- **Agent C**: CIDB BISQ compliance scoring (conditional execution)
- **Agent D**: Report generation (branded PDF + XLSX cost tracker)
- **Orchestrator**: LangGraph state machine coordinating all agents
- **Redis**: Shared state store for inter-agent communication
- **PostgreSQL**: Project records and metadata
- **MinIO**: Document storage

## Development Workflow

### IMPORTANT: Read These First
1. **[GITHUB_MANAGEMENT.md](./GITHUB_MANAGEMENT.md)** - Git workflow, branching, PR process
2. **[FILE_STRUCTURE.md](./FILE_STRUCTURE.md)** - Mandatory folder structure

### Starting Work
```bash
# Always work in feature branches
git checkout main
git pull origin main
git checkout -b <your-name>/<feature-name>

# Make changes, commit, push
git add <files>
git commit -m "[Component] Description"
git push origin <your-name>/<feature-name>

# Create PR on GitHub for review
```

### Running Tests
```bash
# Run all tests
docker-compose exec backend pytest

# Run specific test
docker-compose exec backend pytest backend/tests/test_orchestrator.py

# Run with coverage
docker-compose exec backend pytest --cov=backend
```

## Project Structure

```
buildora/
├── backend/              # Python/FastAPI
│   ├── agents/          # AI agents + orchestrator
│   ├── api/             # REST endpoints
│   ├── core/            # Shared utilities
│   ├── db/              # Database models
│   └── tests/           # Test suite
├── frontend/            # React + Vite + Tailwind
│   └── src/
│       ├── components/  # UI components
│       ├── pages/       # Route pages
│       └── api/         # API client
└── data/                # Demo data
```

See [FILE_STRUCTURE.md](./FILE_STRUCTURE.md) for complete structure.

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `GLM_API_KEY` - Z.AI GLM API key for field extraction
- `TELEGRAM_BOT_TOKEN` - Telegram bot for Agent B alerts
- `POSTGRES_*` - Database credentials
- `REDIS_PASSWORD` - Redis password
- `MINIO_*` - Object storage credentials

## Tech Stack

**Backend:**
- FastAPI (Python 3.10+)
- LangGraph (agent orchestration)
- pdfplumber, PyMuPDF, Tesseract (PDF parsing)
- SQLAlchemy + PostgreSQL
- Redis (state management)
- MinIO (document storage)

**Frontend:**
- React 18
- Vite
- Tailwind CSS

**Infrastructure:**
- Docker + Docker Compose
- PostgreSQL 15
- Redis 7
- MinIO

## API Endpoints

```
GET  /                    # Health check
GET  /health              # Detailed health status
POST /api/upload          # Upload project documents
GET  /api/projects        # List projects
POST /api/projects        # Create project
POST /api/milestones      # Update milestone
GET  /api/reports/{id}    # Generate & download reports
```

## Testing Strategy

See `backend/tests/` for test suite:
- Day 1: GLM response parsing
- Day 2: State handoff between agents
- Day 3-4: Field extraction (≥10 fields, ≥80% accuracy)
- Day 5-6: Delay & cost variance detection
- Day 8: Compliance scoring
- Day 10: Report generation
- Day 11: Full pipeline E2E (<15s)

## Demo Mode

For judges/demo purposes:
```bash
# Access demo mode with pre-loaded data
http://localhost:5173/demo
```

## Troubleshooting

**Services won't start:**
```bash
docker-compose down -v
docker-compose up --build
```

**Database connection issues:**
```bash
docker-compose logs postgres
docker-compose restart postgres
```

**Redis connection issues:**
```bash
docker-compose logs redis
docker-compose exec redis redis-cli -a <REDIS_PASSWORD> ping
```

## Contributing

1. Read [GITHUB_MANAGEMENT.md](./GITHUB_MANAGEMENT.md)
2. Create feature branch: `<your-name>/<feature>`
3. Follow [FILE_STRUCTURE.md](./FILE_STRUCTURE.md)
4. Write tests for new features
5. Create PR with clear description
6. Get 1+ approval before merging

## License

Proprietary - UM Hackathon 2024

## Support

- Git issues: Ask Chip/Azim
- Architecture questions: Check reference docs in `Ref documents/`
- Bugs: Create GitHub issue
