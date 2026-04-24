"""
Buildora Backend - FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Buildora API",
    description="AI-powered construction project management system",
    version="0.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Buildora API",
        "version": "0.1.0"
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "api": "up",
            "database": "pending",
            "redis": "pending",
            "minio": "pending"
        }
    }

# TODO: Import and include routers
# from backend.api import upload, projects, milestones, reports
# app.include_router(upload.router, prefix="/api", tags=["upload"])
# app.include_router(projects.router, prefix="/api", tags=["projects"])
# app.include_router(milestones.router, prefix="/api", tags=["milestones"])
# app.include_router(reports.router, prefix="/api", tags=["reports"])

# Agent D: Notifications & Alerts
from backend.api.notifications import router as notifications_router
app.include_router(notifications_router)

