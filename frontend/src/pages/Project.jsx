import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Activity, ChevronRight, AlertTriangle, Info, BellRing } from 'lucide-react';
import AgentPanel from '../components/AgentPanel.jsx';
import ComplianceScore from '../components/ComplianceScore.jsx';
import ReportDownload from '../components/ReportDownload.jsx';
import MilestoneForm from '../components/MilestoneForm.jsx';
import NotificationsPanel from '../components/NotificationsPanel.jsx';
import MonitoringPanel from '../components/MonitoringPanel.jsx';
import HealthScoreCard from '../components/HealthScoreCard.jsx';
import { getProject, getProjectAlerts, uploadDocuments } from '../api/client.js';
import SourcesPanel from '../components/SourcesPanel.jsx';
import ChatPanel from '../components/ChatPanel.jsx';
import UploadModal from '../components/UploadModal.jsx';

const TABS = ['Overview', 'Alerts', 'Agents', 'Compliance', 'Reports'];

function SkeletonProject() {
  return (
    <div className="flex w-full h-full p-6 animate-fade-in">
      <div className="w-64 space-y-3">
        {Array.from({ length: 5 }).map((_, i) => <div key={i} className="skeleton h-10 rounded-lg" />)}
      </div>
      <div className="flex-1 space-y-4 px-6">
        <div className="skeleton h-10 w-80 rounded" />
        <div className="skeleton h-64 rounded-lg" />
      </div>
    </div>
  );
}

function BigHealthRing({ score }) {
  const color = score >= 80 ? '#16a34a' : score >= 60 ? '#d97706' : '#dc2626';
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative w-[120px] h-[120px] flex items-center justify-center flex-shrink-0">
      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={radius} stroke="#e4e2dc" strokeWidth="8" fill="transparent" />
        <circle
          cx="60"
          cy="60"
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
      <div className="absolute flex flex-col items-center justify-center mt-1">
        <span className="text-3xl font-bold font-outfit" style={{ color }}>{score}</span>
        <span className="text-[10px] text-[#9b9794] font-medium uppercase tracking-wider">Score</span>
      </div>
    </div>
  );
}

function OverviewTab({ project, alerts }) {
  const f = project;
  const hasDetails = f.contractor || f.location || f.contract_value || f.cidb_grade || f.scope;

  return (
    <div className="space-y-6 animate-slide-up pb-8">
      <div className="card p-6">
        <h3 className="font-semibold text-lg text-[#1c1b18] mb-4 font-outfit">Project Overview</h3>
        {hasDetails ? (
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3 text-sm">
            {[
              ['Contractor', f.contractor],
              ['Client', f.client],
              ['Location', f.location],
              ['CIDB Grade', f.cidb_grade],
              ['Contract Value', f.contract_value ? `RM ${Number(f.contract_value).toLocaleString()}` : null],
              ['Scope', f.scope],
              ['Start Date', f.start_date],
              ['End Date', f.end_date],
              ['Project Type', f.project_type],
              ['Extraction', f._extraction_method],
            ].filter(([, v]) => v && v !== 'Unknown Contractor' && v !== 'Unnamed Project').map(([label, value]) => (
              <div key={label} className="flex flex-col">
                <dt className="text-[10px] font-bold uppercase tracking-wider text-[#9b9794]">{label}</dt>
                <dd className="text-[#1c1b18] font-medium mt-0.5 truncate">{value}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="text-[#6b6860] leading-relaxed">
            {f.description || 'Run the AI pipeline to extract project details from uploaded documents.'}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card p-6 flex flex-col items-center justify-center text-center">
          <h3 className="font-semibold text-sm text-[#1c1b18] w-full text-left mb-6 uppercase tracking-wider">Health</h3>
          <BigHealthRing score={project.health_score ?? 0} />
          <p className="text-sm text-[#6b6860] mt-6 max-w-[200px]">
            Based on schedule compliance, cost variance, and CIDB score.
          </p>
        </div>

        <div className="card p-6">
          <h3 className="font-semibold text-sm text-[#1c1b18] mb-6 uppercase tracking-wider">Alerts</h3>
          <div className="space-y-3">
            {alerts && alerts.length > 0 ? (
              alerts.map(a => (
                <div key={a.id} className="flex items-start gap-3 p-3 rounded-xl border border-[#e4e2dc] bg-[#fafaf8]">
                  {a.type === 'urgent' && <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />}
                  {a.type === 'warning' && <BellRing className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />}
                  {a.type === 'info' && <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />}
                  <p className="text-sm text-[#1c1b18] font-medium leading-snug">{a.text}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-[#6b6860] text-center py-4">No alerts at this time</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Project() {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('Overview');

  // Panels collapse state
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);

  // Sources & Chat Context State — loaded from sessionStorage after upload
  const [sources, setSources] = useState(() => {
    try {
      const stored = sessionStorage.getItem(`sources_${id}`);
      return stored ? JSON.parse(stored) : [];
    } catch { return []; }
  });
  const [selectedSources, setSelectedSources] = useState(() => {
    try {
      const stored = sessionStorage.getItem(`sources_${id}`);
      const parsed = stored ? JSON.parse(stored) : [];
      return parsed.map(s => s.id);
    } catch { return []; }
  });

  // Job ID for SSE pipeline streaming
  const [jobId] = useState(() => sessionStorage.getItem(`job_${id}`) || null);

  // Upload Modal State
  const [uploadModalOpen, setUploadModalOpen] = useState(false);

  useEffect(() => {
    setLoading(true);

    // Fetch project and alerts in parallel
    Promise.all([
      getProject(id),
      getProjectAlerts(id).catch(() => ({ alerts: [] })) // Fallback to empty alerts on error
    ])
      .then(([projectData, alertsData]) => {
        setProject(projectData);
        setAlerts(alertsData.alerts || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [id]);

  // Auto-refresh project data while a pipeline job is running (every 10s)
  useEffect(() => {
    if (!jobId) return; // No job = no need to poll

    const poll = setInterval(async () => {
      try {
        const [projectData, alertsData] = await Promise.all([
          getProject(id),
          getProjectAlerts(id).catch(() => ({ alerts: [] })),
        ]);
        setProject(projectData);
        setAlerts(alertsData.alerts || []);
        // Stop polling once backend marks project as processed/error
        if (projectData.status === 'processed' || projectData.status === 'error') {
          clearInterval(poll);
        }
      } catch (e) {
        console.warn('[Buildora] Poll failed:', e.message);
      }
    }, 10_000); // every 10s

    return () => clearInterval(poll);
  }, [id, jobId]);

  const handleUploadContinue = async (newFiles) => {
    const newSources = newFiles.map((f, i) => ({
      id: `new-${Date.now()}-${i}`,
      name: f.name,
      type: (f.type || '').startsWith('image') ? 'image' : 'document'
    }));
    setSources(prev => {
      const merged = [...prev, ...newSources];
      sessionStorage.setItem(`sources_${id}`, JSON.stringify(merged));
      return merged;
    });
    setSelectedSources(prev => [...prev, ...newSources.map(s => s.id)]);
    setUploadModalOpen(false);
    // Fire upload to backend for added documents (non-blocking)
    try {
      await uploadDocuments(newFiles, id);
    } catch (e) {
      console.warn('[Buildora] Background upload failed:', e.message);
    }
  };

  if (loading) return <SkeletonProject />;
  if (!project) return <div className="p-8 text-center text-red-500">Project not found</div>;

  const score = project?.health_score ?? 0;
  const statusColor = score >= 80 ? '#16a34a' : score >= 60 ? '#d97706' : '#dc2626';
  const statusText = project?.status || 'active';

  return (
    <div className="flex w-full h-full overflow-hidden bg-[#f7f6f3]">
      
      {/* LEFT PANEL */}
      <SourcesPanel 
        collapsed={leftCollapsed}
        onToggleCollapse={() => setLeftCollapsed(!leftCollapsed)}
        sources={sources}
        setSources={setSources}
        selectedSources={selectedSources}
        setSelectedSources={setSelectedSources}
        onOpenUpload={() => setUploadModalOpen(true)}
      />

      {/* CENTER PANEL */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          
          {/* Breadcrumb Header */}
          <div className="px-10 py-6 border-b border-[#e4e2dc] bg-white sticky top-0 z-10">
            <nav className="flex items-center gap-1.5 text-sm mb-4">
              <Link to="/" className="text-[#6b6860] hover:text-[#1c1b18] font-medium transition-colors">Buildora</Link>
              <ChevronRight className="w-3.5 h-3.5 text-[#b5b2ab]" />
              <Link to="/" className="text-[#6b6860] hover:text-[#1c1b18] font-medium transition-colors">Projects</Link>
              <ChevronRight className="w-3.5 h-3.5 text-[#b5b2ab]" />
              <span className="text-[#1c1b18] font-semibold">{project.name}</span>
            </nav>

            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-bold text-[#1c1b18] leading-tight font-outfit">{project.name}</h1>
              <span 
                className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase border"
                style={{ backgroundColor: statusColor + '10', color: statusColor, borderColor: statusColor + '30' }}
              >
                <Activity className="w-3 h-3 inline-block mr-1 mb-0.5" />
                {statusText === 'active' ? 'Active' : statusText.replace('-', ' ')}
              </span>
            </div>
            <p className="text-[#6b6860]">{project.contractor || 'Contractor not specified'}</p>
            
            {/* Tabs */}
            <div className="flex gap-6 mt-6 border-b border-[#e4e2dc] -mb-6">
              {TABS.map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`pb-3 text-sm font-semibold transition-colors relative ${
                    activeTab === tab ? 'text-[#f97316]' : 'text-[#9b9794] hover:text-[#1c1b18]'
                  }`}
                >
                  {tab}
                  {activeTab === tab && (
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#f97316] rounded-t-full" />
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Center Content */}
          <div className="p-10 max-w-4xl mx-auto w-full">
            {activeTab === 'Overview' && <OverviewTab project={project} alerts={alerts} />}
            {activeTab === 'Alerts' && (
              <div className="space-y-6 pb-8 animate-slide-up">
                <NotificationsPanel projectId={id} />
              </div>
            )}
            {activeTab === 'Agents' && (
              <div className="space-y-6 pb-8 animate-slide-up">
                <AgentPanel jobId={jobId} demoMode={!jobId} autoStart={!jobId} />

                {/* Health Score Card */}
                <HealthScoreCard projectId={id} />

                {/* Monitoring Panel (Agent B) */}
                <MonitoringPanel projectId={id} />

                <div className="card p-6">
                  <h3 className="font-semibold text-lg text-[#1c1b18] mb-4 font-outfit">Submit Milestone Update</h3>
                  <MilestoneForm projectId={id} />
                </div>
              </div>
            )}
            {activeTab === 'Compliance' && <ComplianceScore projectId={id} />}
            {activeTab === 'Reports' && <ReportDownload projectId={id} />}
          </div>
        </div>
      </div>

      {/* RIGHT PANEL */}
      <ChatPanel 
        collapsed={rightCollapsed}
        onToggleCollapse={() => setRightCollapsed(!rightCollapsed)}
        selectedSources={selectedSources}
        onRemoveSelectedSource={(id) => setSelectedSources(prev => prev.filter(s => s !== id))}
        sources={sources}
      />

      {/* Upload Modal */}
      <UploadModal 
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onContinue={handleUploadContinue}
        projectName={project.name}
      />
    </div>
  );
}
