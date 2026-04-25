"""
Health Score API - Calculate project health based on agent outputs
===================================================================
Combines data from Agent B (monitoring), Agent C (compliance), and Agent D (alerts)
to generate a comprehensive project health score (0-100).

Author: Buildora Team
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from backend.core.firebase_client import get_firestore_client

router = APIRouter()


def calculate_health_score(
    monitoring_results: Dict[str, Any],
    compliance_score: Dict[str, Any],
    notifications: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate project health score based on agent outputs.

    Algorithm:
    - Start with 100 points
    - Deduct points for delays, cost overruns, compliance gaps, and alerts
    - Return score (0-100) with breakdown by category

    Args:
        monitoring_results: Agent B output (delays, cost variance)
        compliance_score: Agent C output (CIDB compliance)
        notifications: Agent D output (alert count)

    Returns:
        {
            "health_score": int (0-100),
            "status": str ("healthy" | "warning" | "critical"),
            "breakdown": {
                "monitoring_penalty": int,
                "compliance_penalty": int,
                "alerts_penalty": int
            },
            "details": {
                "delays": int,
                "cost_variance": float,
                "compliance": float,
                "critical_alerts": int
            }
        }
    """
    score = 100
    breakdown = {
        "monitoring_penalty": 0,
        "compliance_penalty": 0,
        "alerts_penalty": 0
    }

    # Extract metrics
    total_alerts = monitoring_results.get("total_alerts", 0)
    critical_alerts = monitoring_results.get("critical_alerts", 0)
    delay_alerts = len(monitoring_results.get("delay_alerts", []))
    cost_alerts = len(monitoring_results.get("cost_variance_alerts", []))
    compliance = compliance_score.get("score", 100)

    # 1. Monitoring Penalty (max -40 points)
    # - Critical alerts: -10 points each (max -30)
    # - Delay alerts: -5 points each (max -20)
    # - Cost variance alerts: -5 points each (max -20)
    monitoring_penalty = min(40, (critical_alerts * 10) + (delay_alerts * 5) + (cost_alerts * 5))
    breakdown["monitoring_penalty"] = monitoring_penalty
    score -= monitoring_penalty

    # 2. Compliance Penalty (max -40 points)
    # - Linear penalty based on compliance score
    # - 100% compliance = 0 penalty
    # - 0% compliance = 40 penalty
    compliance_penalty = int((100 - compliance) * 0.4)
    breakdown["compliance_penalty"] = compliance_penalty
    score -= compliance_penalty

    # 3. Alerts Penalty (max -20 points)
    # - Based on total notification count
    # - 0 alerts = 0 penalty
    # - 10+ alerts = 20 penalty
    alerts_count = notifications.get("total_alerts", 0)
    alerts_penalty = min(20, alerts_count * 2)
    breakdown["alerts_penalty"] = alerts_penalty
    score -= alerts_penalty

    # Clamp score to 0-100
    score = max(0, min(100, score))

    # Determine status
    if score >= 80:
        status = "healthy"
    elif score >= 60:
        status = "warning"
    else:
        status = "critical"

    return {
        "health_score": score,
        "status": status,
        "breakdown": breakdown,
        "details": {
            "delays": delay_alerts,
            "cost_variance": cost_alerts,
            "compliance": compliance,
            "critical_alerts": critical_alerts,
            "total_alerts": total_alerts
        }
    }


@router.get("/projects/{project_id}/health")
async def get_project_health(project_id: str):
    """
    Calculate and return project health score.

    Reads data from Firestore (written by agents) and calculates health score.
    """
    try:
        db = get_firestore_client()

        # Fetch project data
        project = await db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get monitoring results (Agent B)
        monitoring_results = project.get("monitoring_results", {})
        if not monitoring_results:
            # Try to fetch from separate collection
            monitoring_results = {
                "total_alerts": 0,
                "critical_alerts": 0,
                "delay_alerts": [],
                "cost_variance_alerts": []
            }

        # Get compliance score (Agent C)
        compliance_score = project.get("compliance_score", {"score": 100})

        # Get notifications count (Agent D)
        notifications = {
            "total_alerts": project.get("notifications_sent", 0)
        }

        # Calculate health score
        health_data = calculate_health_score(
            monitoring_results,
            compliance_score,
            notifications
        )

        # Update project with health score
        await db.update_project(project_id, {
            "health_score": health_data["health_score"],
            "health_status": health_data["status"],
            "health_breakdown": health_data["breakdown"]
        })

        return {
            "project_id": project_id,
            **health_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health calculation failed: {str(e)}")


@router.post("/projects/{project_id}/health/recalculate")
async def recalculate_health(project_id: str):
    """
    Force recalculation of project health score.

    Useful after manual data updates or agent re-runs.
    """
    return await get_project_health(project_id)
