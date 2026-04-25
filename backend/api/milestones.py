from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
from backend.core.firebase_client import get_firestore_client

router = APIRouter()

class MilestoneCreate(BaseModel):
    project_id: str
    title: str
    due_date: str
    planned_start_date: Optional[str] = None
    actual_start_date: Optional[str] = None
    actual_end_date: Optional[str] = None
    status: str = "not_started"
    budget_allocated: float = 0.0
    budget_spent: float = 0.0

@router.post("/milestones")
async def add_milestone(milestone: MilestoneCreate):
    db = get_firestore_client()
    project = await db.get_project(milestone.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    milestone_data = {
        "milestone_id": str(uuid.uuid4()),
        "name": milestone.title,
        "planned_start_date": milestone.planned_start_date,
        "planned_end_date": milestone.due_date,
        "actual_start_date": milestone.actual_start_date,
        "actual_end_date": milestone.actual_end_date,
        "status": milestone.status,
        "budget_allocated": milestone.budget_allocated,
        "budget_spent": milestone.budget_spent,
    }

    milestones = list(project.get("milestones", []))
    milestones.append(milestone_data)
    await db.update_project(milestone.project_id, {"milestones": milestones})

    return {"status": "success", "milestone": milestone_data}

@router.get("/milestones/{project_id}")
async def get_milestones(project_id: str):
    db = get_firestore_client()
    project = await db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {"project_id": project_id, "milestones": project.get("milestones", [])}
