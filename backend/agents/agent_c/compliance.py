"""
Agent C: Compliance Engine — Knowledge Base & Scoring
=====================================================
This module contains the digitised DBKL / CIDB regulatory knowledge that
Agent C uses to:
  1. Determine which documents are mandatory for a given project type & stage.
  2. Score the project's current document set against the checklist.
  3. Validate contractor licences against the CIDB G1-G7 grading system.
  4. Map project data onto ePermit form field schemas for pre-filling.

All checklist data was extracted from the "Kuala Lumpur Digital Planning
Permission Submission Form" NotebookLM notebook (108 DBKL/CIDB sources).

Author: Aliasya (Agent C logic)
Data:   Harry   (CIDB knowledge base)
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# ─────────────────────────────────────────────────────────────
# 1. BORANG TYPE MAP
#    Maps development zoning/purpose → correct application form.
#    Agent A extracts project_type; we look it up here.
# ─────────────────────────────────────────────────────────────

class BorangType(str, Enum):
    A1 = "A1"   # Cantuman & Pecah Sempadan (subdivision / layout)
    A2 = "A2"   # Perdagangan / Perdagangan Bercampur (commercial)
    A3 = "A3"   # Kediaman (residential)
    A4 = "A4"   # Perindustrian (industrial)
    A5 = "A5"   # Kemudahan Pelajaran (educational)
    A6 = "A6"   # Institusi Awam & Kemudahan Masyarakat (public)
    A7 = "A7"   # Stesen Minyak / Pusat Servis / Bengkel (petrol)
    A8 = "A8"   # Am — general planning permission
    A10 = "A10" # Penukaran Kegunaan Tanah (land-use change)

BORANG_TYPE_MAP: Dict[str, BorangType] = {
    "subdivision":   BorangType.A1,
    "layout":        BorangType.A1,
    "commercial":    BorangType.A2,
    "mixed":         BorangType.A2,
    "residential":   BorangType.A3,
    "industrial":    BorangType.A4,
    "education":     BorangType.A5,
    "public":        BorangType.A6,
    "community":     BorangType.A6,
    "petrol":        BorangType.A7,
    "workshop":      BorangType.A7,
    "general":       BorangType.A8,
    "land_use_change": BorangType.A10,
}

# ─────────────────────────────────────────────────────────────
# 2. DBKL MASTER CHECKLIST — Kebenaran Merancang (KM)
#    Source: GARISPANDUAN PENYERAHAN DOKUMEN PERMOHONAN
#            KEBENARAN MERANCANG SECARA DIGITAL JPRB V2.pdf
#    Each item is (id, description_en, description_ms, mandatory)
# ─────────────────────────────────────────────────────────────

@dataclass
class ChecklistItem:
    id: str
    description_en: str
    description_ms: str
    mandatory: bool = True
    conditional_note: str = ""

DBKL_MASTER_CHECKLIST: List[ChecklistItem] = [
    # --- A. Mandatory Forms & Declarations ---
    ChecklistItem("KM-01", "Cover Letter", "Surat Iringan", True),
    ChecklistItem("KM-02", "Land Title Copy", "Sesalinan Hakmilik Tanah", True,
                  "Company-owned land requires Form 49/Form 24"),
    ChecklistItem("KM-03", "Sales & Purchase Agreement", "Perjanjian Jual Beli", False,
                  "If applicable as proof of ownership"),
    ChecklistItem("KM-04", "Private Land Search (e-Tanah)", "Carian Persendirian Hakmilik Tanah", True),
    ChecklistItem("KM-05", "Assessment Tax Receipt (latest)", "Resit Cukai Taksiran Terbaharu", True),
    ChecklistItem("KM-06", "Processing Fee Declaration", "Borang Akuan Pembayaran Fee Memproses", True),
    ChecklistItem("KM-07", "Official Works Declaration", "Borang Akuan Kerja Rasmi Binaan/Kerja Tanah", True),
    ChecklistItem("KM-08", "Development Charge Estimate", "Borang Anggaran Penilaian Caj Pembangunan", True),
    ChecklistItem("KM-09", "Low Carbon Building Checklist (.xlsx)", "Borang Semak Bangunan Rendah Karbon KL", True),
    # --- B. Visuals, Plans & Surveys ---
    ChecklistItem("KM-10", "Site Photographs (2 copies)", "Gambar Tapak (2 salinan)", True),
    ChecklistItem("KM-11", "Perspective Drawing (1 copy)", "Lukisan Perspektif (1 salinan)", True),
    ChecklistItem("KM-12", "Survey / Contour Plans (2 sets)", "Pelan Ukur/Kontur (2 set)", True),
    ChecklistItem("KM-13", "Earthwork Cross-Section Plans (2 sets)", "Pelan Keratan Kerja-Kerja Tanah", True),
    ChecklistItem("KM-14", "Existing Tree Plan (2 copies)", "Pelan Pokok Sedia Ada", True),
    # --- C. Technical Reports & Impact Assessments ---
    ChecklistItem("KM-15", "Traffic Impact Assessment (TIA)", "Laporan TIA", True),
    ChecklistItem("KM-16", "Geotechnical / Soil Investigation Report", "Laporan Geoteknikal/Siasatan Tanah", True,
                  "Geotechnical for Cat 1-3; Soil Investigation for Cat 4"),
    ChecklistItem("KM-17", "Feasibility Study Report", "Laporan Kajian Pasaran", True),
    ChecklistItem("KM-18", "Environmental Impact Assessment (EIA)", "Laporan EIA", False,
                  "Required if DOE thresholds met"),
    ChecklistItem("KM-19", "Social Impact Assessment (SIA)", "Laporan SIA", False,
                  "Required if SIA Committee mandates"),
    # --- D. Conditional Clearances ---
    ChecklistItem("KM-20", "TNB Clearance Letter", "Surat Perakuan TNB", False,
                  "If development involves TNB substations"),
    ChecklistItem("KM-21", "JKR Clearance Letter", "Surat Perakuan JKR", False,
                  "If access affects traffic flow"),
    ChecklistItem("KM-22", "PTG WPKL Approval", "Surat Kelulusan PTG WPKL", False,
                  "If land-use contradicts express conditions"),
]

# ─────────────────────────────────────────────────────────────
# 3. CIDB CONTRACTOR GRADING (G1–G7)
#    Source: Keperluan-dan-Prosedur-Pendaftaran.pdf &
#            1.-Definisi-_-Skop-Pendaftaran.pdf
# ─────────────────────────────────────────────────────────────

CIDB_GRADING: Dict[str, float] = {
    "G1": 200_000,
    "G2": 500_000,
    "G3": 1_000_000,
    "G4": 3_000_000,
    "G5": 5_000_000,
    "G6": 10_000_000,
    "G7": float("inf"),  # No limit
}

CIDB_CATEGORIES = {
    "CE": {"name": "Civil Engineering", "codes": "CE01-CE43"},
    "B":  {"name": "Building Construction", "codes": "B01-B29"},
    "ME": {"name": "Mechanical & Electrical", "codes": "M01-M23, E01-E35"},
    "F":  {"name": "Facilities", "codes": "F01-F02"},
}

# ─────────────────────────────────────────────────────────────
# 4. STAGE CHECKLISTS (P2 → P6)
# ─────────────────────────────────────────────────────────────

class ProjectStage(str, Enum):
    P2_KM = "P2-KM"    # Planning Permission
    P2_PB = "P2-PB"    # Building Plans
    P2_PJ = "P2-PJ"    # Engineering / Earthworks
    P2_PL = "P2-PL"    # Landscape
    P3_MK = "P3-MK"    # Notice to Commence Work
    P4_JPIF = "P4-JPIF" # Interim Inspection
    P5_JPIF = "P5-JPIF" # Final Inspection
    P6_CCC = "P6-CCC"  # CCC Deposit
    P6_CFO = "P6-CFO"  # Certificate of Fitness

# P2-PJ-01: Earthworks engineering plan requirements
EARTHWORKS_CHECKLIST: List[str] = [
    "Surat Iringan (Cover Letter)",
    "Laporan Teknikal (Technical Report)",
    "Borang JPIF 1 & JPIF 3 (completed)",
    "Borang JPIF 7(i) — Earthworks fee calculation",
    "Soil Investigation (S.I) Report",
    "Earthworks Specifications",
    "Piling Specifications (if applicable)",
    "ESCP with sediment trap calculations",
    "Retaining Wall calculations (if applicable)",
    "Geotechnical Report (Cat 1&2: Accredited Checker; Cat 3: Certified Engineer)",
    "Site photographs (A3, 4 views per angle)",
    "Development Order + D.O approved plan",
    "ESCP approval from JPS WPKL (large-scale)",
    "EIA approval from JAS (if in D.O conditions)",
    "3 sets earthwork plans (Key, Location, Layout, ESCP, Cross-section, Method Statement)",
    "1 set Engineering Survey Plans (Licensed Surveyor)",
    "Softcopies of all documents and plans",
]

# P6-CCC: Certificate of Completion and Compliance — Borang G1–G21
CCC_BORANG_G: Dict[str, str] = {
    "G1":  "Kerja-Kerja Tanah (Earthworks) — requires Pelan Kerja Tanah approval",
    "G2":  "Pemancangan Tanda (Setting Out) — requires KMB letter",
    "G3":  "Asas Tapak (Foundation) — requires KMB letter",
    "G4":  "Struktur (Structure) — requires RC Plan",
    "G5":  "Perpaipan Air Dalaman (Internal Water) — requires water plan approval",
    "G6":  "Perpaipan Sanitari Dalaman (Sanitary) — requires sanitary plan",
    "G7":  "Elektrikal Dalaman (Internal Electrical)",
    "G8":  "Menentang Kebakaran Pasif (Passive Fire) — requires JBPM clearance",
    "G9":  "Menentang Kebakaran Aktif (Active Fire) — requires JBPM clearance",
    "G10": "Pengudaraan Mekanikal (Mechanical Ventilation)",
    "G11": "Lif/Eskalator (Lift/Escalator) — requires JKKP certificate",
    "G12": "Bangunan (Building) — requires KMB letter",
    "G13": "Bekalan Air Luaran (External Water) — requires Air Selangor cert",
    "G14": "Retikulasi Pembentungan (Sewerage) — requires IWK cert",
    "G15": "Logi Rawatan Pembentungan (STP) — requires IWK cert",
    "G16": "Bekalan Elektrik Luaran (External Power) — requires TNB cert",
    "G17": "Jalan dan Parit (Roads & Drains) — requires JPIF/DBKL cert",
    "G18": "Lampu Jalan (Street Lighting) — requires JKME DBKL approval",
    "G19": "Parit Luaran Utama (Main External Drain) — requires plan approval",
    "G20": "Telekomunikasi (Telecommunications) — requires telco plan approval",
    "G21": "Pandangan Darat (Landscape) — requires landscape plan approval",
}

# ─────────────────────────────────────────────────────────────
# 5. ePERMIT FIELD SCHEMAS
#    Source: Excavation_Permit.pdf, Road_Closure_Permit.pdf,
#            Material Transport Route Permit.pdf
# ─────────────────────────────────────────────────────────────

EPERMIT_FIELDS: Dict[str, List[str]] = {
    "excavation": [
        "jenis_kerja",        # Type of Work
        "tajuk_kerja",        # Work Title
        "nama_projek",        # Project Name
        "nama_pemohon",       # Applicant Name
        "emel_pemohon",       # Applicant Email
        "nama_syarikat",      # Company Name
        "no_pendaftaran",     # Registration Number
        "no_telefon_bimbit",  # Mobile Phone
        "no_telefon_pejabat", # Office Phone
        "alamat",             # Address
        "poskod",             # Postcode
        "negeri",             # State
    ],
    "road_closure": [
        "jenis_kerja",        # Type of Work
        "kategori_projek",    # Project Category
        "kategori_permit",    # Permit Category
        "tempoh_kerja",       # Work Duration
        "aktiviti",           # Activity
        "no_rujukan_jkaws",   # JKAWS Reference (auto from excavation)
        "nama_pemohon",
        "emel_pemohon",
        "nama_syarikat",
        "no_pendaftaran",
        "nama_projek",
        "tajuk_kerja",
        "tarikh_mula",        # Start Date
        "tarikh_tamat",       # End Date
        "masa_mula",          # Start Time
        "masa_tamat",         # End Time
        "nama_jalan",         # Road Name
        "parlimen",           # Parliament area
        "jenis_jalan",        # Road Type
        "firma_perunding",    # Consulting Firm
        "kontraktor",         # Contractor
    ],
    "material_transport": [
        "jenis_kerja",        # Lorry type: with/without D.O, Concrete Mixer
        "nama_projek",
        "tajuk_kerja",
        "tarikh_mula_permit", # Requested permit start date
        "lokasi_bahan_diambil",  # Material pickup location
        "lokasi_bahan_diletak",  # Material drop-off location
        "no_kenderaan",       # Vehicle Number (checked for compound fines)
        "maklumat_kontraktor_pengangkutan",  # Transport contractor info
    ],
}

# ─────────────────────────────────────────────────────────────
# 6. COMPLIANCE RESULT DATACLASS
# ─────────────────────────────────────────────────────────────

@dataclass
class ComplianceResult:
    """Output of a compliance check — consumed by orchestrator & Agent B/E."""
    score: float                             # 0–100 percentage
    status: str                              # "pass" | "fail" | "warning"
    total_items: int = 0
    satisfied_items: int = 0
    gaps: List[Dict[str, Any]] = field(default_factory=list)
    contractor_valid: bool = True
    contractor_issues: List[str] = field(default_factory=list)
    prefilled_forms: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    borang_type: str = ""
    stage: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 1),
            "status": self.status,
            "total_items": self.total_items,
            "satisfied_items": self.satisfied_items,
            "gaps": self.gaps,
            "contractor_valid": self.contractor_valid,
            "contractor_issues": self.contractor_issues,
            "prefilled_forms": self.prefilled_forms,
            "borang_type": self.borang_type,
            "stage": self.stage,
        }


# ─────────────────────────────────────────────────────────────
# 7. COMPLIANCE ENGINE
# ─────────────────────────────────────────────────────────────

class ComplianceEngine:
    """
    Deterministic scoring engine.

    It does NOT call GLM — that is Agent C's job.  This class handles
    the rule-based comparison of project documents against checklists.
    """

    def __init__(self, pass_threshold: int = 80):
        self.pass_threshold = pass_threshold

    # ── public API ───────────────────────────────────────────

    def resolve_borang_type(self, project_type: str) -> BorangType:
        """Map a project_type string to the correct Borang form."""
        key = project_type.lower().strip()
        return BORANG_TYPE_MAP.get(key, BorangType.A8)

    def score_documents(
        self,
        submitted_docs: List[str],
        stage: str = "P2-KM",
    ) -> ComplianceResult:
        """
        Compare submitted document names against the master checklist.

        Args:
            submitted_docs: list of document description strings
                            (from Agent A extracted_fields).
            stage: project stage (P2-KM, P2-PJ, P6-CCC, etc.)

        Returns:
            ComplianceResult with score, gaps, and status.
        """
        checklist = self._get_checklist_for_stage(stage)
        total = len(checklist)
        if total == 0:
            return ComplianceResult(score=100, status="pass")

        gaps = []
        satisfied = 0
        docs_lower = [d.lower() for d in submitted_docs]

        for item in checklist:
            # Fuzzy keyword match against submitted docs
            matched = self._fuzzy_match(item, docs_lower)
            if matched:
                satisfied += 1
            else:
                if isinstance(item, ChecklistItem):
                    gaps.append({
                        "id": item.id,
                        "description_en": item.description_en,
                        "description_ms": item.description_ms,
                        "mandatory": item.mandatory,
                        "note": item.conditional_note,
                    })
                else:
                    gaps.append({
                        "id": "",
                        "description_en": item,
                        "mandatory": True,
                    })

        score = (satisfied / total) * 100 if total else 100
        status = "pass" if score >= self.pass_threshold else "fail"
        if score >= 60 and status == "fail":
            status = "warning"

        return ComplianceResult(
            score=score,
            status=status,
            total_items=total,
            satisfied_items=satisfied,
            gaps=gaps,
            stage=stage,
        )

    def validate_contractor_license(
        self,
        grade: str,
        category: str,
        specialization: str,
        project_value: float,
        project_category: str = "",
    ) -> tuple[bool, List[str]]:
        """
        Validate contractor licence against CIDB rules.

        Args:
            grade:           e.g. "G5"
            category:        e.g. "CE", "B", "ME"
            specialization:  e.g. "CE01", "B01"
            project_value:   total project value in MYR
            project_category: broad project category string

        Returns:
            (is_valid, list_of_issues)
        """
        issues: List[str] = []

        # Check grade exists
        grade_upper = grade.upper().strip()
        if grade_upper not in CIDB_GRADING:
            issues.append(f"Unknown CIDB grade: {grade}")
            return False, issues

        # Check financial capacity
        max_value = CIDB_GRADING[grade_upper]
        if project_value > max_value:
            issues.append(
                f"Grade {grade_upper} max tendering capacity is "
                f"RM {max_value:,.0f} but project value is "
                f"RM {project_value:,.0f}"
            )

        # Check category exists
        cat_upper = category.upper().strip()
        if cat_upper not in CIDB_CATEGORIES:
            issues.append(f"Unknown CIDB category: {category}")

        is_valid = len(issues) == 0
        return is_valid, issues

    def get_stage_requirements(self, stage: str) -> List[str]:
        """Return human-readable requirement list for a given stage."""
        if stage == "P2-PJ":
            return EARTHWORKS_CHECKLIST
        if stage == "P6-CCC":
            return [f"Borang {k}: {v}" for k, v in CCC_BORANG_G.items()]
        return [item.description_en for item in DBKL_MASTER_CHECKLIST]

    def prefill_epermit_fields(
        self,
        permit_type: str,
        project_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Map structured project data onto ePermit field schema.

        Args:
            permit_type: "excavation" | "road_closure" | "material_transport"
            project_data: extracted fields dict from Agent A / Firestore

        Returns:
            Dict of {field_name: value_or_None}
        """
        schema = EPERMIT_FIELDS.get(permit_type, [])
        if not schema:
            return {}

        # Map from Agent A field names → ePermit field names
        field_mapping = {
            "nama_projek":    project_data.get("project_name", ""),
            "tajuk_kerja":    project_data.get("scope", ""),
            "nama_pemohon":   project_data.get("client", ""),
            "nama_syarikat":  project_data.get("contractor", ""),
            "kontraktor":     project_data.get("contractor", ""),
            "tarikh_mula":    project_data.get("start_date", ""),
            "tarikh_tamat":   project_data.get("end_date", ""),
            "alamat":         project_data.get("location", ""),
            "no_pendaftaran": project_data.get("cidb_registration", ""),
        }

        result = {}
        for field_name in schema:
            result[field_name] = field_mapping.get(field_name, None)
        return result

    # ── private helpers ──────────────────────────────────────

    def _get_checklist_for_stage(self, stage: str):
        """Return the correct checklist for a project stage."""
        if stage == "P2-PJ":
            return EARTHWORKS_CHECKLIST
        if stage == "P6-CCC":
            return list(CCC_BORANG_G.values())
        # Default: master KM checklist
        return DBKL_MASTER_CHECKLIST

    # Keyword groups for filename-based matching
    # Maps checklist item IDs to filename keywords that strongly imply that document.
    _FILENAME_SIGNALS: Dict[str, List[str]] = {
        "KM-01": ["cover", "letter", "surat", "iringan"],
        "KM-02": ["title", "hakmilik", "tanah", "land"],
        "KM-04": ["carian", "search", "etanah"],
        "KM-05": ["cukai", "assessment", "tax", "receipt"],
        "KM-09": ["carbon", "green", "rendah", "karbon"],
        "KM-10": ["photo", "gambar", "tapak", "photograph"],
        "KM-11": ["perspective", "perspektif", "lukisan"],
        "KM-12": ["survey", "ukur", "contour", "kontur", "topograph"],
        "KM-15": ["traffic", "tia", "transport"],
        "KM-16": ["geotech", "geotechnic", "soil", "tanah", "investigation", "siasatan"],
        "KM-17": ["feasibility", "kajian", "pasaran", "study"],
        "KM-18": ["eia", "environment", "impact", "alam"],
    }

    # Common document-type keywords → which checklist IDs they satisfy
    _KEYWORD_MAP: Dict[str, List[str]] = {
        "permit": ["KM-01", "KM-06", "KM-07"],
        "permits": ["KM-01", "KM-06", "KM-07"],
        "profile": ["KM-02", "KM-04"],
        "profiles": ["KM-02", "KM-04"],
        "financial": ["KM-05", "KM-08", "KM-17"],
        "finance": ["KM-05", "KM-08"],
        "incident": ["KM-15", "KM-17"],
        "incidents": ["KM-15", "KM-17"],
        "contract": ["KM-01", "KM-03"],
        "boq": ["KM-08", "KM-09"],
        "plan": ["KM-11", "KM-12"],
        "report": ["KM-15", "KM-16", "KM-17"],
        "certificate": ["KM-02", "KM-04"],
        "checklist": ["KM-09"],
        "drawing": ["KM-11", "KM-13"],
        "site": ["KM-10", "KM-12"],
    }

    def _infer_satisfied_ids_from_filenames(self, filenames: List[str]) -> set:
        """Return a set of checklist IDs implied by uploaded filenames."""
        satisfied_ids: set = set()
        for fname in filenames:
            # Use the stem (without extension), split on _ and -
            stem = fname.lower().replace(".pdf", "").replace(".docx", "")
            parts = [p for part in stem.split("_") for p in part.split("-") if len(p) > 2]
            for part in parts:
                if part in self._KEYWORD_MAP:
                    satisfied_ids.update(self._KEYWORD_MAP[part])
                # Also partial match
                for kw, ids in self._KEYWORD_MAP.items():
                    if kw in part or part in kw:
                        satisfied_ids.update(ids)
        return satisfied_ids

    def _fuzzy_match(self, item, docs_lower: List[str]) -> bool:
        """Keyword match — checks if key words appear in any doc string."""
        if isinstance(item, ChecklistItem):
            keywords_en = item.description_en.lower().split()
            keywords_ms = item.description_ms.lower().split()
            # Need at least 1 keyword hit in any single doc (was 2, relaxed for filenames)
            for doc in docs_lower:
                en_hits = sum(1 for kw in keywords_en if len(kw) > 3 and kw in doc)
                ms_hits = sum(1 for kw in keywords_ms if len(kw) > 3 and kw in doc)
                if en_hits >= 1 or ms_hits >= 1:
                    return True
        else:
            # Plain string checklist item
            keywords = [kw for kw in item.lower().split() if len(kw) > 3]
            for doc in docs_lower:
                hits = sum(1 for kw in keywords if kw in doc)
                if hits >= 1:
                    return True
        return False
