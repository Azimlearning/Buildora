/**
 * MilestoneForm.jsx — PM milestone submission form with variance analysis.
 * API: POST /milestones via postMilestone() from api/client.js
 * @param {{ projectId: string, onSuccess?: (milestone: object) => void }} props
 */
import { useState } from 'react';
import { CalendarDays, DollarSign, FileText, AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react';
import { postMilestone } from '../api/client.js';

const EMPTY = { name: '', planned_date: '', actual_date: '', planned_cost: '', actual_cost: '', notes: '' };

function FieldError({ msg }) {
  if (!msg) return null;
  return <p className="text-xs text-[#dc2626] mt-1">{msg}</p>;
}

function VarianceAlert({ type, msg }) {
  const cfg = {
    warning: { bg: 'rgba(217,119,6,0.10)', border: '#d97706', text: '#92400e' },
    error:   { bg: 'rgba(220,38,38,0.10)', border: '#dc2626', text: '#991b1b' },
    success: { bg: 'rgba(22,163,74,0.10)', border: '#16a34a', text: '#14532d' },
  }[type] ?? {};
  const Icon = type === 'success' ? CheckCircle2 : AlertTriangle;
  return (
    <div className="flex items-start gap-2.5 rounded-lg p-3 text-sm" style={{ background: cfg.bg, borderLeft: `3px solid ${cfg.border}` }}>
      <Icon className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: cfg.text }} />
      <span style={{ color: cfg.text }}>{msg}</span>
    </div>
  );
}

export default function MilestoneForm({ projectId, onSuccess }) {
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [variances, setVariances] = useState([]);
  const [submitted, setSubmitted] = useState(false);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const validate = () => {
    const e = {};
    if (!form.name.trim()) e.name = 'Milestone name is required';
    if (!form.planned_date) e.planned_date = 'Planned date is required';
    if (!form.actual_date) e.actual_date = 'Actual date is required';
    if (!form.planned_cost || isNaN(Number(form.planned_cost))) e.planned_cost = 'Enter a valid planned cost';
    if (!form.actual_cost || isNaN(Number(form.actual_cost))) e.actual_cost = 'Enter a valid actual cost';
    return e;
  };

  const computeVariances = (data) => {
    const vars = [];
    const dayDiff = Math.round((new Date(data.actual_date) - new Date(data.planned_date)) / 86400000);
    if (dayDiff > 0) vars.push({ type: 'warning', msg: `⚠ ${dayDiff} day${dayDiff !== 1 ? 's' : ''} behind schedule` });
    else if (dayDiff < 0) vars.push({ type: 'success', msg: `${Math.abs(dayDiff)} days ahead of schedule` });
    const pc = Number(data.planned_cost), ac = Number(data.actual_cost);
    if (pc > 0) {
      const pct = ((ac - pc) / pc * 100).toFixed(1);
      if (ac > pc) vars.push({ type: 'error', msg: `${pct}% over budget — escalated to Agent B` });
      else if (ac < pc) vars.push({ type: 'success', msg: `${Math.abs(pct)}% under budget` });
    }
    return vars;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length) return;
    setSubmitting(true);
    try {
      const payload = { project_id: projectId, ...form, planned_cost: Number(form.planned_cost), actual_cost: Number(form.actual_cost) };
      const result = await postMilestone(payload).catch(() => payload);
      setVariances(computeVariances(form));
      setSubmitted(true);
      onSuccess?.(result);
    } catch (err) {
      setErrors({ _global: err.message ?? 'Submission failed' });
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="space-y-4 animate-slide-up">
        <div className="flex items-center gap-2 text-[#16a34a]">
          <CheckCircle2 className="w-5 h-5" />
          <span className="font-semibold text-sm">Milestone submitted</span>
        </div>
        <div className="space-y-2">{variances.map((v, i) => <VarianceAlert key={i} {...v} />)}</div>
        <button onClick={() => { setForm(EMPTY); setVariances([]); setSubmitted(false); setErrors({}); }} className="btn btn-secondary text-sm">
          Add Another Milestone
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-5 animate-fade-in">
      <h3 className="font-semibold text-[#1c1b18]">Add Milestone</h3>
      {errors._global && <div className="card border-red-200 bg-red-50 p-3 text-sm text-red-700">{errors._global}</div>}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="sm:col-span-2">
          <label htmlFor="ms-name" className="label"><FileText className="inline w-3.5 h-3.5 mr-1 text-[#6b6860]" />Milestone Name</label>
          <input id="ms-name" type="text" placeholder="e.g. Roofing completion" value={form.name} onChange={set('name')} className={`input ${errors.name ? 'error' : ''}`} />
          <FieldError msg={errors.name} />
        </div>
        <div>
          <label htmlFor="ms-pd" className="label"><CalendarDays className="inline w-3.5 h-3.5 mr-1 text-[#6b6860]" />Planned Date</label>
          <input id="ms-pd" type="date" value={form.planned_date} onChange={set('planned_date')} className={`input ${errors.planned_date ? 'error' : ''}`} />
          <FieldError msg={errors.planned_date} />
        </div>
        <div>
          <label htmlFor="ms-ad" className="label"><CalendarDays className="inline w-3.5 h-3.5 mr-1 text-[#6b6860]" />Actual Date</label>
          <input id="ms-ad" type="date" value={form.actual_date} onChange={set('actual_date')} className={`input ${errors.actual_date ? 'error' : ''}`} />
          <FieldError msg={errors.actual_date} />
        </div>
        <div>
          <label htmlFor="ms-pc" className="label"><DollarSign className="inline w-3.5 h-3.5 mr-1 text-[#6b6860]" />Planned Cost (RM)</label>
          <input id="ms-pc" type="number" min="0" step="0.01" placeholder="0.00" value={form.planned_cost} onChange={set('planned_cost')} className={`input ${errors.planned_cost ? 'error' : ''}`} />
          <FieldError msg={errors.planned_cost} />
        </div>
        <div>
          <label htmlFor="ms-ac" className="label"><DollarSign className="inline w-3.5 h-3.5 mr-1 text-[#6b6860]" />Actual Cost (RM)</label>
          <input id="ms-ac" type="number" min="0" step="0.01" placeholder="0.00" value={form.actual_cost} onChange={set('actual_cost')} className={`input ${errors.actual_cost ? 'error' : ''}`} />
          <FieldError msg={errors.actual_cost} />
        </div>
        <div className="sm:col-span-2">
          <label htmlFor="ms-notes" className="label">Notes</label>
          <textarea id="ms-notes" rows={3} placeholder="Additional notes…" value={form.notes} onChange={set('notes')} className="input resize-none" />
        </div>
      </div>
      <button type="submit" disabled={submitting} className="btn btn-primary" aria-label="Submit milestone">
        {submitting ? <><Loader2 className="w-4 h-4 animate-spin" />Submitting…</> : 'Submit Milestone'}
      </button>
    </form>
  );
}
