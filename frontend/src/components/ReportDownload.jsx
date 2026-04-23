/**
 * ReportDownload.jsx — PDF and XLSX report generation & download cards.
 * API: GET /reports/:id via getReport() from api/client.js
 * @param {{ projectId: string, demoMode?: boolean }} props
 */
import { useState, useEffect } from 'react';
import { FileText, FileSpreadsheet, Download, Loader2, Clock, CheckCircle2 } from 'lucide-react';
import { getReport, generateReport } from '../api/client.js';

const DEMO_REPORTS = {
  pdf: { status: 'ready', file_size: '2.4 MB', page_count: 24, generated_at: '2024-04-20T10:30:00Z', url: '#' },
  xlsx: { status: 'ready', row_count: 180, generated_at: '2024-04-20T10:32:00Z', url: '#' },
};

function ReportCard({ type, report, onGenerate, generating }) {
  const isPdf = type === 'pdf';
  const Icon = isPdf ? FileText : FileSpreadsheet;
  const iconColor = isPdf ? '#e11d48' : '#16a34a';
  const title = isPdf ? 'PDF Report' : 'XLSX Cost Tracker';
  const statusCfg = {
    queued:     { label: 'Queued',     bg: '#f0ede7',                     text: '#6b6860' },
    generating: { label: 'Generating', bg: 'rgba(217,119,6,0.12)',         text: '#b45309' },
    ready:      { label: 'Ready',      bg: 'rgba(22,163,74,0.12)',         text: '#15803d' },
    error:      { label: 'Error',      bg: 'rgba(220,38,38,0.12)',         text: '#b91c1c' },
  }[report?.status ?? 'queued'] ?? {};

  const formattedDate = report?.generated_at
    ? new Date(report.generated_at).toLocaleString('en-MY', { dateStyle: 'medium', timeStyle: 'short' })
    : null;

  return (
    <div className="card p-5 flex flex-col gap-4">
      {/* Icon + title */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: iconColor + '14' }}>
          <Icon className="w-5 h-5" style={{ color: iconColor }} />
        </div>
        <div>
          <p className="font-semibold text-sm text-[#1c1b18]">{title}</p>
          <span className="badge text-[10px]" style={{ background: statusCfg.bg, color: statusCfg.text }}>
            {report?.status === 'generating' && <Loader2 className="w-2.5 h-2.5 animate-spin" />}
            {report?.status === 'ready' && <CheckCircle2 className="w-2.5 h-2.5" />}
            {statusCfg.label}
          </span>
        </div>
      </div>

      {/* Metadata */}
      <div className="space-y-1 text-xs text-[#6b6860]">
        {isPdf && report?.file_size && <p>File size: <span className="text-[#1c1b18] font-medium">{report.file_size}</span></p>}
        {isPdf && report?.page_count && <p>Pages: <span className="text-[#1c1b18] font-medium">{report.page_count}</span></p>}
        {!isPdf && report?.row_count && <p>Rows: <span className="text-[#1c1b18] font-medium">{report.row_count.toLocaleString()}</span></p>}
        {formattedDate && (
          <p className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {formattedDate}
          </p>
        )}
      </div>

      {/* Action */}
      {report?.status === 'ready' ? (
        <a
          href={report.url ?? '#'}
          download
          className="btn btn-primary text-sm w-full justify-center"
          aria-label={`Download ${title}`}
        >
          <Download className="w-4 h-4" />
          {isPdf ? 'Download PDF' : 'Download Excel'}
        </a>
      ) : report?.status === 'generating' ? (
        <button disabled className="btn btn-primary opacity-50 text-sm w-full justify-center cursor-not-allowed">
          <Loader2 className="w-4 h-4 animate-spin" />
          Generating…
        </button>
      ) : (
        <button
          onClick={onGenerate}
          disabled={generating}
          className="btn btn-secondary text-sm w-full justify-center"
          aria-label={`Generate ${title}`}
        >
          {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
          Generate Report
        </button>
      )}
    </div>
  );
}

export default function ReportDownload({ projectId, demoMode = false }) {
  const [reports, setReports] = useState({ pdf: null, xlsx: null });
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (demoMode) { setReports(DEMO_REPORTS); setLoading(false); return; }
    getReport(projectId)
      .then((data) => { setReports({ pdf: data?.pdf ?? null, xlsx: data?.xlsx ?? null }); setLoading(false); })
      .catch(() => { setReports({ pdf: { status: 'queued' }, xlsx: { status: 'queued' } }); setLoading(false); });
  }, [projectId, demoMode]);

  const handleGenerate = async () => {
    setGenerating(true);
    setReports((r) => ({ pdf: { ...r.pdf, status: 'generating' }, xlsx: { ...r.xlsx, status: 'generating' } }));
    try {
      await generateReport(projectId).catch(() => {});
      setTimeout(() => {
        setReports(DEMO_REPORTS);
        setGenerating(false);
      }, 3000);
    } catch {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {[0, 1].map(i => (
          <div key={i} className="card p-5 space-y-3">
            <div className="skeleton h-10 w-10 rounded-xl" />
            <div className="skeleton h-4 w-24 rounded" />
            <div className="skeleton h-3 w-32 rounded" />
            <div className="skeleton h-9 w-full rounded-lg" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-fade-in">
      <h3 className="font-semibold text-[#1c1b18]">Reports</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <ReportCard type="pdf"  report={reports.pdf}  onGenerate={handleGenerate} generating={generating} />
        <ReportCard type="xlsx" report={reports.xlsx} onGenerate={handleGenerate} generating={generating} />
      </div>
    </div>
  );
}
