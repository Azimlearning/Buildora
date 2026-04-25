"""
Notifications API Router
=========================
REST endpoints for Agent D notifications.

Provides:
  GET  /notifications/{project_id}   — fetch project-specific alerts
  POST /notifications/{project_id}   — trigger Agent D manually (demo)
  POST /notifications/test-telegram  — send a test message to Telegram

Author: Khaidhir (Agent D)
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel

from backend.agents.agent_d.agent import AgentD, DEMO_ALERTS
from backend.agents.agent_d.telegram_notifier import TelegramNotifier

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ── Response models ──────────────────────────────────────────────

class TelegramTestRequest(BaseModel):
    message: Optional[str] = None


# ── In-memory notification store (demo mode) ─────────────────────
# In production this would come from Firestore.
_notification_store: dict[str, list[dict]] = {}


def _build_project_alerts(project: dict) -> list[dict]:
    """
    Generate context-aware alerts derived from the actual project state.

    Priority order for alert generation:
    1. Compliance gaps → doc_submission / permit_renewal alerts
    2. Delay alerts from Agent B monitoring results
    3. Cost variance alerts from Agent B monitoring results
    4. Low health score → general warning
    5. Missing reports → general info
    Falls back to DEMO_ALERTS only when zero real data is available.
    """
    from datetime import datetime, timedelta
    import uuid

    alerts: list[dict] = []
    now = datetime.utcnow()

    project_name = project.get("name", project.get("project_name_extracted", ""))

    # ── 1. Compliance gaps ───────────────────────────────────────
    compliance = project.get("compliance_score", {})
    if isinstance(compliance, dict):
        score = compliance.get("score", 100)
        gaps: list[dict] = compliance.get("gaps", [])
        mandatory_gaps = [g for g in gaps if g.get("mandatory", False)]
        optional_gaps = [g for g in gaps if not g.get("mandatory", False)]

        if mandatory_gaps:
            alerts.append({
                "id": str(uuid.uuid4()),
                "category": "doc_submission",
                "severity": "critical",
                "title": f"{len(mandatory_gaps)} Mandatory Document(s) Missing",
                "message": (
                    f"The following mandatory documents must be submitted to avoid compliance "
                    f"penalties: {', '.join(g.get('description_en', g.get('name', 'Unknown')) for g in mandatory_gaps[:3])}."
                ),
                "days_remaining": 7,
                "due_date": (now + timedelta(days=7)).strftime("%Y-%m-%d"),
                "project_id": project.get("id", ""),
                "project_name": project_name,
                "status": "active",
                "created_at": now.isoformat(),
            })

        if optional_gaps and score < 80:
            alerts.append({
                "id": str(uuid.uuid4()),
                "category": "permit_renewal",
                "severity": "medium",
                "title": f"CIDB Compliance Score at {round(score)}%",
                "message": (
                    f"{len(optional_gaps)} optional compliance item(s) outstanding. "
                    f"Resolving these will improve your CIDB standing and unlock higher-value contracts."
                ),
                "days_remaining": 21,
                "due_date": (now + timedelta(days=21)).strftime("%Y-%m-%d"),
                "project_id": project.get("id", ""),
                "project_name": project_name,
                "status": "active",
                "created_at": now.isoformat(),
            })

    # ── 2. Delay alerts from Agent B ─────────────────────────────
    monitoring = project.get("monitoring_results", {})
    if isinstance(monitoring, dict):
        delay_alerts = monitoring.get("delay_alerts", [])
        for da in delay_alerts[:3]:
            delay_days = da.get("delay_days", 0)
            severity = "critical" if delay_days >= 5 else "high" if delay_days >= 3 else "medium"
            alerts.append({
                "id": str(uuid.uuid4()),
                "category": "delay_detected",
                "severity": severity,
                "title": da.get("title", f"Schedule Delay: {delay_days} day(s) overdue"),
                "message": da.get(
                    "impact_description",
                    f"Milestone is overdue by {delay_days} day(s). "
                    f"Current variance exceeds the {max(1, delay_days - 2)}-day threshold.",
                ),
                "days_remaining": 0,
                "due_date": now.strftime("%Y-%m-%d"),
                "project_id": project.get("id", ""),
                "project_name": project_name,
                "status": "active",
                "created_at": now.isoformat(),
            })

        # ── 3. Cost variance alerts from Agent B ─────────────────
        cost_alerts = monitoring.get("cost_variance_alerts", [])
        for ca in cost_alerts[:3]:
            variance_pct = abs(ca.get("variance_percentage", 0))
            severity = "critical" if variance_pct >= 20 else "high" if variance_pct >= 10 else "medium"
            alerts.append({
                "id": str(uuid.uuid4()),
                "category": "cost_overrun",
                "severity": severity,
                "title": ca.get("title", f"Cost Variance: {variance_pct:.1f}% over budget"),
                "message": ca.get(
                    "impact_description",
                    f"Cost variance of {variance_pct:.1f}% detected. "
                    f"Review sub-contractor claims and approved variation orders.",
                ),
                "days_remaining": 14,
                "due_date": (now + timedelta(days=14)).strftime("%Y-%m-%d"),
                "project_id": project.get("id", ""),
                "project_name": project_name,
                "status": "active",
                "created_at": now.isoformat(),
            })

    # ── 4. Low overall health score ──────────────────────────────
    health_score = project.get("health_score")
    if health_score is not None and health_score < 70:
        alerts.append({
            "id": str(uuid.uuid4()),
            "category": "general",
            "severity": "high" if health_score < 55 else "medium",
            "title": f"Project Health at {round(health_score)}% — Action Required",
            "message": (
                f"Overall project health is below the 70% threshold. "
                f"Review schedule compliance, outstanding payments, and compliance gaps to improve your score."
            ),
            "days_remaining": 30,
            "due_date": (now + timedelta(days=30)).strftime("%Y-%m-%d"),
            "project_id": project.get("id", ""),
            "project_name": project_name,
            "status": "active",
            "created_at": now.isoformat(),
        })

    # ── 5. Missing reports ───────────────────────────────────────
    reports = project.get("reports", {})
    if not reports or not isinstance(reports, dict):
        alerts.append({
            "id": str(uuid.uuid4()),
            "category": "doc_submission",
            "severity": "info",
            "title": "Project Reports Not Yet Generated",
            "message": (
                "No project reports have been generated. Generate the PDF progress report "
                "and XLSX cost tracker for stakeholder review."
            ),
            "days_remaining": None,
            "project_id": project.get("id", ""),
            "project_name": project_name,
            "status": "active",
            "created_at": now.isoformat(),
        })

    # ── Fallback to generic demo alerts if no real data found ────
    if not alerts:
        agent = AgentD(firestore_client=None, use_demo_alerts=True)
        project_id = project.get("id", "demo")
        alerts = agent._enrich_alerts(DEMO_ALERTS, project_id, project_name)

    return alerts


def _get_project_notifications(project_id: str, project: Optional[dict] = None) -> list[dict]:
    """
    Return cached notifications or regenerate from current project state.
    Pass project data to force regeneration for that project.
    """
    if project:
        # Always regenerate when fresh project data is provided
        enriched = _build_project_alerts(project)
        _notification_store[project_id] = enriched
    elif project_id not in _notification_store:
        # No project data — fall back to demo alerts
        agent = AgentD(firestore_client=None, use_demo_alerts=True)
        enriched = agent._enrich_alerts(DEMO_ALERTS, project_id, "")
        _notification_store[project_id] = enriched

    return _notification_store[project_id]


# ── Endpoints ────────────────────────────────────────────────────

@router.get("/{project_id}")
async def get_notifications(project_id: str, status: Optional[str] = None):
    """
    Get project-specific notifications.

    Attempts to fetch the live project from Firestore so alerts reflect
    real compliance, schedule, and cost data.  Falls back gracefully.

    Query params:
        status — filter by 'active', 'resolved', 'dismissed'
    """
    # Try to load real project data from Firestore
    project_data: Optional[dict] = None
    try:
        from backend.core.firebase_client import get_firestore_client
        db = get_firestore_client()
        project_data = await db.get_project(project_id)
        if project_data:
            project_data["id"] = project_id
    except Exception:
        pass  # Graceful fallback

    notifications = _get_project_notifications(project_id, project_data)

    if status:
        notifications = [n for n in notifications if n.get("status") == status]

    # Sort: critical first, then by days_remaining ascending
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    notifications.sort(
        key=lambda n: (
            severity_order.get(n.get("severity", "medium"), 2),
            n.get("days_remaining") if n.get("days_remaining") is not None else 999,
        )
    )

    return {
        "project_id": project_id,
        "count": len(notifications),
        "notifications": notifications,
    }


@router.post("/{project_id}")
async def trigger_notifications(project_id: str):
    """
    Trigger Agent D to re-process alerts for a project (manual refresh).
    """
    # Force refresh from Firestore
    project_data: Optional[dict] = None
    try:
        from backend.core.firebase_client import get_firestore_client
        db = get_firestore_client()
        project_data = await db.get_project(project_id)
        if project_data:
            project_data["id"] = project_id
    except Exception:
        pass

    enriched = _get_project_notifications(project_id, project_data)

    return {
        "project_id": project_id,
        "processed_at": __import__("datetime").datetime.utcnow().isoformat(),
        "total_alerts": len(enriched),
        "notifications": enriched,
    }


@router.post("/test-telegram")
async def test_telegram(body: TelegramTestRequest):
    """
    Send a test message to Telegram to verify the bot is configured.
    """
    notifier = TelegramNotifier()

    test_alert = {
        "category": "general",
        "severity": "info",
        "title": "Buildora Test Message",
        "message": body.message or "✅ Telegram integration is working! Agent D is live.",
        "project_name": "Test Project",
    }

    result = await notifier.send_alert(test_alert)

    if not result.get("success"):
        raise HTTPException(
            status_code=502,
            detail=f"Telegram send failed: {result.get('error', 'unknown')}",
        )

    return {"status": "ok", "telegram_result": result}
