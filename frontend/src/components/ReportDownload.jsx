/**
 * ReportDownload.jsx — PDF, XLSX and CIBD document generation & download.
 * Calls POST /api/reports/:id/generate and GET /api/reports/:id/download/:format
 */
import { useState, useEffect } from 'react';
import {
  FileText, FileSpreadsheet, Download, Loader2, Clock,
  CheckCircle2, Shield, RefreshCw, ChevronDown, ChevronUp, AlertTriangle
} from 'lucide-react';

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

// CIDB document types from knowledge_base
const CIBD_DOCS = [
  { key: 'pre_construction_checklist', label: 'Pre-Construction Checklist', icon: '📋', desc: 'Form of Tender, Letter of Award, Works Programme, CTMP, JHA' },
  { key: 'during_construction_checklist', label: 'During Construction Register', icon: '🏗️', desc: 'Early Warning Register, Interim Certificates, Mill Certificates, COA' },
  { key: 'handover_checklist', label: 'Handover Checklist', icon: '🏁', desc: 'CPC, CMGD, Final Certificate, Certificate of Determination Cost' },
  { key: 'compliance_report', label: 'CIDB Compliance Report', icon: '✅', desc: 'Contractor grade validation, required docs, compliance gaps analysis' },
];

function StatusBadge({ status }) {
  const configs = {
    queued:     { label: 'Not Generated', bg: '#f0ede7', text: '#6b6860' },
    generating: { label: 'Generating…',  bg: 'rgba(217,119,6,0.12)', text: '#b45309' },
    ready:      { label: 'Ready',         bg: 'rgba(22,163,74,0.12)', text: '#15803d' },
    error:      { label: 'Error',         bg: 'rgba(220,38,38,0.12)', text: '#b91c1c' },
  };
  const cfg = configs[status ?? 'queued'] ?? configs.queued;
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider"
      style={{ background: cfg.bg, color: cfg.text }}>
      {status === 'generating' && <Loader2 className="w-2.5 h-2.5 animate-spin" />}
      {status === 'ready' && <CheckCircle2 className="w-2.5 h-2.5" />}
      {cfg.label}
    </span>
  );
}

function ReportCard({ type, icon: Icon, iconColor, title, description, status, onGenerate, onDownload, generating, metadata }) {
  const isReady = status === 'ready';
  const isGenerating = status === 'generating' || generating;

  return (
    <div className="card p-5 flex flex-col gap-4 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ background: iconColor + '14' }}>
          <Icon className="w-5 h-5" style={{ color: iconColor }} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm text-[#1c1b18]">{title}</p>
          <p className="text-xs text-[#9b9794] mt-0.5 leading-relaxed">{description}</p>
          <div className="mt-2">
            <StatusBadge status={status} />
          </div>
        </div>
      </div>

      {metadata && (
        <div className="text-xs text-[#6b6860] space-y-0.5 pl-1">
          {metadata.file_size && <p>Size: <span className="text-[#1c1b18] font-medium">{metadata.file_size}</span></p>}
          {metadata.page_count && <p>Pages: <span className="text-[#1c1b18] font-medium">{metadata.page_count}</span></p>}
          {metadata.row_count && <p>Rows: <span className="text-[#1c1b18] font-medium">{metadata.row_count.toLocaleString()}</span></p>}
          {metadata.generated_at && (
            <p className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {new Date(metadata.generated_at).toLocaleString('en-MY', { dateStyle: 'medium', timeStyle: 'short' })}
            </p>
          )}
        </div>
      )}

      {isReady ? (
        <button
          onClick={onDownload}
          className="btn btn-primary text-sm w-full justify-center"
          aria-label={`Download ${title}`}
        >
          <Download className="w-4 h-4" />
          Download {type.toUpperCase()}
        </button>
      ) : isGenerating ? (
        <button disabled className="btn btn-primary opacity-50 text-sm w-full justify-center cursor-not-allowed">
          <Loader2 className="w-4 h-4 animate-spin" />
          Generating…
        </button>
      ) : (
        <button onClick={onGenerate} className="btn btn-secondary text-sm w-full justify-center" aria-label={`Generate ${title}`}>
          <FileText className="w-4 h-4" />
          Generate
        </button>
      )}
    </div>
  );
}

function CibdDocCard({ doc, projectId, generating, onGenerate, status }) {
  return (
    <div className="flex items-center gap-4 p-4 rounded-xl border border-[#e4e2dc] bg-white hover:shadow-sm transition-shadow">
      <div className="text-2xl flex-shrink-0">{doc.icon}</div>
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-sm text-[#1c1b18]">{doc.label}</p>
        <p className="text-[11px] text-[#9b9794] mt-0.5 truncate">{doc.desc}</p>
      </div>
      <div className="flex-shrink-0">
        {status === 'generating' ? (
          <button disabled className="btn btn-ghost text-xs opacity-50 cursor-not-allowed flex items-center gap-1.5">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            Generating…
          </button>
        ) : status === 'ready' ? (
          <button
            onClick={() => onGenerate(doc.key, 'download')}
            className="btn btn-ghost text-xs flex items-center gap-1.5 text-green-600 hover:text-green-700"
          >
            <Download className="w-3.5 h-3.5" />
            Download
          </button>
        ) : (
          <button
            onClick={() => onGenerate(doc.key)}
            disabled={generating}
            className="btn btn-ghost text-xs flex items-center gap-1.5"
          >
            <FileText className="w-3.5 h-3.5" />
            Generate
          </button>
        )}
      </div>
    </div>
  );
}

export default function ReportDownload({ projectId, project }) {
  const [reportStatus, setReportStatus] = useState({ pdf: null, xlsx: null });
  const [cibdStatus, setCibdStatus] = useState({});
  const [generating, setGenerating] = useState(false);
  const [cibdExpanded, setCibdExpanded] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Try to load existing report status
    fetch(`${BASE}/api/reports/${projectId}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data) {
          setReportStatus({
            pdf: data.pdf ?? null,
            xlsx: data.xlsx ?? null,
          });
        }
      })
      .catch(() => {});
  }, [projectId]);

  const generateMainReports = async () => {
    setGenerating(true);
    setError(null);
    setReportStatus({ pdf: { status: 'generating' }, xlsx: { status: 'generating' } });

    try {
      const res = await fetch(`${BASE}/api/reports/${projectId}/generate`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project }),
      });
      if (!res.ok) throw new Error('Generation failed');
      const data = await res.json();

      // Poll for completion
      pollReportStatus();
    } catch (err) {
      setError('Report generation failed: ' + err.message);
      setReportStatus({ pdf: { status: 'error' }, xlsx: { status: 'error' } });
      setGenerating(false);
    }
  };

  const pollReportStatus = () => {
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      try {
        const res = await fetch(`${BASE}/api/reports/${projectId}`);
        if (res.ok) {
          const data = await res.json();
          if (data.pdf?.status === 'ready' || data.xlsx?.status === 'ready' || attempts > 30) {
            clearInterval(interval);
            setReportStatus({ pdf: data.pdf ?? { status: 'ready' }, xlsx: data.xlsx ?? { status: 'ready' } });
            setGenerating(false);
          }
        }
      } catch {
        if (attempts > 30) { clearInterval(interval); setGenerating(false); }
      }
    }, 2000);
  };

  const downloadReport = (format) => {
    const url = `${BASE}/api/reports/${projectId}/download/${format}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = `${(project?.name || 'project').replace(/\s+/g, '_')}_report.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleCibdGenerate = async (docKey, action) => {
    if (action === 'download') {
      const url = `${BASE}/api/reports/${projectId}/download/cibd/${docKey}`;
      const a = document.createElement('a');
      a.href = url;
      a.download = `${docKey}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      return;
    }

    setCibdStatus(prev => ({ ...prev, [docKey]: 'generating' }));
    try {
      const res = await fetch(`${BASE}/api/reports/${projectId}/generate/cibd`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doc_type: docKey, project }),
      });
      if (res.ok) {
        setCibdStatus(prev => ({ ...prev, [docKey]: 'ready' }));
      } else {
        throw new Error('Failed');
      }
    } catch {
      setCibdStatus(prev => ({ ...prev, [docKey]: 'error' }));
    }
  };

  const pdfStatus = reportStatus.pdf?.status;
  const xlsxStatus = reportStatus.xlsx?.status;

  return (
    <div className="space-y-6 animate-fade-in pb-8">
      <div>
        <h3 className="font-semibold text-[#1c1b18] text-base font-outfit mb-1">Reports</h3>
        <p className="text-xs text-[#9b9794]">Generate project reports and CIBD-specific compliance documents.</p>
      </div>

      {error && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-red-50 border border-red-200">
          <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Main reports */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <ReportCard
          type="pdf"
          icon={FileText}
          iconColor="#e11d48"
          title="PDF Project Report"
          description="Comprehensive project summary including health score, compliance status, schedule analysis, and recommendations."
          status={pdfStatus}
          generating={generating}
          metadata={reportStatus.pdf}
          onGenerate={generateMainReports}
          onDownload={() => downloadReport('pdf')}
        />
        <ReportCard
          type="xlsx"
          icon={FileSpreadsheet}
          iconColor="#16a34a"
          title="Excel Cost Tracker"
          description="Detailed cost variance table, milestone tracker, and budget breakdown across all project phases."
          status={xlsxStatus}
          generating={generating}
          metadata={reportStatus.xlsx}
          onGenerate={generateMainReports}
          onDownload={() => downloadReport('xlsx')}
        />
      </div>

      {/* CIBD Documents */}
      <div className="card overflow-hidden">
        <div
          className="flex items-center justify-between px-5 py-4 cursor-pointer select-none"
          onClick={() => setCibdExpanded(!cibdExpanded)}
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
              <Shield className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <h4 className="font-semibold text-sm text-[#1c1b18] font-outfit">CIBD Compliance Documents</h4>
              <p className="text-[11px] text-[#9b9794]">Generate standard CIDB forms and checklists</p>
            </div>
          </div>
          {cibdExpanded ? <ChevronUp className="w-4 h-4 text-[#9b9794]" /> : <ChevronDown className="w-4 h-4 text-[#9b9794]" />}
        </div>

        {cibdExpanded && (
          <div className="px-5 pb-5 space-y-3 border-t border-[#e4e2dc] pt-4 animate-slide-up">
            {CIBD_DOCS.map(doc => (
              <CibdDocCard
                key={doc.key}
                doc={doc}
                projectId={projectId}
                generating={generating}
                status={cibdStatus[doc.key]}
                onGenerate={handleCibdGenerate}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
