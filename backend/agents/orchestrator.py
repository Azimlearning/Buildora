"""
LangGraph Orchestrator - Chains all 5 agents in sequence

This is the main orchestration layer that coordinates:
- Agent A: Document Reader (PDF parsing & field extraction)
- Agent B: Monitor (Delay & cost variance detection)
- Agent C: Permits/Compliance (CIDB scoring)
- Agent D: Alerts/Reminders (Telegram notifications)
- Agent E: Report Generator (PDF & XLSX generation)

Author: Chip/Azim
"""

from typing import Annotated
from langgraph.graph import StateGraph, END
import operator
import asyncio
import concurrent.futures
from backend.agents.contracts import BuildoraState
from backend.agents.agent_a.agent import AgentA
from backend.agents.agent_b.agent import AgentB
from backend.agents.agent_c.agent import AgentC
from backend.agents.agent_e.agent import AgentE
from backend.core.glm_client import get_glm_client
from backend.core.firebase_client import get_firestore_client
from backend.core.storage import FirebaseStorageClient


def _run_async(coro):
    """
    Safely run an async coroutine from a sync context, even when called
    inside an already-running event loop (e.g. LangGraph ainvoke nodes).
    Uses a fresh event loop in a background thread to avoid 'loop already running'.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, coro)
        return future.result()


def agent_a_node(state: BuildoraState) -> BuildoraState:
    """
    Agent A: Document Reader
    - Parse PDFs using pdfplumber/PyMuPDF
    - Extract fields via Z.AI GLM
    - Store docs in Firebase Storage
    """
    print(f"[Agent A] Processing {len(state.get('documents', []))} documents...")

    try:
        # Use singleton clients so data is shared across agent nodes
        glm_client = get_glm_client()
        storage_client = FirebaseStorageClient()
        firestore_client = get_firestore_client()

        # Initialize Agent A
        agent_a = AgentA(glm_client, storage_client, firestore_client)

        # Process documents
        result = _run_async(agent_a.process_documents(
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

    try:
        firestore_client = get_firestore_client()
        agent_b = AgentB(firestore_client=firestore_client)

        result = _run_async(agent_b.run_monitoring(
            project_id=state["project_id"]
        ))

        state["monitoring_results"] = result
        state["alerts"] = result.get("alerts", [])
        print(
            f"[Agent B] Generated {result.get('total_alerts', 0)} alert(s) "
            f"with {result.get('critical_alerts', 0)} critical"
        )

    except Exception as e:
        error_msg = f"Agent B error: {str(e)}"
        print(f"[Agent B] {error_msg}")
        state["errors"].append(error_msg)
        state["monitoring_results"] = {
            "project_id": state["project_id"],
            "status": "failed",
            "delay_alerts": [],
            "cost_variance_alerts": [],
            "anomaly_alerts": [],
            "alerts": [],
            "total_alerts": 0,
            "critical_alerts": 0,
            "requires_immediate_action": False,
            "errors": [error_msg],
        }
        state["alerts"] = []

    return state


def agent_d_node(state: BuildoraState) -> BuildoraState:
    """
    Agent D: Alerts/Reminders
    - Generate alerts based on compliance score
    - Send Telegram notifications
    - Track notification status
    """
    print("[Agent D] Generating alerts and notifications...")

    # Placeholder - to be implemented
    # This should check compliance_score and send alerts if score < 80
    state["notifications_sent"] = 0

    return state


def agent_e_node(state: BuildoraState) -> BuildoraState:
    """
    Agent E: Report Generator
    - Generate PDF project report
    - Generate XLSX cost tracker
    - Generate compliance summary
    - Upload reports to Firebase Storage
    """
    print("[Agent E] Generating reports...")

    try:
        # Use singleton clients
        firestore_client = get_firestore_client()
        storage_client = FirebaseStorageClient()

        # Initialize Agent E
        agent_e = AgentE(
            firestore_client=firestore_client,
            storage_client=storage_client
        )

        # Generate reports
        result = _run_async(agent_e.generate_reports(
            project_id=state["project_id"],
            report_types=["pdf", "xlsx"]
        ))

        state["reports"] = result.get("reports", {})

        # Count errors
        errors = result.get("errors", [])
        if errors:
            state["errors"].extend(errors)
            print(f"[Agent E] Generated reports with {len(errors)} errors")
        else:
            print(f"[Agent E] Successfully generated {len(state['reports'])} reports")

    except Exception as e:
        error_msg = f"Agent E error: {str(e)}"
        print(f"[Agent E] {error_msg}")
        state["errors"].append(error_msg)
        state["reports"] = {}

    return state


def agent_c_node(state: BuildoraState) -> BuildoraState:
    """
    Agent C: Permits/Compliance
    - Score against CIDB BISQ checklist
    - Detect compliance gaps
    - Validate contractor licenses
    - Pre-fill ePermit forms
    """
    print("[Agent C] Running compliance check...")

    try:
        # Use singleton clients so Agent C reads data saved by Agent A
        glm_client = get_glm_client()
        firestore_client = get_firestore_client()

        # Initialize Agent C
        agent_c = AgentC(
            glm_client=glm_client,
            firestore_client=firestore_client,
            pass_threshold=80
        )

        # Run compliance check
        result = _run_async(agent_c.run_compliance_check(
            project_id=state["project_id"],
            stage="P2-KM",
            permit_types=["excavation", "road_closure"]
        ))

        state["compliance_score"] = result
        print(f"[Agent C] Compliance score: {result.get('score', 0):.1f}% ({result.get('status', 'unknown')})")

    except Exception as e:
        error_msg = f"Agent C error: {str(e)}"
        print(f"[Agent C] {error_msg}")
        state["errors"].append(error_msg)
        state["compliance_score"] = {
            "score": 0,
            "status": "error",
            "gaps": []
        }

    return state


def create_buildora_graph() -> StateGraph:
    """
    Create the LangGraph workflow

    Flow: Agent A → Agent B → Agent C → Agent D → Agent E
    """
    workflow = StateGraph(BuildoraState)

    # Add nodes
    workflow.add_node("agent_a", agent_a_node)
    workflow.add_node("agent_b", agent_b_node)
    workflow.add_node("agent_c", agent_c_node)
    workflow.add_node("agent_d", agent_d_node)
    workflow.add_node("agent_e", agent_e_node)

    # Define edges - linear flow
    workflow.set_entry_point("agent_a")
    workflow.add_edge("agent_a", "agent_b")
    workflow.add_edge("agent_b", "agent_c")
    workflow.add_edge("agent_c", "agent_d")
    workflow.add_edge("agent_d", "agent_e")
    workflow.add_edge("agent_e", END)

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
        "monitoring_results": {},
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
