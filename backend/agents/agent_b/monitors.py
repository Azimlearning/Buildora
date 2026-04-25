"""
Pure monitoring logic for Agent B.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from backend.agents.contracts import (
    AlertSeverity,
    get_alert_severity_from_delay,
    get_alert_severity_from_variance,
)


def parse_monitoring_date(value: Any) -> date:
    """Parse flexible date inputs used across project and milestone payloads."""
    parsed = _parse_date(value)
    if parsed is not None:
        return parsed
    return datetime.now(timezone.utc).date()


def detect_delay_alerts(
    milestones: Iterable[Dict[str, Any]],
    current_date: Any,
    delay_threshold_days: int,
) -> List[Dict[str, Any]]:
    """Detect milestones delayed beyond the configured threshold."""
    today = parse_monitoring_date(current_date)
    alerts: List[Dict[str, Any]] = []

    for index, milestone in enumerate(milestones):
        planned_end = _parse_date(
            milestone.get("planned_end_date")
            or milestone.get("due_date")
            or milestone.get("target_date")
            or milestone.get("end_date")
        )
        if planned_end is None:
            continue

        actual_end = _parse_date(
            milestone.get("actual_end_date")
            or milestone.get("completed_at")
            or milestone.get("actual_date")
        )
        status = str(milestone.get("status", "")).lower()

        if actual_end is not None and actual_end > planned_end:
            delay_days = (actual_end - planned_end).days
            actual_date = actual_end.isoformat()
        elif status not in {"completed", "done"} and today > planned_end:
            delay_days = (today - planned_end).days
            actual_date = today.isoformat()
        else:
            continue

        if delay_days < delay_threshold_days:
            continue

        milestone_name = (
            milestone.get("name")
            or milestone.get("title")
            or milestone.get("milestone_name")
            or f"Milestone {index + 1}"
        )
        severity = get_alert_severity_from_delay(delay_days)

        alerts.append(
            {
                "alert_id": f"delay-{uuid4()}",
                "milestone_id": str(
                    milestone.get("milestone_id")
                    or milestone.get("id")
                    or f"milestone-{index + 1}"
                ),
                "milestone_name": str(milestone_name),
                "delay_days": delay_days,
                "planned_date": planned_end.isoformat(),
                "actual_date": actual_date,
                "severity": severity.value,
                "impact_description": (
                    f"Milestone '{milestone_name}' is delayed by {delay_days} day(s) "
                    f"against the planned schedule."
                ),
                "recommended_actions": _delay_actions(delay_days),
            }
        )

    return alerts


def detect_cost_variance_alerts(
    baseline_budget: Dict[str, float],
    actual_costs: Dict[str, float],
    cost_variance_threshold: float,
) -> List[Dict[str, Any]]:
    """Detect categories where actual spend deviates from baseline budget."""
    alerts: List[Dict[str, Any]] = []

    for category, baseline_raw in baseline_budget.items():
        baseline_cost = _coerce_float(baseline_raw)
        actual_cost = _coerce_float(actual_costs.get(category, 0.0))

        if baseline_cost <= 0:
            continue

        variance_amount = actual_cost - baseline_cost
        variance_fraction = variance_amount / baseline_cost

        if abs(variance_fraction) < cost_variance_threshold:
            continue

        variance_percentage = round(variance_fraction * 100, 2)
        severity = get_alert_severity_from_variance(variance_percentage)

        alerts.append(
            {
                "alert_id": f"cost-{uuid4()}",
                "category": str(category),
                "baseline_cost": round(baseline_cost, 2),
                "actual_cost": round(actual_cost, 2),
                "variance_amount": round(variance_amount, 2),
                "variance_percentage": variance_percentage,
                "severity": severity.value,
                "impact_description": (
                    f"Cost category '{category}' is at {variance_percentage:.2f}% variance "
                    f"against the approved baseline."
                ),
                "recommended_actions": _cost_actions(variance_percentage),
            }
        )

    return alerts


def detect_anomaly_alerts(
    project: Dict[str, Any],
    merged_fields: Dict[str, Any],
    milestones: Iterable[Dict[str, Any]],
    baseline_budget: Dict[str, float],
    actual_costs: Dict[str, float],
) -> List[Dict[str, Any]]:
    """Detect monitoring anomalies not covered by core threshold checks."""
    alerts: List[Dict[str, Any]] = []

    start_date = _parse_date(
        merged_fields.get("start_date") or project.get("start_date")
    )
    end_date = _parse_date(
        merged_fields.get("end_date") or project.get("end_date")
    )
    if start_date and end_date and start_date > end_date:
        alerts.append(
            _anomaly_alert(
                anomaly_type="date_inconsistency",
                severity=AlertSeverity.HIGH,
                message="Project start date is later than the project end date.",
                actions=[
                    "Validate extracted project dates against the source document.",
                    "Correct the schedule baseline before downstream reporting.",
                ],
            )
        )

    for category in actual_costs:
        if category not in baseline_budget:
            alerts.append(
                _anomaly_alert(
                    anomaly_type="unbudgeted_cost",
                    severity=AlertSeverity.MEDIUM,
                    message=f"Actual spend exists for unbudgeted category '{category}'.",
                    actions=[
                        "Confirm whether this category should be added to the approved budget.",
                        "Review invoices and recode spending if the category was misclassified.",
                    ],
                )
            )

    contract_value = _coerce_float(
        project.get("contract_value") or merged_fields.get("contract_value")
    )
    total_actual_cost = round(sum(_coerce_float(value) for value in actual_costs.values()), 2)
    if contract_value > 0 and total_actual_cost > contract_value:
        alerts.append(
            _anomaly_alert(
                anomaly_type="project_overspend",
                severity=AlertSeverity.CRITICAL,
                message=(
                    f"Recorded project spend ({total_actual_cost:.2f}) exceeds the contract "
                    f"value ({contract_value:.2f})."
                ),
                actions=[
                    "Escalate the overspend to the project manager for immediate review.",
                    "Verify the cost ledger and contract ceiling against source records.",
                ],
            )
        )

    for milestone in milestones:
        status = str(milestone.get("status", "")).lower()
        actual_end = _parse_date(
            milestone.get("actual_end_date")
            or milestone.get("completed_at")
            or milestone.get("actual_date")
        )
        if status in {"completed", "done"} and actual_end is None:
            milestone_name = milestone.get("name") or milestone.get("title") or "Unknown milestone"
            alerts.append(
                _anomaly_alert(
                    anomaly_type="missing_actual_completion_date",
                    severity=AlertSeverity.MEDIUM,
                    message=(
                        f"Milestone '{milestone_name}' is marked completed without an actual "
                        f"completion date."
                    ),
                    actions=[
                        "Update the milestone record with the actual completion date.",
                        "Confirm the status is correct before final reporting.",
                    ],
                )
            )

    return alerts


def build_flattened_alerts(
    delay_alerts: Iterable[Dict[str, Any]],
    cost_alerts: Iterable[Dict[str, Any]],
    anomaly_alerts: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Build a simple alert list for API and report consumers."""
    flattened: List[Dict[str, Any]] = []

    for alert in delay_alerts:
        flattened.append(
            {
                "id": alert["alert_id"],
                "type": "delay",
                "severity": alert["severity"],
                "message": alert["impact_description"],
                "details": alert,
            }
        )

    for alert in cost_alerts:
        flattened.append(
            {
                "id": alert["alert_id"],
                "type": "cost_variance",
                "severity": alert["severity"],
                "message": alert["impact_description"],
                "details": alert,
            }
        )

    for alert in anomaly_alerts:
        flattened.append(
            {
                "id": alert["alert_id"],
                "type": "anomaly",
                "severity": alert["severity"],
                "message": alert["impact_description"],
                "details": alert,
            }
        )

    return flattened


def _anomaly_alert(
    anomaly_type: str,
    severity: AlertSeverity,
    message: str,
    actions: List[str],
) -> Dict[str, Any]:
    return {
        "alert_id": f"anomaly-{uuid4()}",
        "anomaly_type": anomaly_type,
        "severity": severity.value,
        "impact_description": message,
        "recommended_actions": actions,
    }


def _delay_actions(delay_days: int) -> List[str]:
    actions = [
        "Review the blocked task and confirm the root cause with the site team.",
        "Rebaseline dependent milestones if the delay cannot be recovered this week.",
    ]
    if delay_days >= 7:
        actions.append("Escalate the schedule slippage to the project manager immediately.")
    return actions


def _cost_actions(variance_percentage: float) -> List[str]:
    actions = [
        "Review the latest invoices and site claims for this category.",
        "Confirm the baseline budget is still current and approved.",
    ]
    if variance_percentage > 0:
        actions.append("Prepare a mitigation plan to reduce further overspend.")
    else:
        actions.append("Check whether the underspend reflects delayed procurement or scope changes.")
    return actions


def _parse_date(value: Any) -> Optional[date]:
    if value in (None, ""):
        return None

    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None

        normalized = candidate.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized).date()
        except ValueError:
            pass

        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(candidate, fmt).date()
            except ValueError:
                continue

    return None


def _coerce_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(",", "").replace("RM", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    return 0.0
