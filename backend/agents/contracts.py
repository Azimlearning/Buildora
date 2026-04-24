"""
Agent Contracts - Explicit Type Definitions
============================================
This module defines explicit input/output contracts for all agents in the
Buildora pipeline. These contracts serve as:

1. **Documentation** - Clear interface specifications
2. **Type Safety** - Static type checking via mypy/pyright
3. **Validation** - Runtime validation boundaries
4. **AI-Friendly** - Explicit contracts for AI-assisted development

All agents MUST adhere to these contracts. Breaking changes require
updating this file and all dependent agents.

Author: Chip/Azim (AI-First Engineering Initiative)
"""

from typing import TypedDict, Literal, Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ═══════════════════════════════════════════════════════════════
# SHARED TYPES
# ═══════════════════════════════════════════════════════════════


class ProcessingStatus(str, Enum):
    """Standard processing status across all agents"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ConfidenceLevel(str, Enum):
    """Confidence levels for AI-extracted data"""
    HIGH = "high"      # ≥90%
    MEDIUM = "medium"  # 70-89%
    LOW = "low"        # 50-69%
    VERY_LOW = "very_low"  # <50%


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"          # Action required within 24h
    MEDIUM = "medium"      # Action required within 1 week
    LOW = "low"            # Informational
    INFO = "info"          # No action required


class ComplianceStatus(str, Enum):
    """Compliance check status"""
    PASS = "pass"          # Score ≥80%
    WARNING = "warning"    # Score 60-79%
    FAIL = "fail"          # Score <60%
    ERROR = "error"        # Check failed to run


# ═══════════════════════════════════════════════════════════════
# AGENT A: DOCUMENT READER
# ═══════════════════════════════════════════════════════════════


class DocumentMetadata(TypedDict):
    """Input document metadata for Agent A"""
    file_path: str
    filename: str
    file_size_bytes: int
    mime_type: str
    uploaded_at: str  # ISO 8601 timestamp


class ExtractedField(TypedDict):
    """Single extracted field with confidence score"""
    field_name: str
    value: str | int | float | bool | None
    confidence: float  # 0.0 to 1.0
    confidence_level: ConfidenceLevel
    extraction_method: Literal["digital_text", "ocr", "glm_inference"]
    page_number: Optional[int]


class AgentAInput(TypedDict):
    """Input contract for Agent A"""
    project_id: str
    documents: List[DocumentMetadata]
    extraction_config: Optional[Dict[str, Any]]  # Optional extraction settings


class AgentAOutput(TypedDict):
    """Output contract for Agent A"""
    project_id: str
    status: ProcessingStatus
    documents_processed: int
    documents_failed: int
    processing_time_ms: int
    extracted_fields: List[Dict[str, Any]]  # List of field sets per document
    storage_urls: List[str]  # Firebase Storage URLs
    errors: List[str]
    metadata: Dict[str, Any]


class DocumentFieldSet(TypedDict):
    """Extracted fields for a single document"""
    document_id: str
    filename: str
    fields: Dict[str, ExtractedField]
    total_fields_extracted: int
    high_confidence_fields: int  # Count of fields with confidence ≥0.9
    ocr_fallback_used: bool
    processing_time_ms: int
    storage_url: str


# ═══════════════════════════════════════════════════════════════
# AGENT B: MONITOR
# ═══════════════════════════════════════════════════════════════


class MilestoneData(TypedDict):
    """Milestone tracking data"""
    milestone_id: str
    name: str
    planned_start_date: str  # ISO 8601
    planned_end_date: str    # ISO 8601
    actual_start_date: Optional[str]
    actual_end_date: Optional[str]
    status: Literal["not_started", "in_progress", "completed", "delayed"]
    budget_allocated: float
    budget_spent: float


class DelayAlert(TypedDict):
    """Delay detection alert"""
    alert_id: str
    milestone_id: str
    milestone_name: str
    delay_days: int  # Positive integer
    planned_date: str
    actual_date: str
    severity: AlertSeverity
    impact_description: str
    recommended_actions: List[str]


class CostVarianceAlert(TypedDict):
    """Cost variance detection alert"""
    alert_id: str
    category: str  # e.g., "materials", "labor", "equipment"
    baseline_cost: float
    actual_cost: float
    variance_amount: float
    variance_percentage: float  # e.g., 12.5 for 12.5%
    severity: AlertSeverity
    impact_description: str
    recommended_actions: List[str]


class AgentBInput(TypedDict):
    """Input contract for Agent B"""
    project_id: str
    extracted_fields: Dict[str, Any]  # From Agent A
    baseline_schedule: List[MilestoneData]
    baseline_budget: Dict[str, float]  # Category -> amount
    current_date: str  # ISO 8601


class AgentBOutput(TypedDict):
    """Output contract for Agent B"""
    project_id: str
    status: ProcessingStatus
    monitoring_timestamp: str  # ISO 8601
    delay_alerts: List[DelayAlert]
    cost_variance_alerts: List[CostVarianceAlert]
    total_alerts: int
    critical_alerts: int
    requires_immediate_action: bool
    processing_time_ms: int
    errors: List[str]


# ═══════════════════════════════════════════════════════════════
# AGENT C: COMPLIANCE CHECKER
# ═══════════════════════════════════════════════════════════════


class ComplianceGap(TypedDict):
    """Single compliance gap"""
    gap_id: str
    description_en: str
    description_ms: Optional[str]
    category: str  # e.g., "document", "license", "permit"
    mandatory: bool
    severity: AlertSeverity
    resolution_steps: List[str]
    estimated_resolution_days: Optional[int]


class ContractorValidation(TypedDict):
    """Contractor license validation result"""
    is_valid: bool
    grade: str
    category: str
    specialization: str
    project_value_limit: float
    current_project_value: float
    issues: List[str]


class PrefilledForm(TypedDict):
    """Pre-filled ePermit form data"""
    permit_type: str
    form_fields: Dict[str, str | int | float]
    completion_percentage: float
    missing_fields: List[str]


class AgentCInput(TypedDict):
    """Input contract for Agent C"""
    project_id: str
    extracted_fields: Dict[str, Any]  # From Agent A
    project_stage: str  # e.g., "P2-KM", "P2-PJ", "P6-CCC"
    permit_types: List[str]  # e.g., ["excavation", "road_closure"]


class AgentCOutput(TypedDict):
    """Output contract for Agent C"""
    project_id: str
    status: ProcessingStatus
    compliance_score: float  # 0-100
    compliance_status: ComplianceStatus
    borang_type: str  # e.g., "A1", "A2", "A3"
    stage: str
    total_requirements: int
    satisfied_requirements: int
    gaps: List[ComplianceGap]
    contractor_validation: ContractorValidation
    prefilled_forms: Dict[str, PrefilledForm]
    risk_level: Literal["low", "medium", "high", "critical"]
    processing_time_ms: int
    errors: List[str]


# ═══════════════════════════════════════════════════════════════
# AGENT D: TELEGRAM NOTIFICATIONS (PLACEHOLDER)
# ═══════════════════════════════════════════════════════════════


class TelegramMessage(TypedDict):
    """Telegram notification message"""
    message_id: str
    chat_id: str
    message_text: str
    sent_at: str  # ISO 8601
    delivery_status: Literal["sent", "failed", "pending"]


class AgentDInput(TypedDict):
    """Input contract for Agent D (Telegram)"""
    project_id: str
    alerts: List[DelayAlert | CostVarianceAlert]
    compliance_gaps: List[ComplianceGap]
    notification_type: Literal["alert", "summary", "reminder"]


class AgentDOutput(TypedDict):
    """Output contract for Agent D (Telegram)"""
    project_id: str
    status: ProcessingStatus
    messages_sent: int
    messages_failed: int
    telegram_messages: List[TelegramMessage]
    errors: List[str]


# ═══════════════════════════════════════════════════════════════
# AGENT E: REPORT GENERATION
# ═══════════════════════════════════════════════════════════════


class ReportMetadata(TypedDict):
    """Generated report metadata"""
    report_type: Literal["pdf", "xlsx", "compliance", "timeline"]
    filename: str
    file_size_bytes: int
    storage_url: str
    mime_type: str
    generated_at: str  # ISO 8601
    generation_time_ms: int


class PDFReportSections(TypedDict):
    """PDF report content sections"""
    executive_summary: bool
    project_overview: bool
    extracted_fields: bool
    compliance_analysis: bool
    alerts_and_risks: bool
    cost_analysis: bool
    timeline_gantt: bool
    recommendations: bool


class XLSXReportSheets(TypedDict):
    """XLSX report sheet configuration"""
    cost_breakdown: bool
    variance_analysis: bool
    milestone_tracking: bool
    compliance_checklist: bool
    document_register: bool


class AgentEInput(TypedDict):
    """Input contract for Agent E"""
    project_id: str
    report_types: List[Literal["pdf", "xlsx", "compliance", "timeline"]]
    pdf_sections: Optional[PDFReportSections]
    xlsx_sheets: Optional[XLSXReportSheets]
    branding_config: Optional[Dict[str, Any]]


class AgentEOutput(TypedDict):
    """Output contract for Agent E"""
    project_id: str
    status: ProcessingStatus
    generated_at: str  # ISO 8601
    reports: Dict[str, ReportMetadata]  # report_type -> metadata
    total_reports_generated: int
    total_file_size_bytes: int
    processing_time_ms: int
    errors: List[str]


# ═══════════════════════════════════════════════════════════════
# ORCHESTRATOR STATE
# ═══════════════════════════════════════════════════════════════


class BuildoraState(TypedDict):
    """
    Shared state across all agents in the LangGraph pipeline.

    This is the single source of truth for the entire workflow.
    Each agent reads from and writes to this state.
    """
    # Core identifiers
    project_id: str
    pipeline_run_id: str
    started_at: str  # ISO 8601

    # Input data
    documents: List[DocumentMetadata]

    # Agent A output
    extracted_fields: Optional[AgentAOutput]

    # Agent B output
    monitoring_results: Optional[AgentBOutput]

    # Agent C output
    compliance_results: Optional[AgentCOutput]

    # Agent D output (Telegram)
    notification_results: Optional[AgentDOutput]

    # Agent E output (Reports)
    report_results: Optional[AgentEOutput]

    # Pipeline metadata
    current_agent: Optional[str]
    completed_agents: List[str]
    failed_agents: List[str]
    total_processing_time_ms: int

    # Error tracking
    errors: List[str]
    warnings: List[str]

    # Status
    pipeline_status: Literal["running", "completed", "failed", "partial"]


# ═══════════════════════════════════════════════════════════════
# VALIDATION HELPERS
# ═══════════════════════════════════════════════════════════════


def validate_confidence_score(score: float) -> None:
    """
    Validate confidence score is in valid range.

    Raises:
        ValueError: If score is not between 0.0 and 1.0
    """
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"Confidence score must be between 0.0 and 1.0, got {score}")


def validate_percentage(value: float, field_name: str = "value") -> None:
    """
    Validate percentage is in valid range.

    Raises:
        ValueError: If percentage is not between 0.0 and 100.0
    """
    if not 0.0 <= value <= 100.0:
        raise ValueError(f"{field_name} must be between 0.0 and 100.0, got {value}")


def validate_iso8601_timestamp(timestamp: str) -> None:
    """
    Validate ISO 8601 timestamp format.

    Raises:
        ValueError: If timestamp is not valid ISO 8601
    """
    try:
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid ISO 8601 timestamp: {timestamp}") from e


def get_confidence_level(score: float) -> ConfidenceLevel:
    """
    Convert numeric confidence score to confidence level enum.

    Args:
        score: Confidence score between 0.0 and 1.0

    Returns:
        ConfidenceLevel enum value
    """
    validate_confidence_score(score)

    if score >= 0.9:
        return ConfidenceLevel.HIGH
    elif score >= 0.7:
        return ConfidenceLevel.MEDIUM
    elif score >= 0.5:
        return ConfidenceLevel.LOW
    else:
        return ConfidenceLevel.VERY_LOW


def get_alert_severity_from_variance(variance_pct: float) -> AlertSeverity:
    """
    Determine alert severity based on cost variance percentage.

    Args:
        variance_pct: Cost variance as percentage (e.g., 12.5 for 12.5%)

    Returns:
        AlertSeverity enum value
    """
    abs_variance = abs(variance_pct)

    if abs_variance >= 20:
        return AlertSeverity.CRITICAL
    elif abs_variance >= 15:
        return AlertSeverity.HIGH
    elif abs_variance >= 8:
        return AlertSeverity.MEDIUM
    else:
        return AlertSeverity.LOW


def get_alert_severity_from_delay(delay_days: int) -> AlertSeverity:
    """
    Determine alert severity based on delay duration.

    Args:
        delay_days: Number of days delayed

    Returns:
        AlertSeverity enum value
    """
    if delay_days >= 14:
        return AlertSeverity.CRITICAL
    elif delay_days >= 7:
        return AlertSeverity.HIGH
    elif delay_days >= 3:
        return AlertSeverity.MEDIUM
    else:
        return AlertSeverity.LOW


# ═══════════════════════════════════════════════════════════════
# CONTRACT VERSIONING
# ═══════════════════════════════════════════════════════════════


CONTRACT_VERSION = "1.0.0"
CONTRACT_LAST_UPDATED = "2026-04-23"

__all__ = [
    # Enums
    "ProcessingStatus",
    "ConfidenceLevel",
    "AlertSeverity",
    "ComplianceStatus",

    # Agent A
    "DocumentMetadata",
    "ExtractedField",
    "AgentAInput",
    "AgentAOutput",
    "DocumentFieldSet",

    # Agent B
    "MilestoneData",
    "DelayAlert",
    "CostVarianceAlert",
    "AgentBInput",
    "AgentBOutput",

    # Agent C
    "ComplianceGap",
    "ContractorValidation",
    "PrefilledForm",
    "AgentCInput",
    "AgentCOutput",

    # Agent D
    "TelegramMessage",
    "AgentDInput",
    "AgentDOutput",

    # Agent E
    "ReportMetadata",
    "PDFReportSections",
    "XLSXReportSheets",
    "AgentEInput",
    "AgentEOutput",

    # Orchestrator
    "BuildoraState",

    # Validation helpers
    "validate_confidence_score",
    "validate_percentage",
    "validate_iso8601_timestamp",
    "get_confidence_level",
    "get_alert_severity_from_variance",
    "get_alert_severity_from_delay",

    # Metadata
    "CONTRACT_VERSION",
    "CONTRACT_LAST_UPDATED",
]