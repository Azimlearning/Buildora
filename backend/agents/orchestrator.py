"""
LangGraph Orchestrator - Chains all 5 agents in sequence

This is the main orchestration layer that coordinates:
- Agent A: Document Reader (PDF parsing & field extraction)
- Agent B: Monitor (Delay & cost variance detection)
- Agent C: Permits/Compliance (CIDB scoring)
- Agent D: Reports (PDF & XLSX generation)
- Agent E: Alerts/Reminders (Telegram notifications)

Author: Chip/Azim
"""

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator
from backend.agents.agent_a.agent import AgentA
from backend.core.glm_client import GLMClient
from backend.core.firebase_client import FirebaseClient
from backend.core.storage import FirebaseStorage


class BuildoraState(TypedDict):
    """Shared state across all agents"""
    project_id: str
    documents: list[dict]  # Uploaded files
    extracted_fields: dict  # Agent A output
    alerts: list[dict]  # Agent B output
    compliance_score: dict  # Agent C output
    reports: dict  # Agent D output
    notifications_sent: int  # Agent E output
    errors: Annotated[list[str], operator.add]  # Accumulated errors


def agent_a_node(state: BuildoraState) -> BuildoraState:
    """
    Agent A: Document Reader
    - Parse PDFs using pdfplumber/PyMuPDF
    - Extract fields via Z.AI GLM
    - Store docs in Firebase Storage
    """
    import asyncio

    print(f"[Agent A] Processing {len(state.get('documents', []))} documents...")

    try:
        # Initialize clients
        glm_client = GLMClient()
        storage_client = FirebaseStorage()
        firestore_client = FirebaseClient()

        # Initialize Agent A
        agent_a = AgentA(glm_client, storage_client, firestore_client)

        # Process documents
        result = asyncio.run(agent_a.process_documents(
            project_id=state["project_id"],
            documents=state["documents"]
        ))

        state["extracted_fields"] = result
        print(f"[Agent A] Successfully processed {result['documents_processed']} documents")

    except Exception as e:
        error_msg = f"Agent A error: {str(e)}"
        print(f"[Agent A] {error_msg}")
        state["errors"].append(error_msg)
        state["extracted_fields"] = {}

    return state


def agent_b_node(state: BuildoraState) -> BuildoraState:
    """
    Agent B: Monitor
    - Check delay > 3 days
    - Check cost variance > 8%
    - Detect anomalies in project data
    """
    print("[Agent B] Checking for delays and cost variances...")

    # Placeholder - to be implemented by Harry
    state["alerts"] = []

    return state


def agent_e_node(state: BuildoraState) -> BuildoraState:
    """
    Agent E: Alerts/Reminders
    - Send Telegram notifications for critical alerts
    - Schedule reminders for upcoming milestones
    """
    print("[Agent E] Processing alerts and sending notifications...")

    # Placeholder - to be implemented
    # This agent handles Telegram bot integration
    state["notifications_sent"] = len(state.get("alerts", []))

    return state


def should_run_agent_c(state: BuildoraState) -> str:
    """
    Conditional edge: Only run Agent C if compliance check is needed
    """
    # TODO: Add logic to determine if compliance check is needed
    # For now, always run it
    return "agent_c"


def agent_c_node(state: BuildoraState) -> BuildoraState:
    """
    Agent C: Permits/Compliance
    - Score against CIDB BISQ checklist
    - Detect compliance gaps
    """
    # TODO: Implement Agent C logic
    print("[Agent C] Running compliance check...")

    # Placeholder
    state["compliance_score"] = {
        "score": 85,
        "status": "pass",
        "gaps": []
    }

    return state


def agent_d_node(state: BuildoraState) -> BuildoraState:
    """
    Agent D: Reports
    - Generate branded PDF report
    - Generate XLSX cost tracker
    """
    # TODO: Implement Agent D logic
    print("[Agent D] Generating reports...")

    # Placeholder
    state["reports"] = {
        "pdf_url": "/reports/sample.pdf",
        "xlsx_url": "/reports/sample.xlsx"
    }

    return state


def create_buildora_graph() -> StateGraph:
    """
    Create the LangGraph workflow

    Flow: Agent A → Agent B → Agent E → Agent C (conditional) → Agent D
    """
    workflow = StateGraph(BuildoraState)

    # Add nodes
    workflow.add_node("agent_a", agent_a_node)
    workflow.add_node("agent_b", agent_b_node)
    workflow.add_node("agent_c", agent_c_node)
    workflow.add_node("agent_d", agent_d_node)
    workflow.add_node("agent_e", agent_e_node)

    # Define edges
    workflow.set_entry_point("agent_a")
    workflow.add_edge("agent_a", "agent_b")
    workflow.add_edge("agent_b", "agent_e")

    # Conditional edge for Agent C
    workflow.add_conditional_edges(
        "agent_e",
        should_run_agent_c,
        {
            "agent_c": "agent_c",
            "skip": "agent_d"
        }
    )

    workflow.add_edge("agent_c", "agent_d")
    workflow.add_edge("agent_d", END)

    return workflow.compile()


async def run_pipeline(project_id: str, documents: list[dict]) -> dict:
    """
    Main entry point to run the full pipeline

    Args:
        project_id: Unique project identifier
        documents: List of uploaded document metadata

    Returns:
        Final state with all agent outputs
    """
    graph = create_buildora_graph()

    initial_state: BuildoraState = {
        "project_id": project_id,
        "documents": documents,
        "extracted_fields": {},
        "alerts": [],
        "compliance_score": {},
        "reports": {},
        "notifications_sent": 0,
        "errors": []
    }

    # Run the graph
    final_state = await graph.ainvoke(initial_state)

    return final_state


if __name__ == "__main__":
    # Test the orchestrator
    import asyncio

    test_docs = [
        {"filename": "project_plan.pdf", "size": 1024000}
    ]

    result = asyncio.run(run_pipeline("test-project-001", test_docs))
    print("\n=== Pipeline Result ===")
    print(f"Extracted Fields: {result['extracted_fields']}")
    print(f"Alerts: {result['alerts']}")
    print(f"Compliance: {result['compliance_score']}")
    print(f"Reports: {result['reports']}")
