from fastapi import APIRouter, HTTPException
from backend.core.firebase_client import get_firestore_client

router = APIRouter()

# CIDB checklist categories (deterministic fallback when Agent C hasn't run yet)
DEFAULT_CATEGORIES = [
    {
        "name": "Contractor Registration",
        "items": [
            {"label": "CIDB Grade Registration", "status": "warn"},
            {"label": "PKK Certification", "status": "warn"},
            {"label": "SSM Company Registration", "status": "warn"},
        ],
    },
    {
        "name": "Insurance & Bonds",
        "items": [
            {"label": "OSHC Insurance (valid)", "status": "warn"},
            {"label": "Performance Bond 5%", "status": "warn"},
            {"label": "Public Liability RM 1M", "status": "warn"},
        ],
    },
    {
        "name": "Structural & Engineering",
        "items": [
            {"label": "Structural PE Endorsement", "status": "warn"},
            {"label": "Geotechnical Report", "status": "warn"},
            {"label": "Load Calculation Submission", "status": "warn"},
        ],
    },
    {
        "name": "Safety & Permits",
        "items": [
            {"label": "BOMBA Fire Safety Clearance", "status": "warn"},
            {"label": "Fire Escape Compliance", "status": "warn"},
            {"label": "Site Safety Plan (HIRARC)", "status": "warn"},
            {"label": "OSH Officer Appointment", "status": "warn"},
        ],
    },
]


@router.get("/compliance/{project_id}")
async def get_compliance(project_id: str):
    """Return Agent C compliance results for a project, falling back to defaults."""
    db = get_firestore_client()
    project = await db.get_project(project_id)

    if project:
        stored = project.get("compliance_score", {})
        if stored and isinstance(stored, dict):
            # Agent C has run — return its output enriched with `available: true`
            score = stored.get("score", 0)
            status = stored.get("status", "warning")
            gaps = stored.get("gaps", [])

            # Map gaps to category items
            gap_ids = {g.get("id", "") for g in gaps}
            categories = stored.get("categories", DEFAULT_CATEGORIES)

            return {
                "project_id": project_id,
                "available": True,
                "score": round(score),
                "status": status,
                "gaps": gaps,
                "categories": categories,
            }

    # Project exists but Agent C hasn't run yet, or project not found
    # Return partial/default data so UI shows something useful
    return {
        "project_id": project_id,
        "available": True,
        "score": 0,
        "status": "pending",
        "gaps": [],
        "categories": DEFAULT_CATEGORIES,
        "note": "Compliance analysis in progress — run the agent pipeline to get full results.",
    }

