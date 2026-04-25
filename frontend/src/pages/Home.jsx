import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProjects, uploadDocuments, deleteProject } from '../api/client.js';
import { Plus, MoreVertical, Building2, HardHat, Hammer, Construction, Activity, Loader2, Trash2 } from 'lucide-react';
import UploadModal from '../components/UploadModal.jsx';

const CARD_COLORS = ['#1a2a1a', '#1a1a2a', '#2a1a10', '#1a2520', '#251a10'];
const CARD_ICONS = [Building2, HardHat, Hammer, Construction];

function HealthRing({ score }) {
  const color = score >= 80 ? '#16a34a' : score >= 60 ? '#d97706' : '#dc2626';
  const radius = 20;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative w-11 h-11 flex items-center justify-center">
      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 44 44">
        <circle
          cx="22"
          cy="22"
          r={radius}
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="3"
          fill="transparent"
        />
        <circle
          cx="22"
          cy="22"
          r={radius}
          stroke={color}
          strokeWidth="3"
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <span className="absolute text-[11px] font-bold text-white">{score}</span>
    </div>
  );
}

export default function Home() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('recent');

  useEffect(() => {
    loadProjects();
  }, []);

  function loadProjects() {
    setLoading(true);
    getProjects().then(data => {
      setProjects(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }

  const handleDeleteProject = async (e, projectId) => {
    e.stopPropagation();
    if (!window.confirm('Delete this project and all its data? This cannot be undone.')) return;
    try {
      await deleteProject(projectId);
      setProjects(prev => prev.filter(p => p.id !== projectId));
    } catch (err) {
      alert('Failed to delete project: ' + (err.message || 'Unknown error'));
    }
  };

  const filteredProjects = projects.filter(p => 
    (p.name || '').toLowerCase().includes(searchQuery.toLowerCase()) || 
    (p.contractor || '').toLowerCase().includes(searchQuery.toLowerCase())
  ).sort((a, b) => {
    if (sortBy === 'name') return (a.name || '').localeCompare(b.name || '');
    if (sortBy === 'health') return (b.health_score || 0) - (a.health_score || 0);
    return 0;
  });

  const handleCreateProject = async (files, projectTitle) => {
    if (!files || files.length === 0) return;
    setUploadError(null);
    setUploading(true);
    try {
      const result = await uploadDocuments(files, null, projectTitle || 'New Project');
      const { project_id, job_id } = result;
      // Store job_id so Project page can connect to SSE stream
      if (job_id) sessionStorage.setItem(`job_${project_id}`, job_id);
      // Store uploaded file names for sources panel
      sessionStorage.setItem(`sources_${project_id}`, JSON.stringify(
        files.map(f => ({ id: f.name, name: f.name, type: f.type?.startsWith('image') ? 'image' : 'document' }))
      ));
      setIsModalOpen(false);
      // Refresh project list after a short delay so the new project is included
      setTimeout(loadProjects, 800);
      navigate(`/project/${project_id}`);
    } catch (err) {
      setUploadError(err.message || 'Upload failed. Please try again.');
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 p-12">
        <div className="skeleton h-8 w-48 rounded mb-10" />
        <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4">
          {[1,2,3].map(i => <div key={i} className="skeleton h-[180px] rounded-xl" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-[#f7f6f3] overflow-y-auto">
      <div className="px-12 py-10 w-full max-w-[1400px] mx-auto animate-fade-in">
        {/* Header */}
        <div className="flex items-end justify-between mb-8">
          <div>
            <h1 className="text-[28px] font-bold text-[#1c1b18] tracking-tight font-outfit">My Projects</h1>
            <p className="text-[#6b6860] mt-1">{projects.length} active project{projects.length !== 1 ? 's' : ''}</p>
          </div>
          <div className="flex items-center gap-3">
            <input 
              type="search" 
              placeholder="Search projects..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input text-sm w-64 bg-white"
            />
            <div className="flex items-center gap-2">
              <span className="text-sm text-[#9b9794] font-medium whitespace-nowrap">Sort by:</span>
              <select 
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="btn btn-ghost text-sm bg-white border border-[#e4e2dc] pr-8 appearance-none cursor-pointer outline-none focus:border-[#f97316] relative"
                style={{ backgroundImage: `url('data:image/svg+xml;utf8,<svg fill="none" stroke="%239b9794" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>')`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 8px center', backgroundSize: '14px' }}
              >
                <option value="recent">Recent</option>
                <option value="name">Name</option>
                <option value="health">Health Score</option>
              </select>
            </div>
          </div>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4">
          
          {/* Create New Project Card */}
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex flex-col items-center justify-center h-[180px] rounded-xl bg-[#1a1a1b] border border-dashed border-white/15 hover:border-white/30 hover:bg-[#252526] transition-all duration-200 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
              <Plus className="w-5 h-5 text-white/70" />
            </div>
            <span className="text-white/80 font-medium tracking-wide">Create new project</span>
          </button>

          {/* Project Cards */}
          {filteredProjects.map((p, index) => {
            const bgColor = CARD_COLORS[index % CARD_COLORS.length];
            const Icon = CARD_ICONS[index % CARD_ICONS.length];
            
            const statusText = p.status || 'active';
            
            return (
              <div 
                key={p.id}
                onClick={() => navigate(`/project/${p.id}`)}
                className="relative flex flex-col h-[180px] rounded-xl p-5 cursor-pointer hover:-translate-y-1 transition-all duration-200 overflow-hidden shadow-sm hover:shadow-md group"
                style={{ backgroundColor: bgColor }}
              >
                {/* Top: Icon & actions */}
                <div className="flex justify-between items-start mb-auto">
                  <div className="p-2 rounded-lg bg-white/5">
                    <Icon className="w-6 h-6 text-white/60" />
                  </div>
                  <div className="flex items-center gap-1">
                    {/* Delete button - only visible on hover */}
                    <button
                      id={`delete-project-${p.id}`}
                      aria-label={`Delete project ${p.name}`}
                      className="text-white/0 group-hover:text-white/40 hover:!text-red-400 transition-colors p-1 rounded"
                      onClick={(e) => handleDeleteProject(e, p.id)}
                      title="Delete project"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                    <button className="text-white/40 hover:text-white transition-colors" onClick={(e) => e.stopPropagation()}>
                      <MoreVertical className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Middle: Text */}
                <div className="mb-4">
                  <h3 className="font-outfit text-white text-lg font-medium tracking-tight truncate">
                    {p.name}
                  </h3>
                  <p className="text-white/55 text-xs truncate mt-0.5">
                    {p.contractor || 'Contractor not specified'} • Active recently
                  </p>
                </div>

                {/* Bottom: Ring & Badge */}
                <div className="flex justify-between items-end">
                  <HealthRing score={p.health_score ?? 0} />
                  <span 
                    className="px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-white/10 text-white/80 border border-white/10"
                  >
                    {statusText === 'active' ? 'Active' : statusText.replace('-', ' ')}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <UploadModal 
        isOpen={isModalOpen}
        onClose={() => { if (!uploading) { setIsModalOpen(false); setUploadError(null); } }}
        onContinue={handleCreateProject}
        projectName={null}
        uploading={uploading}
        error={uploadError}
      />
    </div>
  );
}
