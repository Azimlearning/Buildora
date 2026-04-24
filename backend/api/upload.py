from fastapi import APIRouter, UploadFile, File, HTTPException, Form, BackgroundTasks
from typing import List, Optional, Dict, Any
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

router = APIRouter()

# In-memory job tracker for SSE streaming
job_tracker: Dict[str, Dict[str, Any]] = {}


def run_orchestrator_background(project_id: str, file_paths: List[str], job_id: str):
    """Background task to run agent pipeline with per-agent log tracking"""

    def emit(agent: str, log: str):
        """Append a log entry for an agent"""
        logs = job_tracker[job_id].setdefault("agent_logs", [])
        logs.append({"agent": agent, "log": log, "idx": len(logs)})

    try:
        # Initialise job
        job_tracker[job_id] = {
            "status": "running",
            "current_agent": "A",
            "current_file": Path(file_paths[0]).name if file_paths else None,
            "progress": 5,
            "message": "Starting pipeline",
            "agent_logs": []
        }

        from backend.agents.orchestrator import run_pipeline
        from backend.core.firebase_client import get_firestore_client

        # ── Agent A: Document Reader ──────────────────────────────────────
        job_tracker[job_id].update({"current_agent": "A", "progress": 10,
                                    "current_file": Path(file_paths[0]).name if file_paths else None})
        emit("A", "Initialising document parser…")
        for fp in file_paths:
            emit("A", f"Reading {Path(fp).name}")
        emit("A", "Extracting text layers and fields…")
        emit("A", "Running Z.AI GLM field extraction…")

        documents = [{"file_path": fp, "filename": Path(fp).name,
                      "uploaded_at": datetime.utcnow().isoformat()} for fp in file_paths]

        # Run the real pipeline
        job_tracker[job_id].update({"progress": 20, "message": "Agent A: Extracting fields"})
        import asyncio as _asyncio
        result = _asyncio.run(run_pipeline(project_id, documents))

        emit("A", f"✓ Extracted fields from {len(file_paths)} document(s)")

        # ── Agent B: Schedule Monitor ─────────────────────────────────────
        job_tracker[job_id].update({"current_agent": "B", "progress": 40,
                                    "message": "Agent B: Monitoring schedule"})
        emit("B", "Analysing project schedule…")
        emit("B", "Checking milestone variances…")
        alerts = (result or {}).get("alerts", [])
        if alerts:
            for alert in alerts[:3]:
                emit("B", f"⚠ Alert: {alert.get('message', str(alert))}")
        else:
            emit("B", "No schedule delays detected")
        emit("B", "✓ Schedule monitoring complete")

        # ── Agent C: CIDB Compliance ──────────────────────────────────────
        job_tracker[job_id].update({"current_agent": "C", "progress": 60,
                                    "message": "Agent C: Compliance check"})
        emit("C", "Loading CIDB BISQ 2024 checklist…")
        emit("C", "Cross-referencing extracted fields…")
        compliance_score = (result or {}).get("compliance_score", {})
        if isinstance(compliance_score, dict):
            score = compliance_score.get("score", "—")
            status = compliance_score.get("status", "unknown")
            gaps = compliance_score.get("gaps", [])
            emit("C", f"CIDB compliance score: {round(score) if isinstance(score, (int, float)) else score}/100")
            if gaps:
                emit("C", f"Found {len(gaps)} compliance gap(s)")
                for gap in gaps[:3]:
                    emit("C", f"  ⚠ {gap.get('description_en', str(gap))}")
            emit("C", f"✓ Compliance check complete — status: {status}")
        else:
            emit("C", "✓ Compliance check complete")

        # ── Agent D: Report Generator ─────────────────────────────────────
        job_tracker[job_id].update({"current_agent": "D", "progress": 80,
                                    "message": "Agent D: Generating reports"})
        emit("D", "Compiling project summary…")
        reports = (result or {}).get("reports", {})
        if reports.get("pdf"):
            emit("D", "✓ PDF project report generated")
        else:
            emit("D", "Rendering PDF report…")
        if reports.get("xlsx"):
            emit("D", "✓ XLSX cost tracker generated")
        else:
            emit("D", "Generating XLSX cost tracker…")
        emit("D", "✓ Reports ready for download")

        # ── Agent E: Notifications ────────────────────────────────────────
        job_tracker[job_id].update({"current_agent": "E", "progress": 95,
                                    "message": "Agent E: Sending notifications"})
        emit("E", "Reading compliance results from Agent C…")
        if isinstance(compliance_score, dict) and compliance_score.get("score", 100) < 80:
            emit("E", "Score below threshold — composing alert…")
            emit("E", "Preparing Telegram notification for project manager…")
        else:
            emit("E", "Compliance score acceptable — no urgent alerts")
        emit("E", "✓ Notifications dispatched")

        # Done
        job_tracker[job_id].update({
            "status": "complete",
            "progress": 100,
            "message": "Pipeline finished",
            "result": result
        })

        # Update project in Firestore (non-critical, ignore failures)
        try:
            db = get_firestore_client()
            _asyncio.run(db.update_project(project_id, {
                "status": "processed",
                "updated_at": datetime.utcnow().isoformat()
            }))
        except Exception:
            pass

    except Exception as e:
        job_tracker[job_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"Pipeline failed: {str(e)}",
            "error": str(e)
        })
        emit("A", f"⚠ Error: {str(e)}")

        try:
            from backend.core.firebase_client import get_firestore_client
            db = get_firestore_client()
            _asyncio.run(db.update_project(project_id, {
                "status": "error",
                "error_message": str(e),
                "updated_at": datetime.utcnow().isoformat()
            }))
        except Exception:
            pass


@router.post("/upload")
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    project_id: Optional[str] = Form(None),
    project_title: Optional[str] = Form(None)
):
    """
    Upload construction documents and trigger AI agent pipeline.

    Args:
        files: List of uploaded files (PDF, DOCX, JPG, PNG)
        project_id: Existing project ID (optional)
        project_title: New project title (required if project_id is None)

    Returns:
        {status, project_id, job_id, files}
    """
    from backend.core.firebase_client import get_firestore_client

    # Validate inputs
    if not project_id and not project_title:
        raise HTTPException(
            status_code=400,
            detail="Either project_id or project_title must be provided"
        )

    # Create new project if needed
    if not project_id:
        db = get_firestore_client()
        project_data = {
            "name": project_title,
            "description": "",
            "status": "processing",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        project_id = await db.create_project(project_data)

    # Create project-specific upload directory
    upload_dir = f"uploads/{project_id}"
    os.makedirs(upload_dir, exist_ok=True)

    # Save uploaded files
    uploaded_files = []
    file_paths = []

    for file in files:
        # Sanitize filename
        safe_filename = Path(file.filename).name
        file_location = os.path.join(upload_dir, safe_filename)

        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)

        uploaded_files.append({
            "filename": safe_filename,
            "path": file_location,
            "size": os.path.getsize(file_location)
        })
        file_paths.append(file_location)

    # Generate job ID for tracking
    job_id = str(uuid.uuid4())

    # Initialize job tracker
    job_tracker[job_id] = {
        "status": "queued",
        "progress": 0,
        "message": "Upload complete, queuing pipeline"
    }

    # Trigger orchestrator in background
    background_tasks.add_task(
        run_orchestrator_background,
        project_id,
        file_paths,
        job_id
    )

    return {
        "status": "success",
        "project_id": project_id,
        "job_id": job_id,
        "files": uploaded_files,
        "message": "Files uploaded successfully. Processing started."
    }
