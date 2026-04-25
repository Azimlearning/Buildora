/**
 * AgentPanel.jsx — Live multi-agent trace viewer (P0 Demo Hook).
 * Shows 4 AI agents processing a construction document in real time.
 * Real backend: SSE via EventSource at GET /agent-stream/:jobId
 * Demo fallback: simulated streaming via setInterval at ~80ms per log line.
 * @param {{ jobId?: string, demoMode?: boolean, autoStart?: boolean }} props
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { ChevronDown, ChevronRight, Clock, FileText, CheckCircle2, XCircle, Loader2, Zap } from 'lucide-react';
import { getAgentStreamUrl } from '../api/client.js';

/* ─── Agent definitions ─── */
const AGENTS = [
  {
    id: 'a',
    label: 'Agent A',
    role: 'Document Reader',
    color: '#f97316',
    bgSoft: 'rgba(249,115,22,0.10)',
    demoLogs: [
      'Initialising document parser…',
      'Reading contract_phase2.pdf (4.2 MB)',
      'Extracting text layers — 47 pages',
      'Parsing clause 3.2: Payment milestones',
      'Detected 12 milestone entries',
      'Cross-referencing BOQ table on p.18',
      'Entity extraction complete: 3 contractors, 8 dates',
      'Forwarding structured payload to Agent B',
      '✓ Document analysis complete',
    ],
    demoFile: 'contract_phase2.pdf',
    demoDuration: 2000,
  },
  {
    id: 'b',
    label: 'Agent B',
    role: 'Schedule Monitor',
    color: '#e11d48',
    bgSoft: 'rgba(225,29,72,0.10)',
    demoLogs: [
      'Received payload from Agent A',
      'Loading project_schedule_v3.xlsx',
      'Parsing Gantt data — 34 tasks',
      'Computing critical path…',
      'Milestone 4 (Roofing): planned 2024-03-15',
      'Milestone 4 actual: 2024-03-29 ⚠ 14d delay',
      'Milestone 6 (MEP rough-in): on track',
      'Cost variance analysis: +12.4% over budget',
      'Escalation flag set for Agent D',
      '✓ Schedule monitoring complete',
    ],
    demoFile: 'project_schedule_v3.xlsx',
    demoDuration: 1500,
  },
  {
    id: 'c',
    label: 'Agent C',
    role: 'CIDB Compliance',
    color: '#d97706',
    bgSoft: 'rgba(217,119,6,0.10)',
    demoLogs: [
      'Loading CIDB permit requirements 2024',
      'Reading site_permit_application.pdf',
      'Checking contractor grade: G7 ✓',
      'Validating OSHC insurance: valid until 2025-06 ✓',
      'Checking PAM contract clause 23',
      'Fire escape compliance: PASS ✓',
      'Structural PE endorsement: MISSING ⚠',
      'BOMBA clearance: pending submission',
      'Overall CIDB score: 74/100',
      '✓ Compliance check complete',
    ],
    demoFile: 'site_permit_application.pdf',
    demoDuration: 3000,
  },
  {
    id: 'd',
    label: 'Agent D',
    role: 'Alerts & Reminders',
    color: '#2563eb',
    bgSoft: 'rgba(37,99,235,0.10)',
    demoLogs: [
      'Reading compliance results from Agent C...',
      'Score below threshold - composing alert...',
      'Preparing Telegram notification for project manager...',
      '[!] Alert: Structural PE Endorsement missing',
      '[!] Alert: BOMBA clearance pending',
      'Sending notification to project manager...',
      '[OK] Alerts dispatched successfully',
    ],
    demoFile: 'alerts_output.json',
    demoDuration: 1200,
  },
  {
    id: 'e',
    label: 'Agent E',
    role: 'Report Generator',
    color: '#7c3aed',
    bgSoft: 'rgba(124,58,237,0.10)',
    demoLogs: [
      'Receiving outputs from Agents A, B, C, D',
      'Compiling project summary',
      'Generating cost variance table',
      'Building delay analysis section',
      'Embedding compliance checklist',
      'Rendering PDF layout - 24 pages',
      'Generating XLSX cost tracker - 180 rows',
      'Uploading to report storage...',
      '[OK] Report generation complete',
    ],
    demoFile: 'report_output.pdf',
    demoDuration: 2000,
  },
];

/* ─── Status badge ─── */
function StatusBadge({ status }) {
  const configs = {
    idle:    { label: 'Idle',    bg: '#f0ede7', text: '#6b6860' },
    running: { label: 'Running', bg: 'rgba(217,119,6,0.12)', text: '#b45309' },
    done:    { label: 'Done',    bg: 'rgba(22,163,74,0.12)',  text: '#15803d' },
    error:   { label: 'Error',   bg: 'rgba(220,38,38,0.12)', text: '#b91c1c' },
  };
  const cfg = configs[status] ?? configs.idle;

  return (
    <span
      className="badge text-[10px]"
      style={{ background: cfg.bg, color: cfg.text }}
    >
      {status === 'running' && (
        <span
          className="agent-pulse-dot inline-block w-1.5 h-1.5 rounded-full"
          style={{ background: cfg.text }}
        />
      )}
      {status === 'done' && <CheckCircle2 className="w-2.5 h-2.5" />}
      {status === 'error' && <XCircle className="w-2.5 h-2.5" />}
      {cfg.label}
    </span>
  );
}

/* ─── Single agent row ─── */
function AgentRow({ agent, state, onToggle, expanded }) {
  const logEndRef = useRef(null);

  useEffect(() => {
    if (expanded && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [state.logs, expanded]);

  const elapsedSecs = state.startedAt
    ? ((state.endedAt ?? Date.now()) - state.startedAt) / 1000
    : null;

  return (
    <div
      className="animate-slide-up"
      style={{ borderLeft: `3px solid ${agent.color}`, background: 'white', borderRadius: 10, overflow: 'hidden', border: `1px solid #e4e2dc`, borderLeftColor: agent.color, borderLeftWidth: 3 }}
    >
      {/* Header row */}
      <button
        onClick={onToggle}
        aria-label={`${expanded ? 'Collapse' : 'Expand'} ${agent.label} logs`}
        className="w-full flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-[#fafaf8] transition-colors duration-150"
      >
        {/* Color dot */}
        <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: agent.color }} />

        {/* Label */}
        <div className="flex-1 text-left min-w-0">
          <span className="font-semibold text-sm text-[#1c1b18]">{agent.label}</span>
          <span className="text-[#6b6860] text-sm ml-1.5">— {agent.role}</span>
        </div>

        {/* Status + time */}
        <div className="flex items-center gap-2.5 flex-shrink-0">
          {state.currentFile && state.status === 'running' && (
            <span className="hidden sm:flex items-center gap-1 text-[11px] text-[#6b6860] bg-[#f0ede7] px-2 py-0.5 rounded">
              <FileText className="w-3 h-3" />
              {state.currentFile}
            </span>
          )}
          {elapsedSecs !== null && (
            <span className="flex items-center gap-1 text-[11px] text-[#6b6860]">
              <Clock className="w-3 h-3" />
              {elapsedSecs.toFixed(1)}s
            </span>
          )}
          <StatusBadge status={state.status} />
          {expanded ? (
            <ChevronDown className="w-4 h-4 text-[#9b9794]" />
          ) : (
            <ChevronRight className="w-4 h-4 text-[#9b9794]" />
          )}
        </div>
      </button>

      {/* Log area */}
      {expanded && (
        <div
          className="border-t border-[#e4e2dc] bg-[#0f0f10] rounded-b-[10px]"
          style={{ maxHeight: 240, overflowY: 'auto' }}
        >
          <div className="p-4 space-y-1">
            {state.logs.length === 0 ? (
              <p className="text-[#9b9794] font-mono text-xs">Waiting to start…</p>
            ) : (
              state.logs.map((line, i) => (
                <p
                  key={i}
                  className="log-line-enter text-[12px] font-mono leading-relaxed"
                  style={{
                    color: (line.startsWith('[OK]') || line.startsWith('✓')) ? '#4ade80' 
                         : (line.includes('[!]') || line.includes('⚠')) ? '#fbbf24' 
                         : '#e5e3de',
                    animationDelay: `${i * 0.02}s`,
                  }}
                >
                  <span className="text-[#555] mr-2 select-none">›</span>
                  {line}
                </p>
              ))
            )}
            {state.status === 'running' && (
              <p className="flex items-center gap-1.5 text-[12px] font-mono text-[#9b9794]">
                <Loader2 className="w-3 h-3 animate-spin" />
                Processing…
              </p>
            )}
            <div ref={logEndRef} />
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Sources strip ─── */
function SourcesStrip({ files }) {
  if (!files.length) return null;
  return (
    <div className="flex items-center gap-2 flex-wrap pt-2 border-t border-[#e4e2dc]">
      <span className="text-[11px] font-semibold text-[#6b6860] uppercase tracking-wide">Sources</span>
      {files.map((f, i) => (
        <span
          key={i}
          className="flex items-center gap-1 text-[11px] text-[#1c1b18] bg-[#f0ede7] px-2 py-0.5 rounded border border-[#e4e2dc]"
        >
          <FileText className="w-3 h-3 text-[#6b6860]" />
          {f}
        </span>
      ))}
    </div>
  );
}

/* ─── Initial agent state factory ─── */
const initState = () => ({
  status: 'idle',
  logs: [],
  currentFile: null,
  startedAt: null,
  endedAt: null,
});

/* ─── AgentPanel ─── */
export default function AgentPanel({ jobId, demoMode = false, autoStart = false }) {
  const [agentStates, setAgentStates] = useState(() =>
    Object.fromEntries(AGENTS.map((a) => [a.id, initState()]))
  );
  const [expanded, setExpanded] = useState({ a: true, b: false, c: false, d: false, e: false });
  const [started, setStarted] = useState(false);
  const timersRef = useRef([]);

  /* ─ Demo simulation ─ */
  const runDemo = useCallback(() => {
    if (started) return;
    setStarted(true);

    // Reset
    setAgentStates(Object.fromEntries(AGENTS.map((a) => [a.id, initState()])));

    let globalDelay = 0;

    AGENTS.forEach((agent, agentIdx) => {
      const startDelay = globalDelay + agentIdx * 400;
      globalDelay += 200;

      // Start agent
      const t1 = setTimeout(() => {
        setAgentStates((prev) => ({
          ...prev,
          [agent.id]: {
            ...prev[agent.id],
            status: 'running',
            currentFile: agent.demoFile,
            startedAt: Date.now(),
          },
        }));
        setExpanded((prev) => ({ ...prev, [agent.id]: true }));
      }, startDelay);
      timersRef.current.push(t1);

      // Stream log lines
      agent.demoLogs.forEach((line, lineIdx) => {
        const lineDelay = startDelay + 300 + lineIdx * 260;
        const t = setTimeout(() => {
          setAgentStates((prev) => ({
            ...prev,
            [agent.id]: {
              ...prev[agent.id],
              logs: [...prev[agent.id].logs, line],
            },
          }));
        }, lineDelay);
        timersRef.current.push(t);
      });

      // Mark done
      const doneDelay = startDelay + 300 + agent.demoLogs.length * 260 + 400;
      const t2 = setTimeout(() => {
        setAgentStates((prev) => ({
          ...prev,
          [agent.id]: {
            ...prev[agent.id],
            status: 'done',
            currentFile: null,
            endedAt: Date.now(),
          },
        }));
      }, doneDelay);
      timersRef.current.push(t2);
    });
  }, [started]);

  /* ─ Real SSE ─ */
  useEffect(() => {
    if (demoMode || !jobId) return;

    const es = new EventSource(getAgentStreamUrl(jobId));
    es.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        const { agent_id, event, log, file } = msg;
        if (!agent_id) return;
        setAgentStates((prev) => {
          const cur = prev[agent_id] ?? initState();
          if (event === 'start')  return { ...prev, [agent_id]: { ...cur, status: 'running', currentFile: file ?? cur.currentFile, startedAt: cur.startedAt ?? Date.now() }};
          if (event === 'log')    return { ...prev, [agent_id]: { ...cur, logs: [...cur.logs, log ?? ''] }};
          if (event === 'done')   return { ...prev, [agent_id]: { ...cur, status: 'done', endedAt: Date.now() }};
          if (event === 'error')  return { ...prev, [agent_id]: { ...cur, status: 'error', endedAt: Date.now() }};
          return prev;
        });
      } catch {}
    };
    es.onerror = () => es.close();

    return () => es.close();
  }, [jobId, demoMode]);

  /* ─ Auto-start in demo mode ─ */
  useEffect(() => {
    if (demoMode && autoStart) runDemo();
    return () => timersRef.current.forEach(clearTimeout);
  }, [demoMode, autoStart, runDemo]);

  const toggleExpanded = (id) =>
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));

  const referencedFiles = [...new Set(AGENTS.map((a) => a.demoFile))];

  const allDone = AGENTS.every((a) => agentStates[a.id]?.status === 'done');
  const anyRunning = AGENTS.some((a) => agentStates[a.id]?.status === 'running');

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-[#1c1b18] text-base">Agent Pipeline</h3>
          <p className="text-xs text-[#6b6860] mt-0.5">
            {anyRunning ? 'Processing document…' : allDone ? 'All agents complete' : 'Waiting for document'}
          </p>
        </div>
        {demoMode && !started && (
          <button onClick={runDemo} className="btn btn-primary text-sm">
            <Zap className="w-4 h-4" />
            Run Pipeline
          </button>
        )}
        {demoMode && started && !allDone && (
          <div className="flex items-center gap-1.5 text-sm text-[#d97706]">
            <Loader2 className="w-4 h-4 animate-spin" />
            Running…
          </div>
        )}
        {allDone && (
          <span className="flex items-center gap-1.5 text-sm text-[#16a34a] font-medium">
            <CheckCircle2 className="w-4 h-4" />
            Complete
          </span>
        )}
      </div>

      {/* Agent rows */}
      <div className="space-y-2">
        {AGENTS.map((agent) => (
          <AgentRow
            key={agent.id}
            agent={agent}
            state={agentStates[agent.id]}
            expanded={expanded[agent.id]}
            onToggle={() => toggleExpanded(agent.id)}
          />
        ))}
      </div>

      {/* Sources strip */}
      {allDone && <SourcesStrip files={referencedFiles} />}
    </div>
  );
}

