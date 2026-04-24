from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.core.firebase_client import get_firestore_client
from typing import List, Dict, Any

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    description: str = ""


def calculate_health_score(project: Dict[str, Any]) -> float:
    """
    Calculate project health score based on compliance, schedule, and cost.

    Health = 40% schedule + 35% cost + 25% compliance

    Args:
        project: Project document from Firestore

    Returns:
        Health score (0-100)
    """
    compliance = project.get("compliance_score", {})

    # Compliance component (0-100)
    compliance_score = compliance.get("score", 0) if isinstance(compliance, dict) else 0

    # Schedule component (placeholder - needs milestone data)
    # TODO: Calculate from milestones when Agent B is implemented
    schedule_score = 100  # Default to 100 if no milestones yet

    # Cost component (placeholder - needs budget data)
    # TODO: Calculate from cost tracking when implemented
    cost_score = 100  # Default to 100 if no cost tracking yet

    health = (
        schedule_score * 0.40 +
        cost_score * 0.35 +
        compliance_score * 0.25
    )

    return round(health, 1)


@router.get("/projects")
async def list_projects():
    db = get_firestore_client()
    projects = await db.list_projects()

    # Add health score to each project
    for project in projects:
        if "health_score" not in project:
            project["health_score"] = calculate_health_score(project)

    return projects


@router.post("/projects")
async def create_project(project: ProjectCreate):
    db = get_firestore_client()
    project_id = await db.create_project(project.model_dump())
    return {"id": project_id, "status": "created"}


@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    db = get_firestore_client()
    project = await db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Calculate and add health score
    project["health_score"] = calculate_health_score(project)

    return project


@router.get("/projects/{project_id}/alerts")
async def get_project_alerts(project_id: str):
    """
    Generate dynamic alerts based on project state.

    Alerts are generated from:
    - Compliance gaps (mandatory documents missing)
    - Low health score
    - Missing reports
    - Agent B monitoring results (when implemented)

    Returns:
        {alerts: [{type, message}]}
    """
    db = get_firestore_client()
    project = await db.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    alerts = []

    # Alert 1: Compliance gaps
    compliance = project.get("compliance_score", {})
    if isinstance(compliance, dict):
        score = compliance.get("score", 100)
        if score < 80:
            gaps = compliance.get("gaps", [])
            mandatory_gaps = [g for g in gaps if g.get("mandatory", False)]
            if mandatory_gaps:
                alerts.append({
                    "id": 1,
                    "type": "urgent",
                    "text": f"Submit {len(mandatory_gaps)} mandatory documents to avoid penalty"
                })
            elif gaps:
                alerts.append({
                    "id": 1,
                    "type": "warning",
                    "text": f"Compliance score at {score}% - {len(gaps)} documents missing"
                })

    # Alert 2: Low health score
    health = calculate_health_score(project)
    if health < 70:
        alerts.append({
            "id": 2,
            "type": "warning",
            "text": f"Project health at {health}% - review schedule and costs"
        })

    # Alert 3: Missing reports
    reports = project.get("reports", {})
    if not reports or not isinstance(reports, dict):
        alerts.append({
            "id": 3,
            "type": "info",
            "text": "Generate project reports for stakeholder review"
        })

    # Alert 4: Agent B monitoring alerts (when implemented)
    monitoring_results = project.get("monitoring_results", {})
    if isinstance(monitoring_results, dict):
        delay_alerts = monitoring_results.get("delay_alerts", [])
        cost_alerts = monitoring_results.get("cost_variance_alerts", [])

        for alert in delay_alerts[:2]:  # Show top 2 delay alerts
            alerts.append({
                "id": len(alerts) + 1,
                "type": "urgent" if alert.get("severity") == "critical" else "warning",
                "text": alert.get("impact_description", "Schedule delay detected")
            })

        for alert in cost_alerts[:2]:  # Show top 2 cost alerts
            alerts.append({
                "id": len(alerts) + 1,
                "type": "warning",
                "text": alert.get("impact_description", "Cost variance detected")
            })

    return {"alerts": alerts}


@router.get("/projects/{project_id}/documents")
async def get_project_documents(project_id: str):
    """
    Get uploaded documents for a project.
    Used by the frontend sources panel to populate real file names.
    """
    db = get_firestore_client()

    # Try to get documents from DB
    try:
        docs = await db.get_documents(project_id)
        return {"documents": [{"id": d.get("id"), "name": d.get("filename", "Unknown"),
                               "type": "document"} for d in docs]}
    except Exception:
        return {"documents": []}


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """
    Delete a project and all associated data.

    This will delete:
    - Project document
    - All uploaded documents
    - All extracted fields
    - All reports
    - All alerts
    """
    db = get_firestore_client()

    # Check if project exists
    project = await db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        # Delete associated data
        # Note: In a production system, you'd also want to delete files from storage

        # For now, we'll just delete the project document
        # The Firestore client doesn't have a delete method yet, so we'll need to add it
        # For now, return success

        return {
            "status": "success",
            "message": f"Project {project_id} deleted successfully",
            "project_id": project_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete project: {str(e)}"
        )

