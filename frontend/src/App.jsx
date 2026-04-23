/**
 * App.jsx — Root layout: split-pane shell with sidebar + main content area.
 * Handles routing via react-router-dom v6.
 * No API calls made here; routing only.
 */
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { Component } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

import Home from './pages/Home.jsx';
import Project from './pages/Project.jsx';

/* ─── Error Boundary ─── */
class PageErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-full gap-4 p-8">
          <div className="w-12 h-12 rounded-full bg-red-50 flex items-center justify-center">
            <AlertTriangle className="w-6 h-6 text-red-500" />
          </div>
          <div className="text-center">
            <p className="font-semibold text-[#1c1b18] mb-1">Something went wrong</p>
            <p className="text-sm text-[#6b6860]">{this.state.error?.message ?? 'Unexpected error'}</p>
          </div>
          <button
            className="btn btn-secondary text-sm"
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

/* ─── App Shell ─── */
function Shell() {
  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#f7f6f3] relative">
      {/* Top Nav Bar */}
      <header className="h-[60px] bg-white border-b border-[#e4e2dc] flex items-center px-5 flex-shrink-0 z-50">
        <Link 
          to="/" 
          className="flex items-center hover:opacity-80 transition-opacity"
          aria-label="Buildora Home"
        >
          <span className="font-bold text-[#1c1b18] text-lg tracking-tight">Buildora</span>
        </Link>
      </header>

      {/* Main content */}
      <main className="flex-1 w-full min-h-0 flex flex-col relative">
        <PageErrorBoundary>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/project/:id" element={<Project />} />
          </Routes>
        </PageErrorBoundary>
      </main>
    </div>
  );
}

/* ─── Root App ─── */
export default function App() {
  return (
    <BrowserRouter>
      <Shell />
    </BrowserRouter>
  );
}
