import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { AlertTriangle, Info, BellRing } from 'lucide-react';
import ComplianceScore from '../components/ComplianceScore.jsx';
import ReportDownload from '../components/ReportDownload.jsx';
import NotificationsPanel from '../components/NotificationsPanel.jsx';
// import MonitoringPanel from '../components/MonitoringPanel.jsx'; // HIDDEN - not needed for now
import { getProject, getProjectAlerts, uploadDocuments } from '../api/client.js';
import SourcesPanel from '../components/SourcesPanel.jsx';
import ChatPanel from '../components/ChatPanel.jsx';
import UploadModal from '../components/UploadModal.jsx';
import AgentPipelineModal from '../components/AgentPipelineModal.jsx';

const TABS = ['Overview', 'Alerts', 'Compliance', 'Reports'];

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
          cx="60" cy="60" r={radius}
          stroke={color} strokeWidth="8" fill="transparent"
          strokeDasharray={circumference} strokeDashoffset={offset}
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

  const standardFields = [
    { label: 'Contractor',         value: f.contractor || 'N/A' },
    { label: 'CIDB Registration',  value: f.cidb_registration || 'N/A' },
    { label: 'Location',           value: f.location || 'N/A' },
    { label: 'Start Date',         value: f.start_date || 'N/A' },
    { label: 'End Date',           value: f.end_date || 'N/A' },
    { label: 'Client',             value: f.client || 'N/A' },
    { label: 'CIDB Grade',         value: f.cidb_grade || 'N/A' },
    { label: 'Contract Value',     value: f.contract_value ? `RM ${Number(f.contract_value).toLocaleString()}` : (f.contract_value || 'N/A') },
    { label: 'Scope',              value: f.scope || 'N/A' },
    { label: 'Project Type',       value: f.project_type || 'N/A' },
  ];

  const cleanedFields = standardFields.map(field => ({
    ...field,
    value: (field.value === 'Unknown Contractor' || field.value === 'Unnamed Project') ? 'N/A' : field.value,
  }));

  return (
    <div className="space-y-6 animate-slide-up pb-8">
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-lg text-[#1c1b18] font-outfit">Project Overview</h3>
        </div>

        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4 text-sm">
          {cleanedFields.map(({ label, value }) => (
            <div key={label} className="flex flex-col">
              <dt className="text-[10px] font-bold uppercase tracking-wider text-[#9b9794]">{label}</dt>
              <dd className={`text-[#1c1b18] font-medium mt-1 ${value === 'N/A' ? 'text-[#9b9794] italic' : ''}`}>
                {value}
              </dd>
            </div>
          ))}
        </dl>

        {f.status === 'pending' && (
          <div className="mt-6 p-4 rounded-lg bg-blue-50 border border-blue-100">
            <p className="text-sm text-blue-700">
              📄 Upload documents and run the AI pipeline to extract project details automatically.
            </p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6">
        <div className="card p-6 flex flex-col items-center justify-center text-center">
          <h3 className="font-semibold text-sm text-[#1c1b18] w-full text-left mb-6 uppercase tracking-wider">Health Score Breakdown</h3>
          <div className="flex flex-col md:flex-row items-center justify-center gap-12 w-full">
            <BigHealthRing score={project.health_score ?? 0} />
            <div className="text-left space-y-3 max-w-sm">
              <p className="text-sm text-[#6b6860]">
                This score represents the overall health of your project, calculated dynamically based on real-time data:
              </p>
              <ul className="text-sm text-[#1c1b18] space-y-2 list-none pl-0">
                <li className="flex items-center justify-between gap-4">
                  <span className="font-semibold text-[#6b6860]">Schedule Compliance (40%)</span>
                  <span className="font-bold text-[#1c1b18]">{project.health_breakdown?.schedule ?? 0}%</span>
                </li>
                <li className="flex items-center justify-between gap-4">
                  <span className="font-semibold text-[#6b6860]">Cost Variance (35%)</span>
                  <span className="font-bold text-[#1c1b18]">{project.health_breakdown?.cost ?? 0}%</span>
                </li>
                <li className="flex items-center justify-between gap-4">
                  <span className="font-semibold text-[#6b6860]">CIDB Score (25%)</span>
                  <span className="font-bold text-[#1c1b18]">{project.health_breakdown?.compliance ?? 0}%</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Project() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [project, setProject] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('Overview');

  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);

  // Sources — merged from sessionStorage AND backend
  const [sources, setSources] = useState([]);
  const [selectedSources, setSelectedSources] = useState([]);

  // Job ID for SSE
  const [jobId] = useState(() => sessionStorage.getItem(`job_${id}`) || null);

  // Upload modal
  const [uploadModalOpen, setUploadModalOpen] = useState(false);

  // Agent pipeline modal — shown after upload
  const [pipelineOpen, setPipelineOpen] = useState(false);
  const [pipelineJobId, setPipelineJobId] = useState(null);

  // Load project + alerts + documents
  useEffect(() => {
    setLoading(true);

    Promise.all([
      getProject(id),
      getProjectAlerts(id).catch(() => ({ alerts: [] })),
      fetch(`/api/projects/${id}/documents`).then(r => r.json()).catch(() => ({ documents: [] })),
    ]).then(([projectData, alertsData, docsData]) => {
      setProject(projectData);
      setAlerts(alertsData.alerts || []);

      // Merge backend documents with sessionStorage sources
      const backendDocs = (docsData.documents || []).map(d => ({
        id: d.id || d.name,
        name: d.name,
        type: d.type || 'document',
      }));

      try {
        const stored = sessionStorage.getItem(`sources_${id}`);
        const sessionDocs = stored ? JSON.parse(stored) : [];
        // Deduplicate by name
        const allNames = new Set(backendDocs.map(d => d.name));
        const extras = sessionDocs.filter(s => !allNames.has(s.name));
        const merged = [...backendDocs, ...extras];
        setSources(merged);
        setSelectedSources(merged.map(s => s.id));
      } catch {
        setSources(backendDocs);
        setSelectedSources(backendDocs.map(d => d.id));
      }

      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, [id]);

  // Show pipeline modal automatically if there's a pending job (new project)
  useEffect(() => {
    if (jobId && !loading) {
      setPipelineJobId(jobId);
      setPipelineOpen(true);
    }
  }, [jobId, loading]);

  // Poll while pipeline running
  useEffect(() => {
    if (!jobId) return;
    const poll = setInterval(async () => {
      try {
        const [projectData, alertsData] = await Promise.all([
          getProject(id),
          getProjectAlerts(id).catch(() => ({ alerts: [] })),
        ]);
        setProject(projectData);
        setAlerts(alertsData.alerts || []);
        if (projectData.status === 'processed' || projectData.status === 'error') {
          clearInterval(poll);
        }
      } catch (e) {
        console.warn('[Buildora] Poll failed:', e.message);
      }
    }, 10_000);
    return () => clearInterval(poll);
  }, [id, jobId]);

  const handleUploadContinue = async (newFiles) => {
    const newSources = newFiles.map((f, i) => ({
      id: `new-${Date.now()}-${i}`,
      name: f.name,
      type: (f.type || '').startsWith('image') ? 'image' : 'document',
    }));
    setSources(prev => {
      const merged = [...prev, ...newSources];
      sessionStorage.setItem(`sources_${id}`, JSON.stringify(merged));
      return merged;
    });
    setSelectedSources(prev => [...prev, ...newSources.map(s => s.id)]);
    setUploadModalOpen(false);

    try {
      const result = await uploadDocuments(newFiles, id);
      if (result?.job_id) {
        sessionStorage.setItem(`job_${id}`, result.job_id);
        setPipelineJobId(result.job_id);
      } else {
        setPipelineJobId(null);
      }
    } catch (e) {
      console.warn('[Buildora] Background upload failed:', e.message);
      setPipelineJobId(null);
    }
    // Show pipeline animation
    setPipelineOpen(true);
  };

  const handlePipelineComplete = async () => {
    setPipelineOpen(false);
    // Clear job from session storage so it doesn't run on reload
    sessionStorage.removeItem(`job_${id}`);
    
    // Refresh project data after pipeline completes
    try {
      const [projectData, alertsData] = await Promise.all([
        getProject(id),
        getProjectAlerts(id).catch(() => ({ alerts: [] })),
      ]);
      setProject(projectData);
      setAlerts(alertsData.alerts || []);
    } catch {}
  };

  if (loading) return <SkeletonProject />;
  if (!project) return <div className="p-8 text-center text-red-500">Project not found</div>;

  const score = project?.health_score ?? 0;

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

          {/* Project Header (no breadcrumb, no status badge) */}
          <div className="px-10 py-6 border-b border-[#e4e2dc] bg-white sticky top-0 z-10">
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-bold text-[#1c1b18] leading-tight font-outfit">{project.name}</h1>
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

          {/* Tab Content */}
          <div className="p-10 max-w-4xl mx-auto w-full">
            {activeTab === 'Overview' && <OverviewTab project={project} alerts={alerts} />}
            {activeTab === 'Alerts' && (
              <div className="space-y-6 pb-8 animate-slide-up">
                <NotificationsPanel projectId={id} />
                {/* MonitoringPanel - HIDDEN (not needed for now) */}
                {/* <MonitoringPanel projectId={id} project={project} /> */}
              </div>
            )}
            {activeTab === 'Compliance' && <ComplianceScore projectId={id} />}
            {activeTab === 'Reports' && <ReportDownload projectId={id} project={project} />}
          </div>
        </div>
      </div>

      {/* RIGHT PANEL — Chat */}
      <ChatPanel
        collapsed={rightCollapsed}
        onToggleCollapse={() => setRightCollapsed(!rightCollapsed)}
        selectedSources={selectedSources}
        onRemoveSelectedSource={(srcId) => setSelectedSources(prev => prev.filter(s => s !== srcId))}
        sources={sources}
        projectId={id}
      />

      {/* Upload Modal */}
      <UploadModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onContinue={handleUploadContinue}
        projectName={project.name}
      />

      {/* Agent Pipeline Modal */}
      <AgentPipelineModal
        isOpen={pipelineOpen}
        jobId={pipelineJobId}
        onComplete={handlePipelineComplete}
      />
    </div>
  );
}
