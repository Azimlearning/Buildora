/**
 * MonitoringPanel.jsx — Agent B Monitoring Display
 *
 * Displays schedule delays and cost variance alerts detected by Agent B.
 * Shows real-time project health metrics with visual indicators.
 *
 * Alert Types:
 *   - Delay alerts (>3 days threshold)
 *   - Cost variance alerts (>8% threshold)
 *   - Anomaly alerts
 *
 * Author: Buildora Team
 */
import { useState, useEffect } from 'react';
import {
  Activity,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Clock,
  DollarSign,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  CheckCircle,
  XCircle,
} from 'lucide-react';

/* ── Alert severity styles ─────────────────────────────────── */
const SEVERITY_STYLES = {
  critical: { bg: '#fef2f2', color: '#dc2626', border: '#fecaca', label: 'Critical' },
  high:     { bg: '#fff7ed', color: '#ea580c', border: '#fed7aa', label: 'High' },
  medium:   { bg: '#fffbeb', color: '#d97706', border: '#fde68a', label: 'Medium' },
  low:      { bg: '#f0fdf4', color: '#16a34a', border: '#bbf7d0', label: 'Low' },
};

/* ── Alert type config ─────────────────────────────────────── */
const ALERT_TYPE_CONFIG = {
  delay: { icon: Clock, label: 'Schedule Delay', color: '#dc2626', bg: '#fef2f2' },
  cost_variance: { icon: DollarSign, label: 'Cost Variance', color: '#ea580c', bg: '#fff7ed' },
  anomaly: { icon: AlertTriangle, label: 'Anomaly', color: '#d97706', bg: '#fffbeb' },
};

/* ── Single alert card ─────────────────────────────────────── */
function MonitoringAlertCard({ alert }) {
  const typeConfig = ALERT_TYPE_CONFIG[alert.type] || ALERT_TYPE_CONFIG.anomaly;
  const sevStyle = SEVERITY_STYLES[alert.severity] || SEVERITY_STYLES.medium;
  const Icon = typeConfig.icon;

  return (
    <div
      className="group relative flex gap-4 p-4 rounded-xl border transition-all duration-200 hover:shadow-md"
      style={{ borderColor: '#e4e2dc', backgroundColor: '#ffffff' }}
    >
      {/* Left icon */}
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5"
        style={{ backgroundColor: typeConfig.bg }}
      >
        <Icon className="w-5 h-5" style={{ color: typeConfig.color }} />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap mb-1">
          <span className="font-semibold text-sm text-[#1c1b18]">{typeConfig.label}</span>

          {/* Severity badge */}
          <span
            className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border"
            style={{ backgroundColor: sevStyle.bg, color: sevStyle.color, borderColor: sevStyle.border }}
          >
            {sevStyle.label}
          </span>
        </div>

        <p className="text-xs text-[#6b6860] leading-relaxed">
          {alert.message}
        </p>

        {/* Metadata */}
        {alert.metadata && (
          <div className="flex gap-3 mt-2 text-[10px] text-[#9b9794]">
            {alert.metadata.milestone && (
              <span>Milestone: {alert.metadata.milestone}</span>
            )}
            {alert.metadata.variance && (
              <span>Variance: {alert.metadata.variance}</span>
            )}
            {alert.metadata.days_overdue && (
              <span className="text-red-500 font-semibold">
                {alert.metadata.days_overdue} days overdue
              </span>
            )}
          </div>
        )}
      </div>

      {/* Status indicator */}
      {alert.requires_action && (
        <div className="flex items-center justify-center flex-shrink-0">
          <div className="px-2.5 py-1 rounded-lg bg-red-50 border border-red-200">
            <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider">
              Action Required
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Summary metrics ───────────────────────────────────────── */
function MetricCard({ icon: Icon, label, value, trend, color }) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-xl border border-[#e4e2dc] bg-white">
      <div
        className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
        style={{ backgroundColor: color + '15' }}
      >
        <Icon className="w-5 h-5" style={{ color }} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[10px] text-[#9b9794] uppercase tracking-wider font-semibold">{label}</p>
        <div className="flex items-center gap-2">
          <span className="text-lg font-bold text-[#1c1b18] font-outfit">{value}</span>
          {trend !== undefined && (
            <span className={`text-xs font-semibold ${trend > 0 ? 'text-red-500' : 'text-green-500'}`}>
              {trend > 0 ? '+' : ''}{trend}%
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Skeleton loader ───────────────────────────────────────── */
function SkeletonMonitoring() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-20 rounded-xl bg-[#e4e2dc]" />
        ))}
      </div>
      <div className="space-y-3">
        {[1, 2].map(i => (
          <div key={i} className="flex gap-4 p-4 rounded-xl border border-[#e4e2dc]">
            <div className="w-10 h-10 rounded-xl bg-[#e4e2dc]" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-48 bg-[#e4e2dc] rounded" />
              <div className="h-3 w-full bg-[#e4e2dc] rounded" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Main panel ────────────────────────────────────────────── */
export default function MonitoringPanel({ projectId }) {
  const [monitoring, setMonitoring] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    if (!projectId) return;
    fetchMonitoring();
  }, [projectId]);

  const fetchMonitoring = async () => {
    setLoading(true);
    try {
      // Fetch project data which includes monitoring_results from Agent B
      const response = await fetch(`/api/projects/${projectId}`);
      const project = await response.json();
      setMonitoring(project.monitoring_results || {
        total_alerts: 0,
        critical_alerts: 0,
        delay_alerts: [],
        cost_variance_alerts: [],
        anomaly_alerts: [],
        alerts: []
      });
    } catch (error) {
      console.error('Failed to fetch monitoring data:', error);
      setMonitoring({
        total_alerts: 0,
        critical_alerts: 0,
        delay_alerts: [],
        cost_variance_alerts: [],
        anomaly_alerts: [],
        alerts: []
      });
    } finally {
      setLoading(false);
    }
  };

  if (!monitoring && !loading) return null;

  const allAlerts = monitoring?.alerts || [];
  const delayCount = monitoring?.delay_alerts?.length || 0;
  const costCount = monitoring?.cost_variance_alerts?.length || 0;
  const criticalCount = monitoring?.critical_alerts || 0;

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-6 py-4 cursor-pointer select-none"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center shadow-sm">
            <Activity className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-[#1c1b18] font-outfit text-sm">
              Project Monitoring
            </h3>
            <p className="text-[10px] text-[#9b9794]">
              Agent B • {allAlerts.length} alert{allAlerts.length !== 1 ? 's' : ''}
              {criticalCount > 0 && (
                <span className="text-red-500 font-bold ml-1">• {criticalCount} critical</span>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            className="p-1.5 rounded-lg hover:bg-[#f0efec] text-[#9b9794] hover:text-[#1c1b18] transition-colors"
            onClick={(e) => { e.stopPropagation(); fetchMonitoring(); }}
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
          {loading ? (
            <SkeletonMonitoring />
          ) : (
            <>
              {/* Summary metrics */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <MetricCard
                  icon={AlertTriangle}
                  label="Total Alerts"
                  value={allAlerts.length}
                  color="#f59e0b"
                />
                <MetricCard
                  icon={Clock}
                  label="Schedule Delays"
                  value={delayCount}
                  color="#dc2626"
                />
                <MetricCard
                  icon={DollarSign}
                  label="Cost Variances"
                  value={costCount}
                  color="#ea580c"
                />
              </div>

              {/* Alert list */}
              {allAlerts.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle className="w-10 h-10 text-green-400 mx-auto mb-2" />
                  <p className="text-sm text-[#6b6860] font-medium">No monitoring alerts</p>
                  <p className="text-xs text-[#9b9794] mt-1">Project is on track!</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {allAlerts.map((alert, i) => (
                    <MonitoringAlertCard key={alert.id || i} alert={alert} />
                  ))}
                </div>
              )}

              {/* Status footer */}
              <div className="flex items-center gap-2 pt-3 border-t border-[#e4e2dc]">
                <Activity className="w-3.5 h-3.5 text-blue-500" />
                <span className="text-[11px] text-[#9b9794]">
                  Monitoring thresholds: Delay &gt;3 days, Cost variance &gt;8%
                </span>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
