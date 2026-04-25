"""
Buildora Backend - FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Buildora API",
    description="AI-powered construction project management system",
    version="0.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Buildora API",
        "version": "0.1.0"
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "api": "up",
            "database": "pending",
            "redis": "pending",
            "minio": "pending"
        }
    }

try:
    from backend.api import upload, projects, milestones, reports, compliance, notifications
except ModuleNotFoundError:
    # When running from backend directory, use relative imports
    from api import upload, projects, milestones, reports, compliance, notifications

from fastapi.responses import StreamingResponse
import asyncio

app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(milestones.router, prefix="/api", tags=["milestones"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
app.include_router(compliance.router, prefix="/api", tags=["compliance"])
app.include_router(notifications.router, prefix="/api", tags=["notifications"])

@app.get("/api/agent-stream/{jobId}")
async def agent_stream(jobId: str):
    """SSE stream for agent updates — emits AgentPanel-compatible per-agent events.

    Strategy:
    - If the job is ALREADY complete (pipeline ran before frontend connected),
      immediately replay all buffered logs then emit done events and close.
    - If the job is STILL running, stream live updates at 0.5s polling cadence.
    """
    import json

    # Map backend agent letters to frontend agent IDs (all 5 agents)
    AGENT_MAP = {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"}

    async def event_generator():
        try:
            from backend.api.upload import job_tracker
        except ModuleNotFoundError:
            from api.upload import job_tracker

        # Wait up to 5s for the job to appear
        for _ in range(10):
            if jobId in job_tracker:
                break
            yield f"data: {json.dumps({'event': 'waiting', 'message': 'Waiting for job'})}\n\n"
            await asyncio.sleep(0.5)

        if jobId not in job_tracker:
            yield f"data: {json.dumps({'event': 'error', 'message': 'Job not found'})}\n\n"
            return

        # ── Snapshot replay for already-complete jobs ──────────────────────
        job = job_tracker[jobId]
        all_logs = job.get("agent_logs", [])
        status = job.get("status", "queued")

        if status in ("complete", "failed"):
            # Replay all buffered logs grouped by agent
            agents_seen = set()
            for log_entry in all_logs:
                agent_letter = log_entry.get("agent", "A")
                agent_id = AGENT_MAP.get(agent_letter, "a")
                log_text = log_entry.get("log", "")

                if agent_id not in agents_seen:
                    agents_seen.add(agent_id)
                    yield f"data: {json.dumps({'agent_id': agent_id, 'event': 'start'})}\n\n"
                    await asyncio.sleep(0)

                yield f"data: {json.dumps({'agent_id': agent_id, 'event': 'log', 'log': log_text})}\n\n"
                await asyncio.sleep(0)

            # Mark all seen agents as done
            for agent_id in agents_seen:
                yield f"data: {json.dumps({'agent_id': agent_id, 'event': 'done'})}\n\n"

            result = job.get("result", {})
            if status == "failed":
                err = job.get("error", "Pipeline failed")
                yield f"data: {json.dumps({'event': 'pipeline_error', 'message': err})}\n\n"
            else:
                yield f"data: {json.dumps({'event': 'pipeline_complete', 'result': result})}\n\n"
            return

        # ── Live streaming for in-progress jobs ────────────────────────────
        sent_start: set = set()
        sent_done: set = set()
        sent_logs: dict = {}  # agent_id -> count of logs already sent
        max_iterations = 360  # 3 minutes max
        iteration = 0

        while iteration < max_iterations:
            job = job_tracker[jobId]
            current_agent_letter = job.get("current_agent", "A")
            agent_id = AGENT_MAP.get(current_agent_letter, "a")
            status = job.get("status", "queued")
            logs = job.get("agent_logs", [])

            # Emit start event for newly started agent
            if status == "running" and agent_id not in sent_start:
                sent_start.add(agent_id)
                sent_logs[agent_id] = 0
                file_hint = job.get("current_file", None)
                yield f"data: {json.dumps({'agent_id': agent_id, 'event': 'start', 'file': file_hint})}\n\n"

            # Emit any new log lines
            for log_entry in logs:
                log_agent = AGENT_MAP.get(log_entry.get("agent", "A"), "a")
                log_text = log_entry.get("log", "")
                log_idx = log_entry.get("idx", 0)
                already_sent = sent_logs.get(log_agent, 0)
                if log_idx >= already_sent:
                    if log_agent not in sent_start:
                        sent_start.add(log_agent)
                        yield f"data: {json.dumps({'agent_id': log_agent, 'event': 'start'})}\n\n"
                    yield f"data: {json.dumps({'agent_id': log_agent, 'event': 'log', 'log': log_text})}\n\n"
                    sent_logs[log_agent] = log_idx + 1

            # Emit done / error
            if status == "complete":
                for aid in list(sent_start):
                    if aid not in sent_done:
                        sent_done.add(aid)
                        yield f"data: {json.dumps({'agent_id': aid, 'event': 'done'})}\n\n"
                result = job.get("result", {})
                yield f"data: {json.dumps({'event': 'pipeline_complete', 'result': result})}\n\n"
                break

            if status == "failed":
                if agent_id not in sent_done:
                    sent_done.add(agent_id)
                    error_msg = job.get("error", "Pipeline failed")
                    yield f"data: {json.dumps({'agent_id': agent_id, 'event': 'error', 'log': error_msg})}\n\n"
                break

            await asyncio.sleep(0.5)
            iteration += 1

        if iteration >= max_iterations:
            yield f"data: {json.dumps({'event': 'timeout', 'message': 'Stream timed out'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


