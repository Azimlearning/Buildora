import { useState } from 'react';
import { ChevronLeft, ChevronRight, Search, FileText, Image as ImageIcon, X, Plus } from 'lucide-react';

export default function SourcesPanel({ 
  collapsed, 
  onToggleCollapse, 
  sources, 
  setSources, 
  selectedSources, 
  setSelectedSources,
  onOpenUpload 
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [previewDoc, setPreviewDoc] = useState(null);

  const toggleAll = (e) => {
    if (e.target.checked) {
      setSelectedSources(sources.map(s => s.id));
    } else {
      setSelectedSources([]);
    }
  };

  const toggleSource = (id) => {
    if (selectedSources.includes(id)) {
      setSelectedSources(prev => prev.filter(s => s !== id));
    } else {
      setSelectedSources(prev => [...prev, id]);
    }
  };

  const removeSource = (id) => {
    setSources(prev => prev.filter(s => s.id !== id));
    setSelectedSources(prev => prev.filter(s => s !== id));
  };

  const filteredSources = sources.filter(s => s.name.toLowerCase().includes(searchQuery.toLowerCase()));
  const allSelected = sources.length > 0 && selectedSources.length === sources.length;
  const someSelected = selectedSources.length > 0 && selectedSources.length < sources.length;

  if (collapsed) {
    return (
      <div className="w-10 h-full bg-[#1a1a1b] flex flex-col items-center py-4 border-r border-[#e4e2dc]">
        <button 
          onClick={onToggleCollapse}
          className="p-1 rounded hover:bg-white/10 text-[#9b9794] hover:text-white transition-colors"
          aria-label="Expand Sources Panel"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    );
  }

  return (
    <>
      <div className="w-[280px] h-full bg-[#fcfcfb] flex flex-col border-r border-[#e4e2dc] flex-shrink-0">
        {/* Header */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-[#e4e2dc]">
        <h2 className="font-outfit font-bold text-[#1c1b18] text-lg tracking-tight">Sources</h2>
        <div className="flex items-center gap-1">
          <button 
            onClick={onToggleCollapse}
            className="p-1.5 rounded-md hover:bg-black/5 text-[#9b9794] transition-colors -mr-1.5"
            aria-label="Collapse panel"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="p-4 flex flex-col flex-1 overflow-hidden">
        <button 
          onClick={onOpenUpload}
          className="w-full mb-4 py-2 border border-[#f97316] text-[#f97316] rounded-lg text-sm font-medium hover:bg-[#f97316]/5 transition-colors flex items-center justify-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Add source
        </button>

        <div className="relative mb-4">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9b9794]" />
          <input 
            type="search"
            placeholder="Search sources..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white border border-[#e4e2dc] rounded-lg pl-9 pr-3 py-1.5 text-sm focus:outline-none focus:border-[#f97316]"
          />
        </div>

        <div className="flex items-center gap-2 mb-3 px-1">
          <input 
            type="checkbox"
            checked={allSelected}
            ref={input => { if (input) input.indeterminate = someSelected }}
            onChange={toggleAll}
            className="w-3.5 h-3.5 rounded border-[#c2c0bb] text-[#f97316] focus:ring-[#f97316]"
          />
          <span className="text-xs font-medium text-[#6b6860]">Select all</span>
        </div>

        <div className="flex-1 overflow-y-auto pr-1 space-y-1 custom-scrollbar">
          {filteredSources.map((s) => (
            <div 
              key={s.id} 
              onDoubleClick={() => setPreviewDoc(s)}
              className="flex items-center gap-2 p-2 rounded-lg hover:bg-[#f0ede7] group transition-colors cursor-pointer"
            >
              <input 
                type="checkbox"
                checked={selectedSources.includes(s.id)}
                onChange={() => toggleSource(s.id)}
                className="w-3.5 h-3.5 rounded border-[#c2c0bb] text-[#f97316] focus:ring-[#f97316] flex-shrink-0"
              />
              {s.type === 'image' ? (
                <ImageIcon className="w-4 h-4 text-[#9b9794] flex-shrink-0" />
              ) : (
                <FileText className="w-4 h-4 text-[#9b9794] flex-shrink-0" />
              )}
              <span className="text-sm text-[#1c1b18] truncate flex-1 select-none" title={s.name}>
                {s.name.length > 24 ? s.name.substring(0, 24) + '...' : s.name}
              </span>
              <button 
                onClick={() => removeSource(s.id)}
                className="hidden group-hover:flex p-1 rounded hover:bg-black/10 text-[#9b9794] hover:text-red-600 flex-shrink-0"
                aria-label="Remove source"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
          {filteredSources.length === 0 && (
            <div className="text-center text-sm text-[#9b9794] mt-8">
              No sources found.
            </div>
          )}
        </div>
      </div>
    </div>

      {previewDoc && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 p-4 animate-fade-in" onClick={() => setPreviewDoc(null)}>
          <div className="bg-white w-full max-w-4xl h-[85vh] rounded-xl flex flex-col overflow-hidden animate-slide-up shadow-2xl" onClick={e => e.stopPropagation()}>
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-[#e4e2dc] bg-[#fcfcfb]">
              <div className="flex items-center gap-3">
                {previewDoc.type === 'image' ? (
                  <ImageIcon className="w-5 h-5 text-[#f97316]" />
                ) : (
                  <FileText className="w-5 h-5 text-[#f97316]" />
                )}
                <h3 className="font-outfit font-semibold text-[#1c1b18] text-lg">{previewDoc.name}</h3>
              </div>
              <button 
                onClick={() => setPreviewDoc(null)} 
                className="p-1.5 rounded-md hover:bg-black/5 text-[#9b9794] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            {/* Body Mockup */}
            <div className="flex-1 bg-[#e4e2dc] flex items-center justify-center p-8 overflow-hidden">
               <div className="bg-white shadow-md w-full max-w-3xl h-full p-10 overflow-y-auto rounded border border-[#c2c0bb]">
                 <div className="skeleton h-10 w-2/3 mb-8" />
                 <div className="skeleton h-4 w-full mb-4" />
                 <div className="skeleton h-4 w-full mb-4" />
                 <div className="skeleton h-4 w-11/12 mb-4" />
                 <div className="skeleton h-4 w-full mb-4" />
                 <div className="skeleton h-4 w-5/6 mb-8" />
                 <div className="flex gap-4 mb-8">
                   <div className="skeleton h-32 flex-1" />
                   <div className="skeleton h-32 flex-1" />
                 </div>
                 <div className="skeleton h-4 w-full mb-4" />
                 <div className="skeleton h-4 w-4/5 mb-4" />
                 <p className="text-center text-[#9b9794] mt-12 font-medium italic">Document preview simulation</p>
               </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
