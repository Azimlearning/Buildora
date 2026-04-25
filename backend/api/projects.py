from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.core.firebase_client import get_firestore_client
from typing import List, Dict, Any

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    description: str = ""


def calculate_health_score(project: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate project health score based on compliance, schedule, and cost.

    Health = 40% schedule + 35% cost + 25% compliance

    Args:
        project: Project document from Firestore

    Returns:
        Dict with 'score' and 'breakdown'
    """
    compliance = project.get("compliance_score", {})

    # Compliance component (0-100)
    compliance_score = compliance.get("score", 0) if isinstance(compliance, dict) else 0

    # Schedule component (placeholder - needs milestone data)
    monitoring = project.get("monitoring_results", {})
    delay_alerts = monitoring.get("delay_alerts", []) if isinstance(monitoring, dict) else []
    if delay_alerts:
        max_delay = max(alert.get("delay_days", 0) for alert in delay_alerts)
        schedule_score = max(0, 100 - min(max_delay * 5, 100))
    else:
        schedule_score = 100

    # Cost component from Agent B variance output
    cost_alerts = monitoring.get("cost_variance_alerts", []) if isinstance(monitoring, dict) else []
    if cost_alerts:
        max_variance = max(abs(alert.get("variance_percentage", 0)) for alert in cost_alerts)
        cost_score = max(0, 100 - min(int(max_variance * 2), 100))
    else:
        cost_score = 100

    health = (
        schedule_score * 0.40 +
        cost_score * 0.35 +
        compliance_score * 0.25
    )

    return {
        "score": round(health, 1),
        "breakdown": {
            "schedule": round(schedule_score, 1),
            "cost": round(cost_score, 1),
            "compliance": round(compliance_score, 1)
        }
    }


@router.get("/projects")
async def list_projects():
    db = get_firestore_client()
    projects = await db.list_projects()

    # Add health score to each project
    for project in projects:
        if "health_score" not in project:
            health_data = calculate_health_score(project)
            project["health_score"] = health_data["score"]
            project["health_breakdown"] = health_data["breakdown"]

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
    health_data = calculate_health_score(project)
    project["health_score"] = health_data["score"]
    project["health_breakdown"] = health_data["breakdown"]

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
    health_data = calculate_health_score(project)
    health = health_data["score"]
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
        anomaly_alerts = monitoring_results.get("anomaly_alerts", [])

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

        for alert in anomaly_alerts[:2]:
            alerts.append({
                "id": len(alerts) + 1,
                "type": "urgent" if alert.get("severity") == "critical" else "warning",
                "text": alert.get("impact_description", "Monitoring anomaly detected")
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
    - All uploaded documents metadata
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
        await db.delete_project(project_id)
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

