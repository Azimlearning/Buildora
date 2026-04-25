import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, Loader2, BookOpen } from 'lucide-react';

export default function ChatbotPanel({ projectId }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '👋 Hi! I\'m your Buildora AI assistant. Ask me about CIDB regulations, project compliance, or construction best practices.',
      timestamp: new Date().toISOString()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    setTimeout(() => {
      const assistantMessage = {
        role: 'assistant',
        content: `🚧 Chatbot integration pending. Your question: "${input}" will be answered once the AI assistant is connected.`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1000);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="card p-6 flex flex-col h-[600px]">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <MessageCircle className="w-5 h-5 text-[#ff6b35]" />
          <h3 className="font-semibold text-lg text-[#1c1b18]">AI Assistant</h3>
        </div>
        <span className="text-xs text-[#9b9794] bg-yellow-100 px-2 py-1 rounded">Integration Pending</span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${msg.role === 'user' ? 'bg-[#ff6b35] text-white' : 'bg-[#f5f4f0] text-[#1c1b18]'}`}>
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
              {msg.timestamp && (
                <p className={`text-[10px] mt-1 ${msg.role === 'user' ? 'text-orange-100' : 'text-[#9b9794]'}`}>
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </p>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-[#f5f4f0] rounded-2xl px-4 py-3">
              <Loader2 className="w-4 h-4 animate-spin text-[#9b9794]" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex gap-2 mb-3 flex-wrap">
        <button onClick={() => setInput('What are the CIDB compliance requirements?')} className="text-xs px-3 py-1.5 rounded-full border border-[#e4e2dc] hover:bg-[#f5f4f0] transition-colors">
          <BookOpen className="w-3 h-3 inline mr-1" />CIDB Requirements
        </button>
        <button onClick={() => setInput('Explain the project delays')} className="text-xs px-3 py-1.5 rounded-full border border-[#e4e2dc] hover:bg-[#f5f4f0] transition-colors">
          📊 Explain Delays
        </button>
        <button onClick={() => setInput('What is BISQ?')} className="text-xs px-3 py-1.5 rounded-full border border-[#e4e2dc] hover:bg-[#f5f4f0] transition-colors">
          ❓ What is BISQ?
        </button>
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask about compliance, regulations, or project insights..."
          className="flex-1 px-4 py-3 rounded-xl border border-[#e4e2dc] focus:outline-none focus:ring-2 focus:ring-[#ff6b35] text-sm"
          disabled={isLoading}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          className="px-4 py-3 rounded-xl bg-[#ff6b35] text-white hover:bg-[#e55a2b] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>

      <p className="text-[10px] text-[#9b9794] mt-3 text-center">🚧 AI chatbot integration in progress by @aliasya</p>
    </div>
  );
}
