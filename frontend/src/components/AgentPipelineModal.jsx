/**
 * AgentPipelineModal.jsx
 * A beautiful animated flow popup showing the 5 AI agents processing documents.
 * Triggered after upload (new project or adding files).
 * Auto-closes when all agents complete.
 */
import { useState, useEffect, useRef } from 'react';
import { CheckCircle2, Loader2, FileText, ChevronRight, Zap, Search, Calendar, Shield, Bell, BarChart } from 'lucide-react';

const AGENTS = [
  { id: 'a', label: 'Agent A', role: 'Document Reader',    color: '#f97316', icon: <Search className="w-6 h-6 text-white/90" /> },
  { id: 'b', label: 'Agent B', role: 'Schedule Monitor',   color: '#e11d48', icon: <Calendar className="w-6 h-6 text-white/90" /> },
  { id: 'c', label: 'Agent C', role: 'CIDB Compliance',    color: '#d97706', icon: <Shield className="w-6 h-6 text-white/90" /> },
  { id: 'd', label: 'Agent D', role: 'Alerts & Reminders', color: '#2563eb', icon: <Bell className="w-6 h-6 text-white/90" /> },
  { id: 'e', label: 'Agent E', role: 'Report Generator',   color: '#7c3aed', icon: <BarChart className="w-6 h-6 text-white/90" /> },
];

const DEMO_LOGS = {
  a: ['Initialising document parser…', 'Reading uploaded files…', 'Extracting text layers…', 'Parsing contract clauses…', 'Detecting milestone entries…', 'Entity extraction complete ✓'],
  b: ['Received payload from Agent A', 'Loading project schedule data…', 'Computing critical path…', 'Checking milestone compliance…', 'Cost variance analysis complete ✓'],
  c: ['Loading CIDB permit requirements…', 'Validating contractor grade…', 'Checking OSHC insurance…', 'Reviewing PAM contract clauses…', 'CIDB compliance check complete ✓'],
  d: ['Reading compliance results…', 'Composing project alerts…', 'Preparing notifications…', 'Alert dispatch complete ✓'],
  e: ['Receiving outputs from all agents…', 'Compiling project summary…', 'Generating cost variance table…', 'Building compliance checklist…', 'Report generation complete ✓'],
};

const DEMO_DURATIONS = { a: 2200, b: 1800, c: 2600, d: 1400, e: 2000 };

function AgentNode({ agent, status, logs, isExpanded, onClick }) {
  const color = agent.color;
  const isRunning = status === 'running';
  const isDone = status === 'done';
  const isIdle = status === 'idle';

  return (
    <div
      className="flex flex-col items-center cursor-pointer select-none"
      onClick={onClick}
      style={{ minWidth: 100 }}
    >
      {/* Circle node */}
      <div
        className="relative w-16 h-16 rounded-full flex items-center justify-center text-2xl transition-all duration-500"
        style={{
          background: isIdle ? '#1a1a1b' : `${color}22`,
          border: `2.5px solid ${isIdle ? '#333' : color}`,
          boxShadow: isRunning ? `0 0 20px ${color}55, 0 0 40px ${color}22` : 'none',
          transform: isRunning ? 'scale(1.12)' : 'scale(1)',
        }}
      >
        <span>{agent.icon}</span>
        {isRunning && (
          <span
            className="absolute inset-0 rounded-full animate-ping opacity-30"
            style={{ background: color }}
          />
        )}
        {isDone && (
          <CheckCircle2
            className="absolute -bottom-1 -right-1 w-5 h-5"
            style={{ color: '#16a34a', background: '#111', borderRadius: '50%' }}
          />
        )}
      </div>

      {/* Label */}
      <p className="text-white font-semibold text-[11px] mt-2 tracking-tight">{agent.label}</p>
      <p className="text-[10px] mt-0.5" style={{ color: isIdle ? '#555' : color }}>
        {agent.role}
      </p>

      {/* Status */}
      {isRunning && (
        <div className="flex items-center gap-1 mt-1">
          <Loader2 className="w-3 h-3 animate-spin" style={{ color }} />
          <span className="text-[10px]" style={{ color }}>Running</span>
        </div>
      )}
      {isDone && (
        <span className="text-[10px] text-green-400 mt-1 font-semibold">Done</span>
      )}
    </div>
  );
}

function Connector({ active, done, color }) {
  return (
    <div className="flex items-center justify-center w-10 flex-shrink-0 mt-[-28px]">
      <div
        className="h-0.5 w-full transition-all duration-700"
        style={{
          background: done || active
            ? `linear-gradient(90deg, ${color}80, ${color})`
            : '#333',
          boxShadow: active ? `0 0 6px ${color}` : 'none',
        }}
      />
    </div>
  );
}

export default function AgentPipelineModal({ isOpen, onComplete, jobId }) {
  const [agentStatus, setAgentStatus] = useState(() =>
    Object.fromEntries(AGENTS.map(a => [a.id, 'idle']))
  );
  const [currentLogs, setCurrentLogs] = useState({});
  const [allDone, setAllDone] = useState(false);
  const [completionShown, setCompletionShown] = useState(false);
  const timersRef = useRef([]);

  useEffect(() => {
    if (!isOpen) return;

    // Reset
    setAgentStatus(Object.fromEntries(AGENTS.map(a => [a.id, 'idle'])));
    setCurrentLogs({});
    setAllDone(false);
    setCompletionShown(false);
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];

    if (jobId) {
      // Real SSE mode
      const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
      const es = new EventSource(`${BASE}/api/agent-stream/${jobId}`);
      es.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          const { agent_id, event, log } = msg;
          if (!agent_id) {
            if (msg.event === 'pipeline_complete') {
              finishUp();
              es.close();
            }
            return;
          }
          setAgentStatus(prev => {
            const next = { ...prev };
            if (event === 'start') next[agent_id] = 'running';
            if (event === 'done' || event === 'error') next[agent_id] = 'done';
            return next;
          });
          if (event === 'log') {
            setCurrentLogs(prev => ({
              ...prev,
              [agent_id]: [...(prev[agent_id] || []), log],
            }));
          }
        } catch {}
      };
      es.onerror = () => { es.close(); finishUp(); };
      return () => es.close();
    } else {
      // Demo simulation
      runDemo();
    }

    return () => timersRef.current.forEach(clearTimeout);
  }, [isOpen, jobId]);

  const runDemo = () => {
    let globalDelay = 0;
    AGENTS.forEach((agent, idx) => {
      const startDelay = globalDelay + idx * 500;
      globalDelay += 250;

      const t1 = setTimeout(() => {
        setAgentStatus(prev => ({ ...prev, [agent.id]: 'running' }));
      }, startDelay);
      timersRef.current.push(t1);

      const logs = DEMO_LOGS[agent.id];
      logs.forEach((line, li) => {
        const lt = setTimeout(() => {
          setCurrentLogs(prev => ({
            ...prev,
            [agent.id]: [...(prev[agent.id] || []), line],
          }));
        }, startDelay + 300 + li * 280);
        timersRef.current.push(lt);
      });

      const doneDelay = startDelay + 300 + logs.length * 280 + 400;
      const t2 = setTimeout(() => {
        setAgentStatus(prev => ({ ...prev, [agent.id]: 'done' }));
      }, doneDelay);
      timersRef.current.push(t2);
    });

    // Compute total done time
    let totalDoneDelay = 0;
    AGENTS.forEach((agent, idx) => {
      const start = idx * 500 + idx * 250;
      const d = start + 300 + DEMO_LOGS[agent.id].length * 280 + 400;
      if (d > totalDoneDelay) totalDoneDelay = d;
    });

    const tf = setTimeout(() => finishUp(), totalDoneDelay + 600);
    timersRef.current.push(tf);
  };

  const finishUp = () => {
    setAllDone(true);
    setCompletionShown(true);
    const tc = setTimeout(() => {
      onComplete?.();
    }, 1800);
    timersRef.current.push(tc);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-sm animate-fade-in p-4">
      <div
        className="w-full max-w-3xl rounded-2xl overflow-hidden animate-slide-up"
        style={{ background: '#111113', border: '1px solid #2a2a2c' }}
      >
        {/* Header */}
        <div className="px-8 py-6 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#f97316]/15 flex items-center justify-center">
              <Zap className="w-5 h-5 text-[#f97316]" />
            </div>
            <div>
              <h2 className="text-white font-bold text-lg tracking-tight font-outfit">
                AI Agent Pipeline
              </h2>
              <p className="text-[#555] text-xs mt-0.5">
                {allDone ? 'Analysis complete — loading your dashboard…' : 'Analysing your project documents…'}
              </p>
            </div>
            {allDone && (
              <div className="ml-auto flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-green-400" />
                <span className="text-green-400 text-sm font-semibold">Complete</span>
              </div>
            )}
          </div>
        </div>

        {/* Flow Diagram */}
        <div className="px-8 py-8">
          {/* Documents source */}
          <div className="flex items-center justify-center gap-0 mb-8">
            <div className="flex flex-col items-center mr-6">
              <div className="w-14 h-14 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-2xl">
                <FileText className="w-7 h-7 text-white/40" />
              </div>
              <p className="text-[10px] text-white/30 mt-2">Documents</p>
            </div>

            <ChevronRight className="w-4 h-4 text-white/20 mr-3 mt-[-20px]" />

            {/* Agent nodes */}
            <div className="flex items-start gap-0">
              {AGENTS.map((agent, idx) => (
                <div key={agent.id} className="flex items-start">
                  <AgentNode
                    agent={agent}
                    status={agentStatus[agent.id]}
                    logs={currentLogs[agent.id] || []}
                  />
                  {idx < AGENTS.length - 1 && (
                    <Connector
                      active={agentStatus[AGENTS[idx + 1].id] === 'running'}
                      done={agentStatus[AGENTS[idx + 1].id] === 'done'}
                      color={AGENTS[idx + 1].color}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Live log feed */}
          <div
            className="rounded-xl p-4 font-mono text-[11px] overflow-y-auto"
            style={{ background: '#0a0a0b', border: '1px solid #1f1f21', maxHeight: 140 }}
          >
            {AGENTS.flatMap(agent =>
              (currentLogs[agent.id] || []).map((line, li) => (
                <div key={`${agent.id}-${li}`} className="flex items-center gap-2 py-0.5">
                  <span style={{ color: agent.color }} className="font-bold flex-shrink-0 w-16">
                    {agent.label}
                  </span>
                  <span style={{ color: line.includes('✓') || line.includes('[OK]') ? '#4ade80' : '#9b9794' }}>
                    › {line}
                  </span>
                </div>
              ))
            ).slice(-12)}
            {!allDone && (
              <div className="flex items-center gap-2 py-0.5 text-white/25">
                <Loader2 className="w-3 h-3 animate-spin" />
                <span>Processing…</span>
              </div>
            )}
          </div>
        </div>

        {/* Footer progress bar */}
        <div className="h-1 bg-white/5">
          <div
            className="h-full bg-gradient-to-r from-[#f97316] to-[#7c3aed] transition-all duration-500"
            style={{
              width: `${(AGENTS.filter(a => agentStatus[a.id] === 'done').length / AGENTS.length) * 100}%`,
            }}
          />
        </div>
      </div>
    </div>
  );
}
