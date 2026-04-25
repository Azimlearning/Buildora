"""
Agent B: Project monitoring and alert generation.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import time
from typing import Any, Dict, List, Optional

from backend.agents.contracts import AlertSeverity, ProcessingStatus
from backend.agents.agent_b.monitors import (
    build_flattened_alerts,
    detect_anomaly_alerts,
    detect_cost_variance_alerts,
    detect_delay_alerts,
)
from backend.agents.agent_b.thresholds import (
    MonitoringThresholds,
    load_monitoring_thresholds,
)
from backend.core.firebase_client import FirestoreClient

logger = logging.getLogger(__name__)


class AgentB:
    """Schedule and cost monitoring agent."""

    def __init__(
        self,
        firestore_client: FirestoreClient,
        thresholds: Optional[MonitoringThresholds] = None,
    ):
        self.db = firestore_client
        self.thresholds = thresholds or load_monitoring_thresholds()

    async def run_monitoring(
        self,
        project_id: str,
        current_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run the Agent B monitoring pipeline for a project."""
        started_at = time.time()
        timestamp = current_date or datetime.now(timezone.utc).isoformat()
        errors: List[str] = []

        project = await self.db.get_project(project_id)
        if not project:
            return {
                "project_id": project_id,
                "status": ProcessingStatus.FAILED,
                "monitoring_timestamp": timestamp,
                "delay_alerts": [],
                "cost_variance_alerts": [],
                "anomaly_alerts": [],
                "alerts": [],
                "total_alerts": 0,
                "critical_alerts": 0,
                "requires_immediate_action": False,
                "processing_time_ms": int((time.time() - started_at) * 1000),
                "errors": [f"Project {project_id} not found"],
            }

        extracted_fields = await self.db.get_extracted_fields(project_id)
        merged_fields = self._flatten_extracted_fields(project, extracted_fields)

        milestones = self._resolve_milestones(project, merged_fields)
        baseline_budget = self._resolve_baseline_budget(project, merged_fields, milestones)
        actual_costs = self._resolve_actual_costs(project, merged_fields, milestones)

        delay_alerts = detect_delay_alerts(
            milestones=milestones,
            current_date=timestamp,
            delay_threshold_days=self.thresholds.delay_days,
        )
        cost_alerts = detect_cost_variance_alerts(
            baseline_budget=baseline_budget,
            actual_costs=actual_costs,
            cost_variance_threshold=self.thresholds.cost_variance_fraction,
        )
        anomaly_alerts = detect_anomaly_alerts(
            project=project,
            merged_fields=merged_fields,
            milestones=milestones,
            baseline_budget=baseline_budget,
            actual_costs=actual_costs,
        )
        flattened_alerts = build_flattened_alerts(delay_alerts, cost_alerts, anomaly_alerts)

        for alert in flattened_alerts:
            try:
                await self.db.create_alert(
                    project_id=project_id,
                    alert_data={
                        "source": "agent_b",
                        "type": alert["type"],
                        "severity": alert["severity"],
                        "message": alert["message"],
                        "details": alert["details"],
                    },
                )
            except Exception as exc:
                logger.warning("[Agent B] Failed to persist alert: %s", exc)
                errors.append(f"Failed to persist alert: {exc}")

        all_severities = [alert["severity"] for alert in flattened_alerts]
        critical_alerts = sum(1 for severity in all_severities if severity == AlertSeverity.CRITICAL.value)
        requires_immediate_action = any(
            severity in {AlertSeverity.CRITICAL.value, AlertSeverity.HIGH.value}
            for severity in all_severities
        )

        result = {
            "project_id": project_id,
            "status": ProcessingStatus.COMPLETED if not errors else ProcessingStatus.PARTIAL,
            "monitoring_timestamp": timestamp,
            "delay_alerts": delay_alerts,
            "cost_variance_alerts": cost_alerts,
            "anomaly_alerts": anomaly_alerts,
            "alerts": flattened_alerts,
            "total_alerts": len(flattened_alerts),
            "critical_alerts": critical_alerts,
            "requires_immediate_action": requires_immediate_action,
            "processing_time_ms": int((time.time() - started_at) * 1000),
            "errors": errors,
            "metadata": {
                "milestones_evaluated": len(milestones),
                "baseline_budget_categories": len(baseline_budget),
                "actual_cost_categories": len(actual_costs),
            },
        }

        try:
            await self.db.update_project(
                project_id,
                {
                    "monitoring_results": result,
                    "alerts": flattened_alerts,
                    "last_monitored_at": timestamp,
                },
            )
        except Exception as exc:
            logger.warning("[Agent B] Failed to update project monitoring results: %s", exc)
            result["errors"].append(f"Failed to update project monitoring results: {exc}")
            result["status"] = ProcessingStatus.PARTIAL

        return result

    def _flatten_extracted_fields(
        self,
        project: Dict[str, Any],
        extracted_list: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        merged = dict(project)
        for entry in extracted_list:
            fields = entry.get("fields", {})
            if isinstance(fields, dict):
                for key, value in fields.items():
                    if value is None:
                        continue
                    if key not in merged or merged[key] in (None, "", [], {}):
                        merged[key] = value
        return merged

    def _resolve_milestones(
        self,
        project: Dict[str, Any],
        merged_fields: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        project_milestones = project.get("milestones")
        if isinstance(project_milestones, list) and project_milestones:
            return [self._normalize_milestone(item, index) for index, item in enumerate(project_milestones)]

        extracted_milestones = merged_fields.get("milestones")
        if isinstance(extracted_milestones, list) and extracted_milestones:
            return [self._normalize_milestone(item, index) for index, item in enumerate(extracted_milestones)]

        project_end = merged_fields.get("end_date") or project.get("end_date")
        if project_end:
            return [
                {
                    "milestone_id": "project-delivery",
                    "name": merged_fields.get("project_name") or project.get("name") or "Project delivery",
                    "planned_end_date": project_end,
                    "actual_end_date": project.get("actual_end_date"),
                    "status": project.get("status", "in_progress"),
                    "budget_allocated": self._parse_amount(
                        project.get("contract_value") or merged_fields.get("contract_value")
                    ),
                    "budget_spent": self._parse_amount(project.get("budget_spent")),
                }
            ]

        return []

    def _normalize_milestone(self, item: Any, index: int) -> Dict[str, Any]:
        if isinstance(item, dict):
            return {
                "milestone_id": item.get("milestone_id") or item.get("id") or f"milestone-{index + 1}",
                "name": item.get("name") or item.get("title") or f"Milestone {index + 1}",
                "planned_start_date": item.get("planned_start_date") or item.get("start_date"),
                "planned_end_date": item.get("planned_end_date") or item.get("due_date") or item.get("end_date"),
                "actual_start_date": item.get("actual_start_date"),
                "actual_end_date": item.get("actual_end_date") or item.get("actual_date"),
                "status": item.get("status", "not_started"),
                "budget_allocated": self._parse_amount(
                    item.get("budget_allocated") or item.get("budget") or item.get("planned_cost")
                ),
                "budget_spent": self._parse_amount(
                    item.get("budget_spent") or item.get("actual_cost") or item.get("cost_spent")
                ),
            }

        return {
            "milestone_id": f"milestone-{index + 1}",
            "name": str(item),
            "planned_start_date": None,
            "planned_end_date": None,
            "actual_start_date": None,
            "actual_end_date": None,
            "status": "not_started",
            "budget_allocated": 0.0,
            "budget_spent": 0.0,
        }

    def _resolve_baseline_budget(
        self,
        project: Dict[str, Any],
        merged_fields: Dict[str, Any],
        milestones: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        for candidate in (
            project.get("baseline_budget"),
            project.get("budget_breakdown"),
            merged_fields.get("baseline_budget"),
            merged_fields.get("budget_breakdown"),
        ):
            budget_map = self._budget_map_from_value(candidate)
            if budget_map:
                return budget_map

        milestone_budget = {
            milestone["name"]: self._parse_amount(milestone.get("budget_allocated"))
            for milestone in milestones
            if self._parse_amount(milestone.get("budget_allocated")) > 0
        }
        if milestone_budget:
            return milestone_budget

        contract_value = self._parse_amount(
            project.get("contract_value") or merged_fields.get("contract_value")
        )
        if contract_value > 0:
            return {"overall_project": contract_value}

        return {}

    def _resolve_actual_costs(
        self,
        project: Dict[str, Any],
        merged_fields: Dict[str, Any],
        milestones: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        for candidate in (
            project.get("actual_costs"),
            project.get("cost_tracking"),
            merged_fields.get("actual_costs"),
            merged_fields.get("cost_tracking"),
        ):
            cost_map = self._budget_map_from_value(candidate)
            if cost_map:
                return cost_map

        milestone_costs = {
            milestone["name"]: self._parse_amount(milestone.get("budget_spent"))
            for milestone in milestones
            if self._parse_amount(milestone.get("budget_spent")) > 0
        }
        if milestone_costs:
            return milestone_costs

        total_spent = self._parse_amount(project.get("budget_spent") or merged_fields.get("budget_spent"))
        if total_spent > 0:
            return {"overall_project": total_spent}

        return {}

    def _budget_map_from_value(self, value: Any) -> Dict[str, float]:
        if isinstance(value, dict):
            return {
                str(key): self._parse_amount(amount)
                for key, amount in value.items()
                if self._parse_amount(amount) != 0
            }

        if isinstance(value, list):
            mapped: Dict[str, float] = {}
            for index, item in enumerate(value):
                if not isinstance(item, dict):
                    continue
                category = item.get("category") or item.get("name") or f"item_{index + 1}"
                amount = (
                    item.get("budgeted_amount")
                    or item.get("baseline_cost")
                    or item.get("amount")
                    or item.get("actual_cost")
                )
                parsed_amount = self._parse_amount(amount)
                if parsed_amount != 0:
                    mapped[str(category)] = parsed_amount
            return mapped

        return {}

    def _parse_amount(self, value: Any) -> float:
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
