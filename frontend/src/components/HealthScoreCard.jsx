/**
 * HealthScoreCard.jsx — Project Health Score Display
 *
 * Displays calculated health score (0-100) with visual breakdown.
 * Shows penalties from Agent B (monitoring), C (compliance), and D (alerts).
 *
 * Score Ranges:
 *   - 80-100: Healthy (green)
 *   - 60-79: Warning (yellow)
 *   - 0-59: Critical (red)
 *
 * Author: Buildora Team
 */
import { useState, useEffect } from 'react';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Info,
} from 'lucide-react';

/* ── Health ring visualization ─────────────────────────────── */
function HealthRing({ score, size = 140 }) {
  const color = score >= 80 ? '#16a34a' : score >= 60 ? '#d97706' : '#dc2626';
  const radius = (size - 16) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg className="w-full h-full transform -rotate-90" viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#e4e2dc"
          strokeWidth="8"
          fill="transparent"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth="8"
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span className="text-4xl font-bold font-outfit" style={{ color }}>
          {score}
        </span>
        <span className="text-[10px] text-[#9b9794] font-medium uppercase tracking-wider">
          Health
        </span>
      </div>
    </div>
  );
}

/* ── Breakdown bar ─────────────────────────────────────────── */
function BreakdownBar({ label, penalty, maxPenalty, color }) {
  const percentage = maxPenalty > 0 ? (penalty / maxPenalty) * 100 : 0;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-[#6b6860] font-medium">{label}</span>
        <span className="text-[#1c1b18] font-bold">-{penalty} pts</span>
      </div>
      <div className="h-2 bg-[#f0efec] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${percentage}%`,
            backgroundColor: color,
          }}
        />
      </div>
    </div>
  );
}

/* ── Skeleton loader ───────────────────────────────────────── */
function SkeletonHealthScore() {
  return (
    <div className="animate-pulse space-y-6">
      <div className="flex justify-center">
        <div className="w-36 h-36 rounded-full bg-[#e4e2dc]" />
      </div>
      <div className="space-y-3">
        {[1, 2, 3].map(i => (
          <div key={i} className="space-y-1.5">
            <div className="h-3 w-32 bg-[#e4e2dc] rounded" />
            <div className="h-2 w-full bg-[#e4e2dc] rounded-full" />
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Main component ────────────────────────────────────────── */
export default function HealthScoreCard({ projectId, compact = false }) {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!projectId) return;
    fetchHealthScore();
  }, [projectId]);

  const fetchHealthScore = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/projects/${projectId}/health`);
      if (!response.ok) throw new Error('Failed to fetch health score');
      const data = await response.json();
      setHealthData(data);
    } catch (err) {
      console.error('Health score fetch error:', err);
      setError(err.message);
      // Fallback to default
      setHealthData({
        health_score: 0,
        status: 'unknown',
        breakdown: {
          monitoring_penalty: 0,
          compliance_penalty: 0,
          alerts_penalty: 0,
        },
        details: {
          delays: 0,
          cost_variance: 0,
          compliance: 100,
          critical_alerts: 0,
        },
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="card p-6">
        <SkeletonHealthScore />
      </div>
    );
  }

  const score = healthData?.health_score || 0;
  const status = healthData?.status || 'unknown';
  const breakdown = healthData?.breakdown || {};
  const details = healthData?.details || {};

  const statusConfig = {
    healthy: { label: 'Healthy', color: '#16a34a', bg: '#f0fdf4', icon: CheckCircle },
    warning: { label: 'Warning', color: '#d97706', bg: '#fffbeb', icon: AlertTriangle },
    critical: { label: 'Critical', color: '#dc2626', bg: '#fef2f2', icon: AlertTriangle },
    unknown: { label: 'Unknown', color: '#6b7280', bg: '#f9fafb', icon: Info },
  };

  const config = statusConfig[status] || statusConfig.unknown;
  const StatusIcon = config.icon;

  if (compact) {
    return (
      <div className="flex items-center gap-4 p-4 rounded-xl border border-[#e4e2dc] bg-white">
        <HealthRing score={score} size={80} />
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-semibold text-[#1c1b18]">Project Health</span>
            <span
              className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider"
              style={{ backgroundColor: config.bg, color: config.color }}
            >
              {config.label}
            </span>
          </div>
          <p className="text-xs text-[#6b6860]">
            Based on monitoring, compliance, and alerts
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-[#e4e2dc]">
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center shadow-sm"
            style={{ backgroundColor: config.bg }}
          >
            <StatusIcon className="w-4 h-4" style={{ color: config.color }} />
          </div>
          <div>
            <h3 className="font-semibold text-[#1c1b18] font-outfit text-sm">
              Health Score
            </h3>
            <p className="text-[10px] text-[#9b9794]">
              Combined metrics from all agents
            </p>
          </div>
        </div>

        <button
          className="p-1.5 rounded-lg hover:bg-[#f0efec] text-[#9b9794] hover:text-[#1c1b18] transition-colors"
          onClick={fetchHealthScore}
          title="Refresh"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Score ring */}
        <div className="flex flex-col items-center">
          <HealthRing score={score} size={140} />
          <div
            className="mt-4 px-4 py-2 rounded-full text-sm font-bold uppercase tracking-wider"
            style={{ backgroundColor: config.bg, color: config.color }}
          >
            {config.label}
          </div>
        </div>

        {/* Breakdown */}
        <div className="space-y-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-[#9b9794]">
            Score Breakdown
          </h4>

          <BreakdownBar
            label="Monitoring Penalties"
            penalty={breakdown.monitoring_penalty || 0}
            maxPenalty={40}
            color="#dc2626"
          />

          <BreakdownBar
            label="Compliance Penalties"
            penalty={breakdown.compliance_penalty || 0}
            maxPenalty={40}
            color="#ea580c"
          />

          <BreakdownBar
            label="Alert Penalties"
            penalty={breakdown.alerts_penalty || 0}
            maxPenalty={20}
            color="#d97706"
          />
        </div>

        {/* Details */}
        <div className="grid grid-cols-2 gap-3 pt-4 border-t border-[#e4e2dc]">
          <div className="text-center p-3 rounded-lg bg-[#f9fafb]">
            <p className="text-xs text-[#9b9794] mb-1">Delays</p>
            <p className="text-lg font-bold text-[#1c1b18] font-outfit">
              {details.delays || 0}
            </p>
          </div>
          <div className="text-center p-3 rounded-lg bg-[#f9fafb]">
            <p className="text-xs text-[#9b9794] mb-1">Cost Issues</p>
            <p className="text-lg font-bold text-[#1c1b18] font-outfit">
              {details.cost_variance || 0}
            </p>
          </div>
          <div className="text-center p-3 rounded-lg bg-[#f9fafb]">
            <p className="text-xs text-[#9b9794] mb-1">Compliance</p>
            <p className="text-lg font-bold text-[#1c1b18] font-outfit">
              {Math.round(details.compliance || 0)}%
            </p>
          </div>
          <div className="text-center p-3 rounded-lg bg-[#f9fafb]">
            <p className="text-xs text-[#9b9794] mb-1">Critical Alerts</p>
            <p className="text-lg font-bold text-[#1c1b18] font-outfit">
              {details.critical_alerts || 0}
            </p>
          </div>
        </div>

        {/* Info footer */}
        <div className="flex items-start gap-2 p-3 rounded-lg bg-blue-50 border border-blue-100">
          <Info className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-blue-700 leading-relaxed">
            Health score is calculated from Agent B (monitoring), Agent C (compliance),
            and Agent D (alerts). Score updates automatically when agents run.
          </p>
        </div>
      </div>
    </div>
  );
}
