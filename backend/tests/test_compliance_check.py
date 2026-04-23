from backend.agents.agent_c.compliance import ComplianceEngine

def test_perfect_compliance_score():
    """Test a fully compliant project."""
    engine = ComplianceEngine()
    
    # Fake extracted document list (perfect submission)
    submitted_docs = [
        "Surat Iringan Permohonan",
        "Hakmilik Tanah (Geran)",
        "Carian Persendirian e-Tanah",
        "Resit Cukai Taksiran Semasa",
        "Borang Akuan Pembayaran Fee Memproses",
        "Borang Akuan Kerja Rasmi Binaan",
        "Borang Anggaran Penilaian Caj Pembangunan",
        "Borang Semak Bangunan Rendah Karbon.xlsx",
        "Gambar Tapak Projek (A3)",
        "Lukisan Perspektif Cadangan",
        "Pelan Ukur / Kontur",
        "Pelan Keratan Kerja Tanah",
        "Pelan Pokok Sedia Ada",
        "Laporan TIA Traffic Impact",
        "Laporan Geoteknikal dan Siasatan Tanah",
        "Laporan Kajian Pasaran Feasibility",
        "Laporan EIA JAS",
        "Laporan SIA",
        "Surat Perakuan TNB",
        "Surat Perakuan JKR",
        "Surat Kelulusan PTG WPKL"
    ]
    
    result = engine.score_documents(submitted_docs, stage="P2-KM")
    
    assert result.status == "pass"
    assert result.score > 90.0

def test_missing_documents_warning():
    """Test a submission missing a few critical documents."""
    engine = ComplianceEngine()
    
    # Missing: TIA, Geotechnical, EIA
    submitted_docs = [
        "Surat Iringan Permohonan",
        "Hakmilik Tanah (Geran)",
        "Resit Cukai Taksiran Semasa",
        "Borang Akuan Pembayaran",
        "Borang Akuan Kerja Rasmi Binaan",
    ]
    
    result = engine.score_documents(submitted_docs, stage="P2-KM")
    
    assert result.status == "fail"
    assert result.score < 50.0
    assert len(result.gaps) > 10

def test_contractor_license_validation():
    """Test CIDB contractor validation rules."""
    engine = ComplianceEngine()
    
    # 1. Valid: G5 contractor (max 5M) doing a 4.5M project
    valid, issues = engine.validate_contractor_license(
        grade="G5", category="CE", specialization="CE01", project_value=4500000
    )
    assert valid is True
    assert len(issues) == 0
    
    # 2. Invalid: G2 contractor (max 500k) doing a 2M project
    valid, issues = engine.validate_contractor_license(
        grade="G2", category="B", specialization="B04", project_value=2000000
    )
    assert valid is False
    assert "RM 500,000" in issues[0]

def test_epermit_prefill():
    """Test mapping project data to ePermit schema."""
    engine = ComplianceEngine()
    
    # Fake project state from Redis/Firestore
    project_data = {
        "project_name": "Cadangan Membina 2 Blok Kondominium",
        "scope": "Kerja-kerja Tanah",
        "client": "Maju Jaya Sdn Bhd",
        "contractor": "Bina Cepat Construction",
        "cidb_registration": "0120040823-WP123456",
        "location": "Lot 1234, Jalan Ampang, Kuala Lumpur",
    }
    
    # Simulate pre-filling the Excavation permit form
    form_data = engine.prefill_epermit_fields("excavation", project_data)
    
    assert form_data["nama_projek"] == "Cadangan Membina 2 Blok Kondominium"
    assert form_data["nama_syarikat"] == "Bina Cepat Construction"
    assert form_data["alamat"] == "Lot 1234, Jalan Ampang, Kuala Lumpur"


if __name__ == "__main__":
    # Allow running this file directly to see output
    print("--- Running Agent C Fake Data Tests ---")
    
    engine = ComplianceEngine()
    
    print("\n1. Testing Document Gap Analysis...")
    fake_docs = ["Surat Iringan", "Hakmilik Tanah", "Resit Cukai Taksiran"]
    res = engine.score_documents(fake_docs, stage="P2-KM")
    print(f"Submitted 3 docs. Score: {res.score:.1f}% | Status: {res.status.upper()}")
    print(f"Found {len(res.gaps)} missing documents. Example gaps:")
    for gap in res.gaps[:3]:
        print(f"  - {gap['description_ms']} ({gap['description_en']})")
        
    print("\n2. Testing Contractor CIDB Rules...")
    valid, issues = engine.validate_contractor_license("G3", "CE", "CE01", project_value=3_500_000)
    print(f"G3 Contractor attempting RM 3.5M project -> Valid? {valid}")
    if not valid:
        print(f"Issue: {issues[0]}")
        
    print("\n3. Testing ePermit Pre-fill...")
    fake_project = {
        "project_name": "Menara Berkembar Dummy",
        "contractor": "ABC Bina",
        "cidb_registration": "CIDB-123"
    }
    form = engine.prefill_epermit_fields("excavation", fake_project)
    print("Mapped fields for DBKL portal:")
    for k, v in form.items():
        if v: print(f"  {k} -> {v}")
