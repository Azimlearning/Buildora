import { useState, useRef, useCallback } from 'react';
import { Upload, FileText, X, Search, FileImage, Link as LinkIcon, ArrowRight, CheckCircle2 } from 'lucide-react';

const ACCEPTED_TYPES = [
  { ext: 'PDF',  mime: 'application/pdf' },
  { ext: 'DOCX', mime: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' },
  { ext: 'JPG',  mime: 'image/jpeg' },
  { ext: 'PNG',  mime: 'image/png' },
];
const ACCEPTED_MIME = new Set(ACCEPTED_TYPES.map((t) => t.mime));

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function UploadModal({ isOpen, onClose, onContinue, projectName }) {
  const [files, setFiles] = useState([]);
  const [projectTitle, setProjectTitle] = useState('');
  const [isHover, setIsHover] = useState(false);
  const inputRef = useRef(null);

  if (!isOpen) return null;

  const handleFiles = (selectedFiles) => {
    const validFiles = Array.from(selectedFiles).filter(f => ACCEPTED_MIME.has(f.type));
    if (validFiles.length > 0) {
      setFiles(prev => [...prev, ...validFiles]);
    }
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const onDrop = (e) => {
    e.preventDefault();
    setIsHover(false);
    handleFiles(e.dataTransfer.files);
  };

  const onDragOver = (e) => { e.preventDefault(); setIsHover(true); };
  const onDragLeave = () => setIsHover(false);

  const handleContinue = () => {
    onContinue(files, projectTitle);
    setFiles([]); // Clear on close
    setProjectTitle('');
  };

  const handlePasteText = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (!text) return;
      const file = new File([text], 'Pasted_Text.txt', { type: 'text/plain' });
      // Add a dummy size property if File API doesn't populate it correctly in this context
      Object.defineProperty(file, 'size', { value: new Blob([text]).size });
      setFiles(prev => [...prev, file]);
    } catch (err) {
      console.error('Clipboard access denied or empty', err);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4 animate-fade-in">
      <div className="bg-[#1e1e1f] w-full max-w-[560px] rounded-[14px] shadow-2xl flex flex-col overflow-hidden animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
          <h2 className="text-white font-medium text-lg tracking-tight font-outfit">
            {projectName ? `Add sources to ${projectName}` : 'Add sources'}
          </h2>
          <button 
            onClick={onClose}
            className="p-1.5 rounded-md hover:bg-white/10 text-[#9b9794] hover:text-white transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 flex flex-col gap-4 overflow-y-auto max-h-[70vh] custom-scrollbar">
          
          {/* Project Title Input (only for new projects) */}
          {!projectName && (
            <div className="mb-2">
              <label htmlFor="project-title" className="block text-[#9b9794] text-xs font-medium mb-1.5 uppercase tracking-wide">
                Project Title
              </label>
              <input
                id="project-title"
                type="text"
                placeholder="e.g. KVMRT Line 2 Expansion"
                value={projectTitle}
                onChange={(e) => setProjectTitle(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-[#f97316] focus:ring-1 focus:ring-[#f97316]/30 transition-all placeholder:text-[#9b9794]"
              />
            </div>
          )}

          {/* Dropzone */}
          <div
            onDrop={onDrop}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            className={`flex flex-col items-center justify-center p-8 rounded-xl border-2 border-dashed transition-colors duration-150 ${
              isHover ? 'border-[#f97316] bg-[#f97316]/10' : 'border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10'
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.jpg,.jpeg,.png"
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
            <p className="text-[#e5e3de] font-medium mb-1">or drop your files here</p>
            <p className="text-[#9b9794] text-xs mb-5">pdf, docx, jpg, png — multiple allowed</p>
            
            <div className="flex gap-3">
              <button 
                onClick={() => inputRef.current?.click()}
                className="bg-white/10 hover:bg-white/20 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
              >
                <Upload className="w-4 h-4" />
                Upload files
              </button>
              <button 
                onClick={handlePasteText}
                className="bg-white/5 hover:bg-white/10 border border-white/10 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
              >
                <LinkIcon className="w-4 h-4" />
                Paste text
              </button>
            </div>
          </div>

          {/* Uploaded List */}
          {files.length > 0 && (
            <div className="mt-2 flex flex-col gap-2">
              <div className="text-sm text-[#e5e3de] font-medium mb-1">Uploaded ({files.length}):</div>
              {files.map((f, i) => (
                <div key={i} className="flex items-center justify-between bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                  <div className="flex items-center gap-3 overflow-hidden">
                    <FileText className="w-4 h-4 text-[#16a34a] flex-shrink-0" />
                    <span className="text-sm text-white truncate">{f.name}</span>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0 ml-3">
                    <span className="text-xs text-[#9b9794]">{formatBytes(f.size)}</span>
                    <button 
                      onClick={() => removeFile(i)}
                      className="p-1 rounded hover:bg-red-500/20 text-[#9b9794] hover:text-red-400 transition-colors"
                      aria-label="Remove file"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-white/10 flex justify-between items-center bg-[#1e1e1f]">
          <button 
            onClick={() => inputRef.current?.click()}
            className="text-[#9b9794] hover:text-white text-sm font-medium transition-colors flex items-center gap-2"
          >
            <Upload className="w-4 h-4" />
            Upload More
          </button>
          
          <button 
            onClick={handleContinue}
            disabled={files.length === 0 || (!projectName && !projectTitle.trim())}
            className="bg-[#f97316] hover:bg-[#ea580c] disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors flex items-center gap-2"
          >
            Continue Session
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
