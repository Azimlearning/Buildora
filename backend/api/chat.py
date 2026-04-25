from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, Response
from backend.core.firebase_client import get_firestore_client  # type: ignore
from pydantic import BaseModel
import os
import json
from openai import AsyncOpenAI

router = APIRouter()

class ChatRequest(BaseModel):
    project_id: str
    message: str
    selected_sources: list[str] = []
    history: list[dict] = []

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    db = get_firestore_client()
    project = await db.get_project(req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Load knowledge base for CIBD context
    try:
        with open("knowledge_base.json", "r") as f:
            kb = json.load(f)
            kb_text = json.dumps(kb, indent=2)
    except:
        kb_text = "CIBD knowledge base unavailable."

    # Load API key from environment only (never hardcode secrets)
    api_key = os.getenv("OPENAI_API_KEY")
    
    client = AsyncOpenAI(api_key=api_key)

    system_prompt = f"""You are Buildora's AI assistant for construction project management.
You answer questions about the current project and CIDB compliance.

PROJECT DETAILS:
Name: {project.get('name', 'Unknown')}
Contractor: {project.get('contractor', 'Unknown')}
Status: {project.get('status', 'Unknown')}
Health Score: {project.get('health_score', 'N/A')}
CIDB Grade: {project.get('cidb_grade', 'N/A')}

SELECTED SOURCES TO REFERENCE:
{', '.join(req.selected_sources) if req.selected_sources else 'None selected'}

CIDB KNOWLEDGE BASE:
{kb_text[:2000]} # Truncated for context limits

Be concise, professional, and helpful. If asked about a source not selected, remind the user to select it.
"""

    messages = [{"role": "system", "content": system_prompt}]
    
    # Add history
    for msg in req.history[-5:]: # Keep last 5 messages for context
        if msg.get("role") in ["user", "assistant"]:
            messages.append({"role": msg["role"], "content": msg.get("content", "")})
            
    # Add current message
    messages.append({"role": "user", "content": req.message})

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        return {"reply": reply}
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return {"reply": f"I encountered an error connecting to the AI service: {str(e)}"}
