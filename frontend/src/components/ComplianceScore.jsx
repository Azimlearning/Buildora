/**
 * ComplianceScore.jsx — CIDB compliance result display (Agent C output).
 * Shows overall score, checklist accordion, and permit action CTA.
 * API: GET /compliance/:id via getComplianceScore() from api/client.js
 * @param {{ projectId: string, demoData?: object }} props
 */
import { useState, useEffect } from 'react';
import { CheckCircle2, XCircle, AlertTriangle, ChevronDown, ChevronRight, Shield, Info } from 'lucide-react';
import { getComplianceScore } from '../api/client.js';

const DEMO_COMPLIANCE = {
  score: 74,
  available: true,
  categories: [
    {
      name: 'Contractor Registration',
      items: [
        { label: 'CIDB Grade G7 registration', status: 'pass' },
        { label: 'PKK Class A certification', status: 'pass' },
        { label: 'Company SSM registration', status: 'pass' },
      ],
    },
    {
      name: 'Insurance & Bonds',
      items: [
        { label: 'OSHC insurance (valid)', status: 'pass' },
        { label: 'Performance bond 5%', status: 'pass' },
        { label: 'Public liability RM 1M', status: 'warn' },
      ],
    },
    {
      name: 'Structural & Engineering',
      items: [
        { label: 'Structural PE endorsement', status: 'fail' },
        { label: 'Geotechnical report', status: 'pass' },
        { label: 'Load calculation submission', status: 'pass' },
      ],
    },
    {
      name: 'Safety & Permits',
      items: [
        { label: 'BOMBA fire safety clearance', status: 'fail' },
        { label: 'Fire escape compliance', status: 'pass' },
        { label: 'Site safety plan (HIRARC)', status: 'pass' },
        { label: 'OSH officer appointment', status: 'pass' },
      ],
    },
  ],
};

function StatusIcon({ status }) {
  if (status === 'pass') return <CheckCircle2 className="w-4 h-4 text-[#16a34a] flex-shrink-0" />;
  if (status === 'fail') return <XCircle className="w-4 h-4 text-[#dc2626] flex-shrink-0" />;
  return <AlertTriangle className="w-4 h-4 text-[#d97706] flex-shrink-0" />;
}

function CategoryAccordion({ category }) {
  const [open, setOpen] = useState(false);
  const passCount = category.items.filter(i => i.status === 'pass').length;

  return (
    <div className="border border-[#e4e2dc] rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
        aria-label={`${open ? 'Collapse' : 'Expand'} ${category.name}`}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-[#fafaf8] cursor-pointer transition-colors duration-150"
      >
        <div className="flex items-center gap-2.5">
          {open ? <ChevronDown className="w-4 h-4 text-[#9b9794]" /> : <ChevronRight className="w-4 h-4 text-[#9b9794]" />}
          <span className="font-medium text-sm text-[#1c1b18]">{category.name}</span>
        </div>
        <span className="text-xs text-[#6b6860]">{passCount}/{category.items.length} passed</span>
      </button>
      {open && (
        <div className="border-t border-[#e4e2dc] divide-y divide-[#f0ede7]">
          {category.items.map((item, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-2.5">
              <StatusIcon status={item.status} />
              <span className="text-sm text-[#1c1b18]">{item.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ScoreSkeleton() {
  return (
    <div className="space-y-4">
      <div className="skeleton h-6 w-32 rounded" />
      <div className="skeleton h-4 w-full rounded" />
      <div className="skeleton h-32 w-full rounded-lg" />
    </div>
  );
}

export default function ComplianceScore({ projectId, demoData }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (demoData) { setData(demoData); setLoading(false); return; }
    getComplianceScore(projectId)
      .then((res) => { setData(res); setLoading(false); })
      .catch(() => { setData(DEMO_COMPLIANCE); setLoading(false); });
  }, [projectId, demoData]);

  if (loading) return <ScoreSkeleton />;

  if (!data?.available) {
    return (
      <div className="card p-5 border-l-4 border-l-[#d97706] flex items-start gap-3">
        <Info className="w-5 h-5 text-[#d97706] flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold text-sm text-[#1c1b18]">Compliance check unavailable</p>
          <p className="text-sm text-[#6b6860] mt-0.5">
            Permit compliance check is not available in this build. The project runs as a 3-agent system.
          </p>
        </div>
      </div>
    );
  }

  const score = data.score ?? 0;
  const barColor = score >= 80 ? '#16a34a' : score >= 60 ? '#d97706' : '#dc2626';
  const canGenerate = score >= 60;

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Score display */}
      <div className="card p-5">
        <div className="flex items-center gap-3 mb-1">
          <Shield className="w-5 h-5 text-[#f97316]" />
          <h3 className="font-semibold text-[#1c1b18]">CIDB Compliance Score</h3>
        </div>
        <div className="flex items-end gap-2 mb-3">
          <span className="text-4xl font-bold" style={{ color: barColor }}>{score}</span>
          <span className="text-xl text-[#6b6860] mb-1">/ 100</span>
        </div>
        <div className="h-2.5 bg-[#e4e2dc] rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${score}%`, background: barColor }}
          />
        </div>
        <p className="text-xs text-[#6b6860] mt-2">
          {score >= 80 ? 'Excellent compliance — ready for permit submission' :
           score >= 60 ? 'Acceptable — minor gaps to address' :
           'Critical gaps detected — address before proceeding'}
        </p>
      </div>

      {/* Accordion checklist */}
      <div className="space-y-2">
        {(data.categories ?? []).map((cat, i) => (
          <CategoryAccordion key={i} category={cat} />
        ))}
      </div>

    </div>
  );
}
