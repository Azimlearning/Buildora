import pytest
from unittest.mock import AsyncMock

from backend.agents.agent_b.agent import AgentB
from backend.agents.agent_b.monitors import (
    detect_anomaly_alerts,
    detect_cost_variance_alerts,
    detect_delay_alerts,
)
from backend.agents.agent_b.thresholds import MonitoringThresholds
from backend.agents.contracts import ProcessingStatus


def test_detect_delay_alerts_over_threshold():
    milestones = [
        {
            "milestone_id": "m1",
            "name": "Foundation",
            "planned_end_date": "2026-04-20",
            "status": "in_progress",
        }
    ]

    alerts = detect_delay_alerts(
        milestones=milestones,
        current_date="2026-04-25",
        delay_threshold_days=3,
    )

    assert len(alerts) == 1
    assert alerts[0]["milestone_id"] == "m1"
    assert alerts[0]["delay_days"] == 5
    assert alerts[0]["severity"] in {"medium", "high", "critical"}


def test_detect_cost_variance_alerts_over_threshold():
    alerts = detect_cost_variance_alerts(
        baseline_budget={"materials": 100000.0},
        actual_costs={"materials": 112000.0},
        cost_variance_threshold=0.08,
    )

    assert len(alerts) == 1
    assert alerts[0]["category"] == "materials"
    assert alerts[0]["variance_percentage"] == 12.0
    assert alerts[0]["severity"] == "medium"


def test_detect_anomaly_alerts_flags_project_inconsistencies():
    alerts = detect_anomaly_alerts(
        project={"contract_value": 100000.0},
        merged_fields={"start_date": "2026-05-01", "end_date": "2026-04-01"},
        milestones=[
            {
                "name": "Finishes",
                "status": "completed",
                "actual_end_date": None,
            }
        ],
        baseline_budget={"materials": 50000.0},
        actual_costs={"materials": 55000.0, "unplanned": 10000.0},
    )

    assert len(alerts) >= 2
    messages = " ".join(alert["impact_description"] for alert in alerts)
    assert "start date" in messages.lower() or "unbudgeted" in messages.lower()


@pytest.mark.asyncio
async def test_agent_b_run_monitoring_persists_results():
    firestore_client = AsyncMock()
    firestore_client.get_project.return_value = {
        "id": "proj_001",
        "name": "Buildora Demo",
        "milestones": [
            {
                "milestone_id": "m1",
                "name": "Foundation",
                "planned_end_date": "2026-04-20",
                "status": "in_progress",
                "budget_allocated": 50000.0,
                "budget_spent": 60000.0,
            },
            {
                "milestone_id": "m2",
                "name": "Structure",
                "planned_end_date": "2026-05-10",
                "status": "completed",
                "budget_allocated": 30000.0,
                "budget_spent": 25000.0,
            },
        ],
        "baseline_budget": {"materials": 100000.0},
        "actual_costs": {"materials": 115000.0},
        "contract_value": 120000.0,
    }
    firestore_client.get_extracted_fields.return_value = []
    firestore_client.create_alert.return_value = "alert_001"
    firestore_client.update_project.return_value = True

    agent_b = AgentB(
        firestore_client=firestore_client,
        thresholds=MonitoringThresholds(delay_days=3, cost_variance_fraction=0.08),
    )

    result = await agent_b.run_monitoring("proj_001", current_date="2026-04-25")

    assert result["project_id"] == "proj_001"
    assert result["status"] in {ProcessingStatus.COMPLETED, ProcessingStatus.PARTIAL}
    assert len(result["delay_alerts"]) == 1
    assert len(result["cost_variance_alerts"]) == 1
    assert len(result["anomaly_alerts"]) >= 1
    assert result["total_alerts"] == len(result["alerts"])
    assert firestore_client.create_alert.await_count == result["total_alerts"]
    firestore_client.update_project.assert_awaited_once()
