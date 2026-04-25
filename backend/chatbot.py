import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from backend.core.firebase_client import get_firestore_client
from backend.core.glm_client import get_glm_client

logger = logging.getLogger(__name__)

class ComplianceChatbot:
    """
    Standalone Compliance Chatbot that answers user inquiries based on 
    project documents and CIDB domain knowledge.
    """
    
    def __init__(self, kb_path: str = "knowledge_base.json"):
        self.firestore = get_firestore_client()
        self.glm = get_glm_client()
        
        # Load Domain Knowledge
        try:
            with open(kb_path, "r") as f:
                self.kb_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
            self.kb_data = {}

    async def _fetch_project_data(self, project_id: str) -> Dict[str, Any]:
        """Fetch all relevant project data from Firestore"""
        project = await self.firestore.get_project(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found.")

        documents = await self.firestore.get_documents(project_id)
        extracted_fields = await self.firestore.get_extracted_fields(project_id)
        alerts = await self.firestore.get_alerts(project_id, status="active")

        return {
            "project": project,
            "documents": documents,
            "extracted_fields": extracted_fields,
            "alerts": alerts
        }

    def _format_currency(self, amount: Any) -> str:
        """Format number as RM with thousand separators"""
        try:
            return f"{float(amount):,.2f}"
        except (ValueError, TypeError):
            return str(amount)

    def _format_context_summary(self, raw_data: Dict[str, Any]) -> str:
        """
        Format the raw Firestore data into a clean context summary 
        according to the strict required format.
        """
        proj = raw_data.get("project", {})
        docs = raw_data.get("documents", [])
        alerts = raw_data.get("alerts", [])
        fields = raw_data.get("extracted_fields", [])

        # Documents on file
        doc_names = [d.get("filename", d.get("name", "Unknown Document")) for d in docs if d]
        docs_str = "\n".join(f"- {name}" for name in doc_names) if doc_names else "- None"

        # Compliance Status
        comp_status = proj.get("compliance_status", "Unknown")
        comp_score_map = proj.get("compliance_score", {})
        score_breakdown = ", ".join(f"{k}: {v}" for k, v in comp_score_map.items()) if comp_score_map else "Not available"

        # Active Alerts
        if alerts:
            alerts_str = "\n".join(
                f"- [{a.get('severity', 'INFO').upper()}] {a.get('message', a.get('description', ''))}" 
                for a in alerts
            )
        else:
            alerts_str = "- None"

        # Extracted Field Notes
        fields_str_list = []
        for ef in fields:
            field_data = ef.get("fields", {})
            for k, v in field_data.items():
                if v is not None and v != "":
                    fields_str_list.append(f"- {k}: {v}")
        
        fields_str = "\n".join(fields_str_list) if fields_str_list else "- None"

        # Handle numbers and missing fields gracefully
        contract_value = proj.get("contract_value")
        
        summary_lines = ["PROJECT SUMMARY"]
        if proj.get('name'): summary_lines.append(f"- Name: {proj['name']}")
        if proj.get('contractor_name'): summary_lines.append(f"- Contractor: {proj['contractor_name']}")
        if proj.get('client_name'): summary_lines.append(f"- Client: {proj['client_name']}")
        if proj.get('location'): summary_lines.append(f"- Location: {proj['location']}")
        if proj.get('cidb_grade'): summary_lines.append(f"- CIDB Grade: {proj['cidb_grade']}")
        if contract_value is not None: summary_lines.append(f"- Contract Value: RM {self._format_currency(contract_value)}")
        if proj.get('project_type'): summary_lines.append(f"- Project Type: {proj['project_type']}")
        if proj.get('status'): summary_lines.append(f"- Status: {proj['status']}")

        proj_summary_str = "\n".join(summary_lines)

        summary = f"""{proj_summary_str}

DOCUMENTS CURRENTLY ON FILE
{docs_str}

COMPLIANCE STATUS
- Overall: {comp_status}
- Score breakdown: {score_breakdown}

ACTIVE ALERTS
{alerts_str}

EXTRACTED FIELD NOTES
{fields_str}"""
        return summary

    def _build_system_prompt(self, context_summary: str) -> str:
        """Build the complete system prompt with knowledge base and project context."""
        
        kb_str = json.dumps(self.kb_data, indent=2)
        
        return f"""You are a standalone compliance chatbot for a Malaysian construction project management system (Buildora).

You have been given two sources of data:

SOURCE 1 — DOMAIN KNOWLEDGE (static regulatory rules):
{kb_str}

SOURCE 2 — PROJECT DATA (live from this specific project):
{context_summary}

Your capabilities:
1. Answer questions about this project's current status, documents, and compliance.
2. Identify what documents are missing based on the project's CIDB grade and project type.
3. Suggest the next steps the contractor should take.
4. Explain what any document is, who issues it, and how to obtain it in Malaysia.
5. Warn about compliance risks based on the current data.

Rules you must follow:
- Use ONLY the data provided above. Never invent values, dates, or document names.
- If a piece of information is missing from both sources, say exactly: "This information is not available in the current project records."
- You are READ-ONLY. Never say you can update, submit, or trigger any process.
- Keep answers professional, clear, and practical.
- When suggesting next steps, prioritise by urgency (missing mandatory docs > expiring docs > optional improvements).
- All regulatory references must be specific to Malaysian law (CIDB Act 520, UBBL, local authority requirements).
- If the user's question is unrelated to construction or this project, politely redirect: "I can only assist with questions related to this construction project and compliance requirements."

When answering, identify the user's intent and respond accordingly:

INTENT: "What documents do I still need?"
→ Compare documents_found against knowledge_base/cidb_rules for the project's grade.
→ List missing documents clearly, grouped as: Critical (legally required) and Recommended.
→ For each missing document, state: what it is, who issues it, and approximate time to obtain.

INTENT: "What should I do next?"
→ Look at compliance_status and any active alerts first.
→ Suggest up to 3 prioritised action items.
→ Format as: Action → Why it matters → Who to contact.

INTENT: "Is my project compliant?"
→ State the overall compliance_status clearly.
→ Break down which areas pass and which fail using compliance_score.
→ End with a one-line summary of the most urgent issue.

INTENT: General questions about a document or regulation
→ Use knowledge_base/document_definitions and compliance_rules.
→ Give a plain-English explanation relevant to Malaysian construction context.
→ Always end with: "For official confirmation, refer to [relevant authority]."
"""

    async def answer_question(self, project_id: str, question: str) -> str:
        """
        Process a user question for a specific project.
        """
        try:
            # 1. Fetch raw data
            raw_data = await self._fetch_project_data(project_id)
            
            # 2. Format into clean context summary
            context_summary = self._format_context_summary(raw_data)
            
            # 3. Build system prompt
            system_prompt = self._build_system_prompt(context_summary)
            
            # 4. Construct final LLM prompt (System + User question)
            full_prompt = f"{system_prompt}\n\nUSER QUESTION: {question}\n\nANSWER:"
            
            # 5. Call LLM
            response = await self.glm.chat_completion(
                prompt=full_prompt,
                temperature=0.3,
                max_tokens=1500
            )
            
            if response.get("_fallback"):
                return "The AI service is currently unavailable. Please check the API configuration."
                
            content = response["choices"][0]["message"]["content"]
            return content.strip()
            
        except ValueError as e:
            return str(e)
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return "An error occurred while processing your inquiry."


