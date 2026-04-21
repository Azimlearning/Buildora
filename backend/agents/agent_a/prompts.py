"""
Agent A: GLM Prompts for Field Extraction

Author: Chip/Azim
"""

EXTRACTION_PROMPT = """You are an AI assistant specialized in extracting structured information from Malaysian construction project documents.

Extract the following fields from the provided text. If a field is not found, return null.

Required fields:
1. project_name: Full name of the construction project
2. contractor: Name of the main contractor
3. client: Name of the client/project owner
4. project_value: Total project value in MYR (numeric only)
5. start_date: Project start date (YYYY-MM-DD format)
6. end_date: Expected completion date (YYYY-MM-DD format)
7. location: Project location/address
8. project_type: Type of construction (e.g., residential, commercial, infrastructure)
9. scope: Brief description of project scope
10. milestones: List of key milestones with dates

Additional fields (if available):
11. consultant: Name of project consultant
12. architect: Name of architect
13. engineer: Name of engineer
14. permit_status: Status of permits/approvals
15. cidb_registration: CIDB registration number

Document text:
{document_text}

Return the extracted information as a JSON object with the field names as keys.
"""

MILESTONE_EXTRACTION_PROMPT = """Extract milestone information from the following text.

For each milestone, extract:
- name: Milestone name/description
- planned_date: Planned completion date (YYYY-MM-DD)
- actual_date: Actual completion date if completed (YYYY-MM-DD or null)
- status: Status (planned, in_progress, completed, delayed)
- budget: Allocated budget for this milestone (numeric)
- actual_cost: Actual cost if completed (numeric or null)

Text:
{milestone_text}

Return as a JSON array of milestone objects.
"""

COST_BREAKDOWN_PROMPT = """Extract cost breakdown information from the following text.

Extract:
- category: Cost category (e.g., materials, labor, equipment, subcontractor)
- description: Description of the cost item
- budgeted_amount: Budgeted amount in MYR
- actual_amount: Actual amount spent (if available)
- variance: Difference between budgeted and actual
- percentage: Percentage of total project cost

Text:
{cost_text}

Return as a JSON array of cost items.
"""

RISK_EXTRACTION_PROMPT = """Identify and extract project risks from the following text.

For each risk, extract:
- risk_description: Description of the risk
- category: Risk category (schedule, cost, quality, safety, compliance)
- severity: Severity level (low, medium, high, critical)
- mitigation: Mitigation strategy if mentioned
- status: Current status (identified, mitigated, resolved)

Text:
{risk_text}

Return as a JSON array of risk objects.
"""


def build_extraction_prompt(document_text: str) -> str:
    """
    Build the main field extraction prompt

    Args:
        document_text: Raw text from PDF

    Returns:
        Formatted prompt for GLM
    """
    return EXTRACTION_PROMPT.format(document_text=document_text)


def build_milestone_prompt(milestone_text: str) -> str:
    """
    Build milestone extraction prompt

    Args:
        milestone_text: Text containing milestone information

    Returns:
        Formatted prompt for GLM
    """
    return MILESTONE_EXTRACTION_PROMPT.format(milestone_text=milestone_text)


def build_cost_prompt(cost_text: str) -> str:
    """
    Build cost breakdown extraction prompt

    Args:
        cost_text: Text containing cost information

    Returns:
        Formatted prompt for GLM
    """
    return COST_BREAKDOWN_PROMPT.format(cost_text=cost_text)


def build_risk_prompt(risk_text: str) -> str:
    """
    Build risk extraction prompt

    Args:
        risk_text: Text containing risk information

    Returns:
        Formatted prompt for GLM
    """
    return RISK_EXTRACTION_PROMPT.format(risk_text=risk_text)
