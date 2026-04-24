/**
 * NotificationsPanel.jsx — Agent D Alert Display
 * 
 * Fetches notifications from the backend API and renders them as a
 * visually rich, categorised list.  Each alert shows an icon, severity
 * badge, countdown, and description.
 *
 * Categories:
 *   doc_submission, payment_due, account_receivable,
 *   extension_of_time, delay_detected, cost_overrun,
 *   permit_renewal, general
 *
 * Author: Khaidhir (Agent D)
 */
import { useState, useEffect } from 'react';
import {
  Bell,
  AlertTriangle,
  Clock,
  FileText,
  CreditCard,
  Receipt,
  Timer,
  ShieldAlert,
  TrendingUp,
  BadgeCheck,
  Send,
  RefreshCw,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { getNotifications } from '../api/client.js';

/* ── Category config ───────────────────────────────────────── */
const CATEGORY_CONFIG = {
  doc_submission:     { icon: FileText,     label: 'Document Submission', color: '#3b82f6', bg: '#eff6ff' },
  payment_due:        { icon: CreditCard,   label: 'Payment Due',         color: '#ef4444', bg: '#fef2f2' },
  account_receivable: { icon: Receipt,      label: 'Account Receivable',  color: '#8b5cf6', bg: '#f5f3ff' },
  extension_of_time:  { icon: Timer,        label: 'Extension of Time',   color: '#f59e0b', bg: '#fffbeb' },
  delay_detected:     { icon: AlertTriangle, label: 'Delay Detected',     color: '#dc2626', bg: '#fef2f2' },
  cost_overrun:       { icon: TrendingUp,   label: 'Cost Overrun',        color: '#ea580c', bg: '#fff7ed' },
  permit_renewal:     { icon: ShieldAlert,  label: 'Permit Renewal',      color: '#0891b2', bg: '#ecfeff' },
  general:            { icon: Bell,         label: 'General',             color: '#6b7280', bg: '#f9fafb' },
};

const SEVERITY_STYLES = {
  critical: { label: 'Critical', bg: '#fef2f2', color: '#dc2626', border: '#fecaca' },
  high:     { label: 'High',     bg: '#fff7ed', color: '#ea580c', border: '#fed7aa' },
  medium:   { label: 'Medium',   bg: '#fffbeb', color: '#d97706', border: '#fde68a' },
  low:      { label: 'Low',      bg: '#f0fdf4', color: '#16a34a', border: '#bbf7d0' },
  info:     { label: 'Info',     bg: '#eff6ff', color: '#2563eb', border: '#bfdbfe' },
};

/* ── Single alert card ─────────────────────────────────────── */
function AlertCard({ alert }) {
  const cat = CATEGORY_CONFIG[alert.category] || CATEGORY_CONFIG.general;
  const sev = SEVERITY_STYLES[alert.severity] || SEVERITY_STYLES.medium;
  const Icon = cat.icon;
  const days = alert.days_remaining;

  return (
    <div
      className="group relative flex gap-4 p-4 rounded-xl border transition-all duration-200 hover:shadow-md"
      style={{ borderColor: '#e4e2dc', backgroundColor: '#ffffff' }}
    >
      {/* Left icon */}
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5"
        style={{ backgroundColor: cat.bg }}
      >
        <Icon className="w-5 h-5" style={{ color: cat.color }} />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap mb-1">
          <span className="font-semibold text-sm text-[#1c1b18] truncate">{alert.title}</span>

          {/* Severity badge */}
          <span
            className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border"
            style={{ backgroundColor: sev.bg, color: sev.color, borderColor: sev.border }}
          >
            {sev.label}
          </span>

          {/* Category */}
          <span className="text-[10px] font-medium tracking-wide text-[#9b9794] uppercase hidden sm:inline">
            {cat.label}
          </span>
        </div>

        <p className="text-xs text-[#6b6860] leading-relaxed line-clamp-2">
          {alert.message}
        </p>
      </div>

      {/* Days countdown */}
      {days !== undefined && days !== null && (
        <div className="flex flex-col items-center justify-center flex-shrink-0 min-w-[56px]">
          <div
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold"
            style={{
              backgroundColor: days <= 3 ? '#fef2f2' : days <= 7 ? '#fffbeb' : '#f0fdf4',
              color: days <= 3 ? '#dc2626' : days <= 7 ? '#d97706' : '#16a34a',
            }}
          >
            <Clock className="w-3.5 h-3.5" />
            {days === 0 ? 'NOW' : `${days}d`}
          </div>
          {days > 0 && (
            <span className="text-[10px] text-[#9b9794] mt-0.5">remaining</span>
          )}
          {days === 0 && (
            <span className="text-[10px] text-red-500 font-semibold mt-0.5">OVERDUE</span>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Skeleton loader ───────────────────────────────────────── */
function SkeletonAlerts() {
  return (
    <div className="space-y-3 animate-pulse">
      {[1, 2, 3].map(i => (
        <div key={i} className="flex gap-4 p-4 rounded-xl border border-[#e4e2dc]">
          <div className="w-10 h-10 rounded-xl bg-[#e4e2dc]" />
          <div className="flex-1 space-y-2">
            <div className="h-4 w-48 bg-[#e4e2dc] rounded" />
            <div className="h-3 w-full bg-[#e4e2dc] rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Main panel ────────────────────────────────────────────── */
export default function NotificationsPanel({ projectId }) {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(true);
  const [filter, setFilter] = useState('all'); // all | critical | high | medium ...

  useEffect(() => {
    if (!projectId) return;
    setLoading(true);
    getNotifications(projectId)
      .then(data => { setNotifications(data.notifications || []); })
      .catch(() => { setNotifications([]); })
      .finally(() => setLoading(false));
  }, [projectId]);

  const handleRefresh = () => {
    setLoading(true);
    getNotifications(projectId)
      .then(data => { setNotifications(data.notifications || []); })
      .catch(() => { setNotifications([]); })
      .finally(() => setLoading(false));
  };

  const filtered = filter === 'all'
    ? notifications
    : notifications.filter(n => n.severity === filter);

  const criticalCount = notifications.filter(n => n.severity === 'critical').length;
  const highCount = notifications.filter(n => n.severity === 'high').length;

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-6 py-4 cursor-pointer select-none"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center shadow-sm">
            <Bell className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-[#1c1b18] font-outfit text-sm">
              Alerts & Notifications
            </h3>
            <p className="text-[10px] text-[#9b9794]">
              Agent D • {notifications.length} alert{notifications.length !== 1 ? 's' : ''}
              {criticalCount > 0 && (
                <span className="text-red-500 font-bold ml-1">• {criticalCount} critical</span>
              )}
              {highCount > 0 && (
                <span className="text-orange-500 font-semibold ml-1">• {highCount} high</span>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            className="p-1.5 rounded-lg hover:bg-[#f0efec] text-[#9b9794] hover:text-[#1c1b18] transition-colors"
            onClick={(e) => { e.stopPropagation(); handleRefresh(); }}
            title="Refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-[#9b9794]" />
          ) : (
            <ChevronDown className="w-4 h-4 text-[#9b9794]" />
          )}
        </div>
      </div>

      {expanded && (
        <div className="px-6 pb-5 space-y-4 animate-slide-up">
          {/* Filter chips */}
          <div className="flex gap-2 flex-wrap">
            {['all', 'critical', 'high', 'medium', 'low'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1 rounded-full text-[11px] font-semibold tracking-wide uppercase border transition-all ${
                  filter === f
                    ? 'bg-[#1c1b18] text-white border-[#1c1b18]'
                    : 'bg-white text-[#6b6860] border-[#e4e2dc] hover:border-[#9b9794]'
                }`}
              >
                {f === 'all' ? `All (${notifications.length})` : f}
              </button>
            ))}
          </div>

          {/* Alert list */}
          {loading ? (
            <SkeletonAlerts />
          ) : filtered.length === 0 ? (
            <div className="text-center py-8">
              <BadgeCheck className="w-10 h-10 text-green-400 mx-auto mb-2" />
              <p className="text-sm text-[#6b6860] font-medium">No alerts found</p>
              <p className="text-xs text-[#9b9794] mt-1">All clear for now!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filtered.map((alert, i) => (
                <AlertCard key={alert.id || i} alert={alert} />
              ))}
            </div>
          )}

          {/* Telegram status footer */}
          <div className="flex items-center gap-2 pt-3 border-t border-[#e4e2dc]">
            <Send className="w-3.5 h-3.5 text-[#0088cc]" />
            <span className="text-[11px] text-[#9b9794]">
              Alerts are also sent to the PM's Telegram
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
