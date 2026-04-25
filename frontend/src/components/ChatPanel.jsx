import { useState, useRef, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Send, FileText, User, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export default function ChatPanel({
  collapsed,
  onToggleCollapse,
  selectedSources,
  onRemoveSelectedSource,
  sources,
  projectId,
}) {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: "Ask me anything about your project documents or CIDB compliance. I'll use the selected sources for context." }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const endRef = useRef(null);
  const textareaRef = useRef(null);

  const selectedDocs = sources.filter(s => selectedSources.includes(s.id));

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 128) + 'px';
    }
  }, [input]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isTyping) return;

    const userMsg = { role: 'user', text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const res = await fetch(`${BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          message: text,
          selected_sources: selectedDocs.map(s => s.name),
          history: messages.map(m => ({ role: m.role, content: m.text })),
        }),
      });

      if (!res.ok) throw new Error('Chat API error');

      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', text: data.reply }]);
    } catch (err) {
      // Fallback: simple local response
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: `I couldn't connect to the AI service right now. Please make sure the backend is running and try again. (${err.message})`,
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  if (collapsed) {
    return (
      <div className="w-10 h-full bg-[#1a1a1b] flex flex-col items-center py-4 border-l border-[#e4e2dc]">
        <button
          onClick={onToggleCollapse}
          className="p-1 rounded hover:bg-white/10 text-[#9b9794] hover:text-white transition-colors"
          aria-label="Expand Chat Panel"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
      </div>
    );
  }

  return (
    <div className="w-[340px] h-full bg-white flex flex-col border-l border-[#e4e2dc] flex-shrink-0 relative shadow-[-4px_0_24px_rgba(0,0,0,0.02)]">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-[#e4e2dc]">
        <div className="flex items-center gap-1">
          <button
            onClick={onToggleCollapse}
            className="p-1.5 rounded-md hover:bg-black/5 text-[#9b9794] transition-colors -ml-1.5"
            aria-label="Collapse panel"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
        <h2 className="font-outfit font-bold text-[#1c1b18] text-lg tracking-tight">Chat</h2>
        <div className="w-8" />
      </div>

      {/* Context Chips */}
      {selectedDocs.length > 0 && (
        <div className="px-4 py-3 bg-[#fafaf8] border-b border-[#e4e2dc] flex flex-wrap gap-1.5 overflow-y-auto max-h-[80px] custom-scrollbar">
          {selectedDocs.map(doc => (
            <div key={doc.id} className="flex items-center gap-1.5 bg-white border border-[#e4e2dc] rounded-full px-2.5 py-1 max-w-full">
              <FileText className="w-3 h-3 text-[#f97316] flex-shrink-0" />
              <span className="text-[10px] font-medium text-[#6b6860] truncate">{doc.name}</span>
              <button
                onClick={() => onRemoveSelectedSource(doc.id)}
                className="p-0.5 rounded-full hover:bg-black/10 text-[#9b9794] flex-shrink-0 ml-1"
                aria-label="Remove source"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5 custom-scrollbar">
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
            {/* Avatar — user gets dark circle, assistant gets a simple orange dot */}
            <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
              m.role === 'user' ? 'bg-[#1c1b18]' : 'bg-[#f97316]/15 border border-[#f97316]/20'
            }`}>
              {m.role === 'user'
                ? <User className="w-4 h-4 text-white" />
                : <span className="w-2 h-2 rounded-full bg-[#f97316] inline-block" />
              }
            </div>
            <div className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'} max-w-[80%]`}>
              <div className={`text-[13px] leading-relaxed px-3.5 py-2.5 rounded-2xl ${
                m.role === 'user'
                  ? 'bg-[#1c1b18] text-white rounded-tr-sm'
                  : 'bg-[#f4f4f5] text-[#1c1b18] rounded-tl-sm border border-[#e4e2dc]'
              }`}>
                {m.role === 'user' ? (
                  m.text
                ) : (
                  <div className="prose prose-sm max-w-none prose-p:leading-snug prose-li:my-0.5">
                    <ReactMarkdown>{m.text}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-[#f97316]/15 border border-[#f97316]/20 flex items-center justify-center flex-shrink-0 mt-0.5">
              <span className="w-2 h-2 rounded-full bg-[#f97316] inline-block" />
            </div>
            <div className="bg-[#f4f4f5] border border-[#e4e2dc] rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 bg-[#9b9794] rounded-full animate-bounce [animation-delay:-0.3s]" />
              <div className="w-1.5 h-1.5 bg-[#9b9794] rounded-full animate-bounce [animation-delay:-0.15s]" />
              <div className="w-1.5 h-1.5 bg-[#9b9794] rounded-full animate-bounce" />
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div className="p-4 bg-white border-t border-[#e4e2dc]">
        <div className="relative flex items-end bg-[#f4f4f5] border border-[#e4e2dc] rounded-xl focus-within:border-[#f97316] focus-within:ring-1 focus-within:ring-[#f97316]/30 transition-all p-1">
          <textarea
            ref={textareaRef}
            placeholder="Ask about your project…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            rows={1}
            className="w-full bg-transparent text-sm resize-none px-3 py-2.5 focus:outline-none max-h-32 min-h-[40px] custom-scrollbar"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            className="mb-1 mr-1 p-2 rounded-lg bg-[#f97316] text-white disabled:opacity-50 disabled:bg-[#9b9794] transition-colors"
            aria-label="Send message"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
