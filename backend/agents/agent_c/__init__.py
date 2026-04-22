"""
Agent C: Permits & Compliance Checker
======================================
Compares project documents against CIDB/DBKL checklists, validates
contractor licences, calculates compliance scores, and pre-fills
ePermit form fields.

Exports:
    AgentC           — Main agent class (used by orchestrator)
    ComplianceEngine — Deterministic scoring engine (used by agent + tests)
    ComplianceResult — Dataclass for compliance check output
"""

from backend.agents.agent_c.agent import AgentC
from backend.agents.agent_c.compliance import ComplianceEngine, ComplianceResult

__all__ = ["AgentC", "ComplianceEngine", "ComplianceResult"]
