"""
Threshold helpers for Agent B monitoring rules.
"""

from dataclasses import dataclass

from backend.core.config import get_settings


@dataclass(frozen=True)
class MonitoringThresholds:
    """Central threshold configuration for schedule and cost monitoring."""

    delay_days: int
    cost_variance_fraction: float

    @property
    def cost_variance_percentage(self) -> float:
        return self.cost_variance_fraction * 100


def load_monitoring_thresholds() -> MonitoringThresholds:
    """Load Agent B thresholds from shared settings."""
    settings = get_settings()
    return MonitoringThresholds(
        delay_days=settings.DELAY_THRESHOLD_DAYS,
        cost_variance_fraction=settings.COST_VARIANCE_THRESHOLD,
    )
