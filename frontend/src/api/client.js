/**
 * Buildora API Client
 * Centralizes ALL HTTP calls to the FastAPI backend.
 * No component should call fetch or axios directly.
 * @module client
 */

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const DEMO_PROJECTS = [
  {
    id: 'alpha',
    name: 'Projek Perumahan Alpha',
    status: 'active',
    contractor: 'Syarikat Bina Jaya Sdn Bhd',
    location: 'Shah Alam, Selangor',
    start_date: '2023-08-01',
    contract_value: 'RM 12,500,000',
    health_score: 74,
    description: 'Phase 2 residential development comprising 3 blocks of affordable housing under PPR programme.',
  },
  {
    id: 'kl-tower',
    name: 'KL Tower Renovation',
    status: 'active',
    contractor: 'Apex Construction Builders',
    location: 'Kuala Lumpur',
    start_date: '2024-01-15',
    contract_value: 'RM 8,200,000',
    health_score: 88,
    description: 'Modernization of observation deck facilities and structural reinforcement of the antenna mast.',
  },
  {
    id: 'penang-bridge',
    name: 'Penang Bridge Maintenance',
    status: 'at-risk',
    contractor: 'Jambatan Utama Eng.',
    location: 'Penang',
    start_date: '2023-11-01',
    contract_value: 'RM 24,000,000',
    health_score: 55,
    description: 'Cable replacement and resurfacing of the northbound lanes. High urgency due to structural fatigue alerts.',
  },
  {
    id: 'mrt-line-3',
    name: 'MRT Line 3 Depot',
    status: 'active',
    contractor: 'Rapid Rail Constructors',
    location: 'Klang Valley',
    start_date: '2024-03-10',
    contract_value: 'RM 45,500,000',
    health_score: 92,
    description: 'Construction of the main train depot, maintenance facilities, and operations control center.',
  },
  {
    id: 'hospital-selayang',
    name: 'Hospital Selayang Wing',
    status: 'active',
    contractor: 'MedBuild Solutions',
    location: 'Selayang',
    start_date: '2022-09-01',
    contract_value: 'RM 18,300,000',
    health_score: 65,
    description: 'Extension of the pediatric wing including new specialized ICUs and quarantine wards.',
  }
];

/**
 * Generic request helper with error handling.
 * @param {string} path - Endpoint path
 * @param {RequestInit} [options] - Fetch options
 * @returns {Promise<any>}
 */
async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail ?? 'Request failed');
  }
  return res.json();
}

/**
 * Upload a construction document.
 * POST /upload
 * @param {FormData} formData - Multipart form with the document file
 * @returns {Promise<{ project_id: string, filename: string }>}
 */
export const uploadDocument = (formData) =>
  fetch(`${BASE}/upload`, { method: 'POST', body: formData }).then((res) => {
    if (!res.ok) throw new Error('Upload failed');
    return res.json();
  });

/**
 * Fetch all projects for the dashboard.
 * GET /projects
 * @returns {Promise<Project[]>}
 */
export const getProjects = () => request('/projects').catch(() => DEMO_PROJECTS);

/**
 * Create a new project.
 * POST /projects
 * @param {{ name: string, contractor: string, location: string }} data
 * @returns {Promise<Project>}
 */
export const createProject = (data) =>
  request('/projects', { method: 'POST', body: JSON.stringify(data) });

/**
 * Get a single project by ID.
 * GET /projects/:id
 * @param {string} id - Project ID
 * @returns {Promise<Project>}
 */
export const getProject = (id) => request(`/projects/${id}`).catch(() => {
  const proj = DEMO_PROJECTS.find(p => p.id === id);
  if (!proj) throw new Error('Project not found');
  return proj;
});

/**
 * Submit a milestone entry.
 * POST /milestones
 * @param {{ project_id: string, name: string, planned_date: string, actual_date: string, planned_cost: number, actual_cost: number, notes: string }} data
 * @returns {Promise<Milestone>}
 */
export const postMilestone = (data) =>
  request('/milestones', { method: 'POST', body: JSON.stringify(data) });

/**
 * Get milestones for a project.
 * GET /milestones/:project_id
 * @param {string} projectId
 * @returns {Promise<Milestone[]>}
 */
export const getMilestones = (projectId) => request(`/milestones/${projectId}`);

/**
 * Fetch the generated report for a project.
 * GET /reports/:id
 * @param {string} id - Project ID
 * @returns {Promise<Report>}
 */
export const getReport = (id) => request(`/reports/${id}`);

/**
 * Trigger report generation for a project.
 * POST /reports/:id/generate
 * @param {string} id - Project ID
 * @returns {Promise<{ status: string }>}
 */
export const generateReport = (id) =>
  request(`/reports/${id}/generate`, { method: 'POST' });

/**
 * Get compliance score for a project.
 * GET /compliance/:id
 * @param {string} id - Project ID
 * @returns {Promise<ComplianceResult>}
 */
export const getComplianceScore = (id) => request(`/compliance/${id}`);

/**
 * Get notifications/alerts for a project (Agent D).
 * GET /notifications/:id
 * @param {string} id - Project ID
 * @returns {Promise<{ project_id: string, count: number, notifications: Notification[] }>}
 */
export const getNotifications = (id) => request(`/notifications/${id}`).catch(() => ({
  project_id: id,
  count: 0,
  notifications: [],
}));

/**
 * Trigger Agent D to process alerts for a project.
 * POST /notifications/:id
 * @param {string} id - Project ID
 * @returns {Promise<Object>}
 */
export const triggerNotifications = (id) =>
  request(`/notifications/${id}`, { method: 'POST' });

/**
 * Returns the full SSE URL for agent streaming.
 * Connect via EventSource in AgentPanel.
 * GET /agent-stream/:jobId
 * @param {string} jobId
 * @returns {string} SSE URL
 */
export const getAgentStreamUrl = (jobId) => `${BASE}/agent-stream/${jobId}`;
