from fastapi import APIRouter, HTTPException
from backend.core.firebase_client import get_firestore_client

router = APIRouter()

@router.get("/reports/{project_id}")
async def get_reports(project_id: str):
    db = get_firestore_client()
    reports = await db.get_reports(project_id)
    return {"project_id": project_id, "reports": reports}

@router.post("/reports/{project_id}/generate")
async def generate_report(project_id: str):
    # This would normally trigger Agent E
    return {"status": "success", "message": "Report generation triggered"}
