"""
Notifications API Router
=========================
REST endpoints for Agent D notifications.

Provides:
  GET  /notifications/{project_id}   — fetch alerts for a project
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
# For the hackathon demo we keep an in-memory dict keyed by project_id.
_notification_store: dict[str, list[dict]] = {}


def _get_demo_notifications(project_id: str) -> list[dict]:
    """Return stored notifications or generate demo ones on first access."""
    if project_id not in _notification_store:
        agent = AgentD(firestore_client=None, use_demo_alerts=True)
        enriched = agent._enrich_alerts(DEMO_ALERTS, project_id, "")
        _notification_store[project_id] = enriched
    return _notification_store[project_id]


# ── Endpoints ────────────────────────────────────────────────────

@router.get("/{project_id}")
async def get_notifications(project_id: str, status: Optional[str] = None):
    """
    Get notifications for a project.

    Query params:
        status — filter by 'active', 'resolved', 'dismissed'
    """
    notifications = _get_demo_notifications(project_id)

    if status:
        notifications = [n for n in notifications if n.get("status") == status]

    # Sort: critical first, then by days_remaining ascending
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    notifications.sort(
        key=lambda n: (
            severity_order.get(n.get("severity", "medium"), 2),
            n.get("days_remaining", 999),
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
    Trigger Agent D to process alerts for a project (demo/manual trigger).
    """
    agent = AgentD(firestore_client=None, use_demo_alerts=True)
    result = await agent.process_alerts(
        project_id=project_id,
        alerts=[],
        project_name="",
    )

    # Store the enriched notifications
    _notification_store[project_id] = result.get("notifications", [])

    return result


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
