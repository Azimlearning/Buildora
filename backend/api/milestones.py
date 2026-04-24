from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from backend.core.firebase_client import get_firestore_client

router = APIRouter()

class MilestoneCreate(BaseModel):
    project_id: str
    title: str
    due_date: str
    status: str = "pending"

@router.post("/milestones")
async def add_milestone(milestone: MilestoneCreate):
    db = get_firestore_client()
    # Assuming milestones are saved as part of project updates or a new collection
    # Here we can just save it as a document in a 'milestones' collection if we implement it,
    # but for now we'll mock returning a success response
    return {"status": "success", "milestone": milestone.model_dump()}

@router.get("/milestones/{project_id}")
async def get_milestones(project_id: str):
    # Mock data for now, ideally fetch from Firestore
    return {"project_id": project_id, "milestones": []}
